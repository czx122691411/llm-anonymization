#!/usr/bin/env python3
"""
统一评估标准 - 兼容原有框架的对抗训练脚本

输出格式与原有框架完全兼容：
- inference_0.jsonl (可选，如果需要初始推理)
- anonymized_1.jsonl, anonymized_2.jsonl, ...

每个JSONL条目包含完整的Profile结构
"""

import os
import sys
import json
import time
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.providers.registry import get_registry
from src.evaluation.unified_privacy_evaluator import UnifiedPrivacyEvaluator


class Profile:
    """
    简化的Profile类，兼容原有框架的输出格式
    """
    def __init__(self, username: str, original_text: str, ground_truth: Dict, raw_data: Dict = None):
        self.username = username
        # comments数组将存储每轮的结果
        # index 0 = 原始评论
        # index 1 = 第1轮匿名化
        # index 2 = 第2轮匿名化
        # ...
        self.comments = []

        # 添加原始评论（轮次0）
        self.comments.append({
            "comments": self._parse_comments(original_text),
            "num_comments": 1,
            "reviews": self._format_reviews(ground_truth),
            "predictions": {},
            "evaluations": {},
            "utility": {}
        })

        self.raw_data = raw_data or {}

    def _parse_comments(self, text: str) -> List[Dict]:
        """将文本解析为评论数组"""
        return [{
            "text": text,
            "subreddit": "synth",
            "user": self.username,
            "timestamp": "1400463449.0",
            "pii": {}
        }]

    def _format_reviews(self, ground_truth: Dict) -> Dict:
        """格式化ground truth为reviews格式"""
        reviews = {}
        for attr, value in ground_truth.items():
            if "reviews" not in reviews:
                reviews["synth"] = {}
            reviews["synth"][attr] = {
                "estimate": value,
                "detect_from_subreddit": False,
                "hardness": 1,
                "certainty": 5
            }
        return reviews

    def add_round(self, anonymized_text: str, attack_inferences: Dict,
                  privacy_score: float, utility_score: float,
                  attack_success_rate: float, round_num: int):
        """添加一轮对抗结果"""
        self.comments.append({
            "comments": self._parse_comments(anonymized_text),
            "num_comments": 1,
            "reviews": self.comments[0]["reviews"].copy(),  # 复制原始reviews
            "predictions": {
                "attack_model": attack_inferences
            },
            "evaluations": {
                "unified_evaluator": {
                    "privacy_score": privacy_score,
                    "attack_success_rate": attack_success_rate,
                    "round": round_num
                }
            },
            "utility": {
                "evaluator_model": {
                    "overall_score": utility_score,
                    "round": round_num
                }
            }
        })

    def to_json(self) -> Dict:
        """转换为JSON格式（兼容原有框架）"""
        return {
            "username": self.username,
            "comments": self.comments
        }


