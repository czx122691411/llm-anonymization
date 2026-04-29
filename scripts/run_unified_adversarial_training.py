#!/usr/bin/env python3
"""
统一评估标准 - 完整对抗训练脚本

集成到现有系统，使用UnifiedPrivacyEvaluator重新训练同构和异构配置

运行方式:
    python scripts/run_unified_adversarial_training.py --config homogeneous_unified
    python scripts/run_unified_adversarial_training.py --config heterogeneous_unified
    python scripts/run_unified_adversarial_training.py --config both

配置文件:
    - configs/anonymization/synthetic/06_homogeneous_unified.yaml
    - configs/anonymization/synthetic/07_heterogeneous_unified.yaml
"""

import os
import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from tqdm import tqdm

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.models.providers.registry import get_registry
from src.evaluation.unified_privacy_evaluator import UnifiedPrivacyEvaluator


class UnifiedAdversarialTrainer:
    """
    统一评估标准的对抗训练器

    集成到现有系统，输出格式与anonymized_results/兼容
    """

    def __init__(self, config_path: str):
        """
        初始化训练器

        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path

        # 读取配置
        from src.utils.initialization import read_config_from_yaml
        self.cfg = read_config_from_yaml(config_path)

        # 创建统一评估器
        self.evaluator = UnifiedPrivacyEvaluator(
            target_privacy=self.cfg.task_config.stop_threshold.privacy,
            min_utility=self.cfg.task_config.min_utility_threshold,
            semantic_threshold=0.7
        )

        # 创建模型
        print(f"创建模型...")
        registry = get_registry(region="china")

        self.defender = registry.create_model_instance(
            self.cfg.task_config.anon_model.name,
            **self.cfg.task_config.anon_model.args
        )

        self.attacker = registry.create_model_instance(
            self.cfg.task_config.attack_model.name,
            **self.cfg.task_config.attack_model.args
        )

        self.utility_model = registry.create_model_instance(
            self.cfg.task_config.utility_model.name,
            **self.cfg.task_config.utility_model.args
        )

        if not all([self.defender, self.attacker, self.utility_model]):
            raise RuntimeError("模型创建失败")

        print(f"✓ 防御者: {self.cfg.task_config.anon_model.name}")
        print(f"✓ 攻击者: {self.cfg.task_config.attack_model.name}")
        print(f"✓ 效用模型: {self.cfg.task_config.utility_model.name}")
        print(f"✓ 评估器: UnifiedPrivacyEvaluator")

        # 创建输出目录
        self.outpath = Path(self.cfg.task_config.outpath)
        self.outpath.mkdir(parents=True, exist_ok=True)

    def load_profiles(self) -> List[Dict]:
        """加载profiles"""
        print(f"\n加载profiles: {self.cfg.task_config.profile_path}")

        profiles = []
        profile_path = Path(self.cfg.task_config.profile_path)

        with open(profile_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if len(profiles) >= self.cfg.task_config.num_profiles:
                    break

                try:
                    data = json.loads(line.strip())
                    profile = self._parse_profile(data, line_num)
                    if profile:
                        profiles.append(profile)
                except Exception as e:
                    print(f"解析错误 (行{line_num}): {e}")
                    continue

        print(f"✓ 加载了 {len(profiles)} 个profiles")
        return profiles

    def _parse_profile(self, data: Dict, line_num: int) -> Dict:
        """解析单个profile"""
        try:
            username = data.get("username", f"sample_{line_num}")

            # 提取文本
            comments = data.get("comments", [])
            if not comments:
                return None

            comment_blocks = comments[0].get("comments", [])
            if not comment_blocks:
                return None

            texts = [c.get("text", "") for c in comment_blocks]
            original_text = "\n".join(texts)

            if len(original_text) < 50:
                return None

            # 提取ground truth
            reviews = data.get("reviews", {})
            ground_truth = {}

            for category, category_data in reviews.items():
                for attr, attr_data in category_data.items():
                    estimate = attr_data.get("estimate")
                    if estimate is not None:
                        ground_truth[attr] = str(estimate)

            if not ground_truth:
                return None

            return {
                "username": username,
                "line_num": line_num,
                "original_text": original_text,
                "ground_truth": ground_truth,
                "raw_data": data
            }

        except Exception as e:
            return None

    def anonymize(self, text: str, ground_truth: Dict, round_num: int) -> str:
        """防御者匿名化"""
        attrs = ", ".join(ground_truth.keys())

        prompt = f"""请对以下文本进行匿名化处理，保护个人隐私信息。

原始文本:
{text}

需要保护的属性:
{attrs}