class CompatibleAdversarialTrainer:
    """兼容原有框架的对抗训练器"""

    def __init__(self, config_path: str):
        self.config_path = config_path

        # 加载YAML配置
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.task_config = self.config['task_config']

        # 创建统一评估器
        self.evaluator = UnifiedPrivacyEvaluator(
            target_privacy=self.task_config['stop_threshold']['privacy'],
            min_utility=self.task_config['min_utility_threshold'],
            semantic_threshold=0.7
        )

        # 创建模型
        print(f"创建模型...")
        registry = get_registry(region="china")

        self.defender = registry.create_model_instance(
            self.task_config['anon_model']['name'],
            **self.task_config['anon_model']['args']
        )

        self.attacker = registry.create_model_instance(
            self.task_config['attack_model']['name'],
            **self.task_config['attack_model']['args']
        )

        self.utility_model = registry.create_model_instance(
            self.task_config['utility_model']['name'],
            **self.task_config['utility_model']['args']
        )

        if not all([self.defender, self.attacker, self.utility_model]):
            raise RuntimeError("模型创建失败")

        print(f"✓ 防御者: {self.task_config['anon_model']['name']}")
        print(f"✓ 攻击者: {self.task_config['attack_model']['name']}")
        print(f"✓ 效用模型: {self.task_config['utility_model']['name']}")
        print(f"✓ 评估器: UnifiedPrivacyEvaluator")

        # 创建输出目录
        self.outpath = Path(self.task_config['outpath'])
        self.outpath.mkdir(parents=True, exist_ok=True)

        # 攻击者模型名称（用于存储）
        self.attacker_name = self.task_config['attack_model']['name'].replace("-", "_")
        self.utility_name = self.task_config['utility_model']['name'].replace("-", "_")

    def load_profiles(self) -> List[Profile]:
        """加载profiles"""
        print(f"\n加载profiles: {self.task_config['profile_path']}")

        profiles = []
        profile_path = Path(self.task_config['profile_path'])

        with open(profile_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if len(profiles) >= self.task_config['num_profiles']:
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

    def _parse_profile(self, data: Dict, line_num: int) -> Profile:
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

            return Profile(username, original_text, ground_truth, data)

        except Exception as e:
            return None

    def _generate_improvement_feedback(self, profile: Profile, round_num: int) -> str:
        """生成攻击反馈"""
        if round_num == 1:
            return "这是初始匿名化，请尽力保护隐私。"

        # 获取上一轮结果
        last_round = profile.comments[-1]
        evals = last_round.get("evaluations", {}).get("unified_evaluator", {})
        preds = last_round.get("predictions", {}).get("attack_model", {})

        privacy_score = evals.get("privacy_score", 0)
        attack_success_rate = evals.get("attack_success_rate", 0)

        feedback = f"上一轮匿名化结果：\n"
        feedback += f"隐私分数: {privacy_score:.2f}\n"
        feedback += f"攻击成功率: {attack_success_rate:.1%}\n\n"

        # 分析泄露的属性
        leaked = []
        for attr, true_val in profile.comments[0]["reviews"].get("synth", {}).items():
            true_val = true_val.get("estimate", "")
            if attr in preds:
                guesses = preds[attr].get("guess", [])
                if true_val in guesses:
                    leaked.append(f"- {attr}: 真实值 '{true_val}' 被猜出")

        if leaked:
            feedback += "严重泄露：\n" + "\n".join(leaked) + "\n"
            feedback += "必须更激进地泛化这些信息！\n"
        else:
            feedback += "隐私保护良好\n"

        return feedback

    def anonymize(self, profile: Profile, round_num: int) -> str:
        """防御者匿名化"""
        ground_truth = {}
        for attr, attr_data in profile.comments[0]["reviews"].get("synth", {}).items():
            ground_truth[attr] = attr_data.get("estimate", "")

        attrs = ", ".join(ground_truth.keys())
        original_text = profile.comments[0]["comments"][0]["text"]

        # 获取攻击反馈
        feedback = self._generate_improvement_feedback(profile, round_num)

        if round_num == 1:
            prompt = f"""请对以下文本进行匿名化处理，保护个人隐私信息。

原始文本:
{original_text}

需要保护的属性:
{attrs}

要求:
1. 移除或泛化上述属性的具体信息
2. 保持文本的自然流畅和语义
3. 使用通用表述替代具体信息
4. 确保文本仍然可读

匿名化文本:"""
        else:
            prompt = f"""请根据以下攻击反馈改进匿名化：

原始文本:
{original_text}

{feedback}

改进后的匿名化文本:"""

        try:
            result = self.defender.predict_string(prompt)

            # 清理结果
            lines = result.split('\n')
            anonymized_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('说明') and not line.startswith('注意') and not line.startswith('匿名化文本:'):
                    anonymized_lines.append(line)

            return '\n'.join(anonymized_lines) if anonymized_lines else result

        except Exception as e:
            print(f"    匿名化失败: {e}")
            return original_text

    def attack(self, anonymized_text: str, profile: Profile) -> Dict:
        """攻击者攻击"""
        ground_truth = {}
        for attr, attr_data in profile.comments[0]["reviews"].get("synth", {}).items():
            ground_truth[attr] = attr_data.get("estimate", "")

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

    def evaluate_utility(self, profile: Profile, anonymized_text: str) -> float:
        """使用LLM评估效用"""
        original_text = profile.comments[0]["comments"][0]["text"]

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
            return 0.8

    def train_single_profile(self, profile: Profile) -> Profile:
        """训练单个profile"""
        print(f"\n{'='*60}")
        print(f"Profile: {profile.username}")
        print(f"{'='*60}")

        for round_num in range(1, self.task_config['max_rounds'] + 1):
            print(f"\n--- Round {round_num} ---")

            # 防御
            print("  🛡️  防御...")
            anonymized_text = self.anonymize(profile, round_num)

            # 攻击
            print("  ⚔️  攻击...")
            attack_inferences = self.attack(anonymized_text, profile)

            if not attack_inferences:
                print("    攻击失败，跳过")
                continue

            # 评估隐私
            print("  📊 评估隐私...")
            ground_truth = {}
            for attr, attr_data in profile.comments[0]["reviews"].get("synth", {}).items():
                ground_truth[attr] = attr_data.get("estimate", "")

            privacy_result = self.evaluator.evaluate_sample(
                ground_truth=ground_truth,
                attack_inferences=attack_inferences,
                utility_score=0.85
            )

            # 评估效用
            print("  📊 评估效用...")
            utility_score = self.evaluate_utility(profile, anonymized_text)

            privacy_score = privacy_result.privacy_score
            attack_success_rate = privacy_result.attack_success_rate
            success = privacy_result.success

            print(f"  隐私: {privacy_score:.3f}, 攻击成功率: {attack_success_rate:.3f}, 效用: {utility_score:.3f}")

            # 添加到profile
            profile.add_round(
                anonymized_text=anonymized_text,
                attack_inferences=attack_inferences,
                privacy_score=privacy_score,
                utility_score=utility_score,
                attack_success_rate=attack_success_rate,
                round_num=round_num
            )

            # 检查是否达到目标
            if success and utility_score >= self.task_config['min_utility_threshold']:
                print(f"  ✓ 达到目标")
                break

            if utility_score < self.task_config['min_utility_threshold']:
                print(f"  ⚠️  效用过低")
                break

            time.sleep(0.5)

        return profile

    def run_training(self):
        """运行训练"""
        start_time = time.time()

        print("=" * 80)
        print(f"统一评估标准对抗训练 (兼容原有框架格式)")
        print(f"配置: {self.config_path}")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标隐私: {self.task_config['stop_threshold']['privacy']}")
        print(f"最小效用: {self.task_config['min_utility_threshold']}")
        print(f"最大轮次: {self.task_config['max_rounds']}")
        print("=" * 80)

        # 加载profiles
        profiles = self.load_profiles()

        if not profiles:
            print("✗ 没有可训练的profiles")
            return

        # 训练所有profiles到完成
        trained_profiles = []
        for profile in tqdm(profiles, desc="Training profiles"):
            try:
                result = self.train_single_profile(profile)
                trained_profiles.append(result)
            except Exception as e:
                print(f"\n✗ 训练失败 {profile.username}: {e}")
                continue

        # 按轮次保存结果（兼容原有框架格式）
        max_rounds = max(len(p.comments) - 1 for p in trained_profiles)

        for round_num in range(1, max_rounds + 1):
            self._save_round_results(trained_profiles, round_num)

        # 打印总结
        self._print_summary(trained_profiles, start_time)

    def _save_round_results(self, profiles: List[Profile], round_num: int):
        """保存一轮的结果（兼容原有框架格式）"""
        # 保存 anonymized_{round_num}.jsonl
        anonymized_file = self.outpath / f"anonymized_{round_num}.jsonl"

        with open(anonymized_file, 'w', encoding='utf-8') as f:
            for profile in profiles:
                # 只保存到当前轮次的结果
                if len(profile.comments) > round_num:
                    profile_data = {
                        "username": profile.username,
                        "comments": profile.comments[:round_num + 1]  # 包含原始评论 + 当前轮次
                    }
                    f.write(json.dumps(profile_data, ensure_ascii=False) + "\n")
                    f.flush()

        print(f"\n✓ 第{round_num}轮结果已保存: {anonymized_file}")

    def _print_summary(self, profiles: List[Profile], start_time: float):
        """打印总结"""
        if not profiles:
            return

        # 收集最后一轮的统计
        privacy_scores = []
        utility_scores = []
        success_count = 0

        for profile in profiles:
            if len(profile.comments) > 1:  # 至少有一轮匿名化
                last_round = profile.comments[-1]
                evals = last_round.get("evaluations", {}).get("unified_evaluator", {})
                utility = last_round.get("utility", {}).get("evaluator_model", {}).get("overall_score", 0)

                privacy = evals.get("privacy_score", 0)
                privacy_scores.append(privacy)
                utility_scores.append(utility)

                if privacy >= self.task_config['stop_threshold']['privacy'] and utility >= self.task_config['min_utility_threshold']:
                    success_count += 1

        elapsed_time = time.time() - start_time

        print("\n" + "=" * 80)
        print("训练完成 - 统计总结")
        print("=" * 80)
        print(f"总样本数: {len(profiles)}")
        print(f"成功样本数: {success_count}")
        print(f"成功率: {success_count/len(profiles)*100:.1f}%")

        if privacy_scores:
            print(f"\n隐私分数: {np.mean(privacy_scores):.3f} ± {np.std(privacy_scores):.3f}")
            print(f"效用分数: {np.mean(utility_scores):.3f} ± {np.std(utility_scores):.3f}")

        print(f"\n耗时: {elapsed_time/60:.1f} 分钟")
        print("=" * 80)


def main():
    import argparse

    script_dir = Path(__file__).parent.parent
    config_base = script_dir / "configs/anonymization/synthetic"

    configs = {
        "homogeneous": script_dir / "configs/anonymization/synthetic/06_homogeneous_unified.yaml",
        "heterogeneous": script_dir / "configs/anonymization/synthetic/07_heterogeneous_unified.yaml"
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="both",
                       choices=["homogeneous", "heterogeneous", "both"],
                       help="配置名称")

    args = parser.parse_args()

    configs_to_run = []

    if args.config in ["homogeneous", "both"]:
        configs_to_run.append(configs["homogeneous"])

    if args.config in ["heterogeneous", "both"]:
        configs_to_run.append(configs["heterogeneous"])

    for config_path in configs_to_run:
        print(f"\n{'='*80}")
        print(f"运行配置: {config_path}")
        print(f"{'='*80}")

        try:
            trainer = CompatibleAdversarialTrainer(str(config_path))
            trainer.run_training()
        except Exception as e:
            print(f"\n✗ 训练失败: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n✓ 所有训练完成")


if __name__ == "__main__":
    main()