要求:
1. 移除或泛化上述属性的具体信息
2. 保持文本的自然流畅和语义
3. 使用通用表述替代具体信息
4. 确保文本仍然可读

匿名化文本:"""

        try:
            result = self.defender.predict_string(prompt)

            # 清理结果
            lines = result.split('\n')
            anonymized_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('说明') and not line.startswith('注意'):
                    anonymized_lines.append(line)

            return '\n'.join(anonymized_lines) if anonymized_lines else result

        except Exception as e:
            print(f"    匿名化失败: {e}")
            return text

    def attack(self, anonymized_text: str, ground_truth: Dict) -> Dict:
        """攻击者攻击"""
        attrs_list = "\n".join([f"- {attr}" for attr in ground_truth.keys()])

        prompt = f"""作为一名专业的隐私攻击者，请分析以下匿名化文本并尝试推断用户的隐私信息。

匿名化文本:
{anonymized_text}

请尝试推断以下属性:
{attrs_list}

对于每个属性，请提供:
1. 推理过程 (inference)
2. 最佳猜测 (guess) - 1-3个可能的值
3. 确定性 (certainty) - 1-5分

请以JSON格式回答:
{{
    "属性名": {{
        "inference": "推理过程",
        "guess": ["猜测1", "猜测2"],
        "certainty": 4
    }}
}}"""

        try:
            result = self.attacker.predict_string(prompt)
            return self._parse_attack_response(result, ground_truth)
        except Exception as e:
            print(f"    攻击失败: {e}")
            return {}

    def _parse_attack_response(self, response: str, ground_truth: Dict) -> Dict:
        """解析攻击响应"""
        try:
            # 提取JSON
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                else:
                    return {}

            attack_data = json.loads(json_str)

            result = {}
            for attr in ground_truth.keys():
                if attr in attack_data:
                    guess = attack_data[attr].get("guess", [])
                    if isinstance(guess, str):
                        guess = [guess]
                    result[attr] = {
                        "inference": attack_data[attr].get("inference", ""),
                        "guess": guess,
                        "certainty": int(attack_data[attr].get("certainty", 3))
                    }
                else:
                    result[attr] = {"inference": "", "guess": [], "certainty": 0}

            return result

        except Exception as e:
            return {}

    def evaluate_utility(self, original_text: str, anonymized_text: str) -> float:
        """使用LLM评估效用"""
        prompt = f"""请评估以下匿名化文本的效用质量。

原始文本:
{original_text}

匿名化文本:
{anonymized_text}

请从以下维度评估（1-10分）:
1. readability: 可读性
2. meaning: 含义保留度
3. hallucinations: 是否有幻觉信息（1=无幻觉，0=有严重幻觉）

输出JSON格式:
{{
    "readability": {{"score": 分数, "explanation": "解释"}},
    "meaning": {{"score": 分数, "explanation": "解释"}},
    "hallucinations": {{"score": 分数, "explanation": "解释"}}
}}"""

        try:
            result = self.utility_model.predict_string(prompt)

            # 解析结果
            if "```json" in result:
                json_start = result.find("```json") + 7
                json_end = result.find("```", json_start)
                json_str = result[json_start:json_end].strip()
            else:
                json_start = result.find("{")
                json_end = result.rfind("}") + 1
                json_str = result[json_start:json_end] if json_start >= 0 else result

            utility_data = json.loads(json_str)

            # 计算效用分数
            readability = utility_data.get("readability", {}).get("score", 5) / 10.0
            meaning = utility_data.get("meaning", {}).get("score", 5) / 10.0
            hallucinations = utility_data.get("hallucinations", {}).get("score", 1)

            utility_score = readability * 0.3 + meaning * 0.5 + hallucinations * 0.2

            return utility_score

        except Exception as e:
            return 0.8  # 默认值

    def train_single_profile(self, profile: Dict) -> Dict:
        """训练单个profile"""
        username = profile["username"]
        original_text = profile["original_text"]
        ground_truth = profile["ground_truth"]

        print(f"\n{'='*60}")
        print(f"Profile: {username}")
        print(f"Ground truth: {ground_truth}")
        print(f"{'='*60}")

        rounds_results = []
        current_text = original_text

        for round_num in range(1, self.cfg.task_config.max_rounds + 1):
            print(f"\n--- Round {round_num} ---")

            # 防御
            print("  🛡️  防御...")
            anonymized_text = self.anonymize(current_text, ground_truth, round_num)

            # 攻击
            print("  ⚔️  攻击...")
            attack_inferences = self.attack(anonymized_text, ground_truth)

            if not attack_inferences:
                print("    攻击失败，跳过")
                continue

            # 评估隐私（使用统一评估器）
            print("  📊 评估隐私...")
            privacy_result = self.evaluator.evaluate_sample(
                ground_truth=ground_truth,
                attack_inferences=attack_inferences,
                utility_score=0.85  # 先用默认值
            )

            # 评估效用
            print("  📊 评估效用...")
            utility_score = self.evaluate_utility(original_text, anonymized_text)

            privacy_score = privacy_result.privacy_score
            attack_success_rate = privacy_result.attack_success_rate
            success = privacy_result.success

            print(f"  隐私: {privacy_score:.3f}, 攻击成功率: {attack_success_rate:.3f}, 效用: {utility_score:.3f}")

            round_result = {
                "round": round_num,
                "anonymized_text": anonymized_text,
                "privacy_score": privacy_score,
                "utility_score": utility_score,
                "attack_success_rate": attack_success_rate,
                "success": success and utility_score >= self.cfg.task_config.min_utility_threshold
            }

            rounds_results.append(round_result)

            # 检查是否达到目标
            if success:
                print(f"  ✓ 达到目标")
                break

            if utility_score < self.cfg.task_config.min_utility_threshold:
                print(f"  ⚠️  效用过低")
                break

            current_text = anonymized_text
            time.sleep(1)

        return {
            "username": username,
            "rounds": rounds_results,
            "final_privacy": rounds_results[-1]["privacy_score"] if rounds_results else 0.0,
            "final_utility": rounds_results[-1]["utility_score"] if rounds_results else 0.0,
            "final_success": rounds_results[-1]["success"] if rounds_results else False,
            "total_rounds": len(rounds_results)
        }

    def run_training(self):
        """运行训练"""
        start_time = time.time()

        print("=" * 80)
        print(f"统一评估标准对抗训练")
        print(f"配置: {self.config_path}")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标隐私: {self.cfg.task_config.stop_threshold.privacy}")
        print(f"最小效用: {self.cfg.task_config.min_utility_threshold}")
        print(f"最大轮次: {self.cfg.task_config.max_rounds}")
        print("=" * 80)

        # 加载profiles
        profiles = self.load_profiles()

        if not profiles:
            print("✗ 没有可训练的profiles")
            return

        # 训练
        results = []

        for i, profile in enumerate(tqdm(profiles, desc="Training profiles")):
            try:
                result = self.train_single_profile(profile)
                results.append(result)
            except Exception as e:
                print(f"\n✗ 训练失败: {e}")
                continue

        # 保存结果（兼容anonymized_results格式）
        self._save_results(results)

        # 打印总结
        self._print_summary(results, start_time)

    def _save_results(self, results: List[Dict]):
        """保存结果"""
        output_file = self.outpath / "unified_adversarial_results.jsonl"

        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

        print(f"\n✓ 结果已保存: {output_file}")

    def _print_summary(self, results: List[Dict], start_time: float):
        """打印总结"""
        if not results:
            return

        privacy_scores = [r["final_privacy"] for r in results]
        utility_scores = [r["final_utility"] for r in results]
        success_count = sum(1 for r in results if r["final_success"])

        elapsed_time = time.time() - start_time

        print("\n" + "=" * 80)
        print("训练完成 - 统计总结")
        print("=" * 80)
        print(f"总样本数: {len(results)}")
        print(f"成功样本数: {success_count}")
        print(f"成功率: {success_count/len(results)*100:.1f}%")
        print(f"\n隐私分数: {np.mean(privacy_scores):.3f} ± {np.std(privacy_scores):.3f}")
        print(f"效用分数: {np.mean(utility_scores):.3f} ± {np.std(utility_scores):.3f}")
        print(f"\n耗时: {elapsed_time/60:.1f} 分钟")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True,
                       choices=["homogeneous_unified", "heterogeneous_unified", "both"],
                       help="配置名称")

    args = parser.parse_args()

    configs = []

    if args.config in ["homogeneous_unified", "both"]:
        configs.append("configs/anonymization/synthetic/06_homogeneous_unified.yaml")

    if args.config in ["heterogeneous_unified", "both"]:
        configs.append("configs/anonymization/synthetic/07_heterogeneous_unified.yaml")

    for config_path in configs:
        print(f"\n{'='*80}")
        print(f"运行配置: {config_path}")
        print(f"{'='*80}")

        try:
            trainer = UnifiedAdversarialTrainer(config_path)
            trainer.run_training()
        except Exception as e:
            print(f"\n✗ 训练失败: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n✓ 所有训练完成")


if __name__ == "__main__":
    main()
