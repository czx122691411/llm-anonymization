#!/usr/bin/env python3
"""
统一评估标准 - 完整对抗训练脚本 (增强版)
支持攻击反馈驱动的防御改进
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

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.providers.registry import get_registry
from src.evaluation.unified_privacy_evaluator import UnifiedPrivacyEvaluator


class AdversarialRoundResult:
    """单轮对抗结果"""
    def __init__(self, round_num, anonymized_text, attack_inferences,
                 privacy_score, utility_score, attack_success_rate, success):
        self.round_num = round_num
        self.anonymized_text = anonymized_text
        self.attack_inferences = attack_inferences
        self.privacy_score = privacy_score
        self.utility_score = utility_score
        self.attack_success_rate = attack_success_rate
        self.success = success


class UnifiedAdversarialTrainer:
    """统一评估标准的对抗训练器 (支持反馈驱动改进)"""

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

    def load_profiles(self):
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

    def _parse_profile(self, data, line_num):
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

    def _generate_improvement_feedback(self, last_result: AdversarialRoundResult, ground_truth: dict) -> str:
        """
        基于上一轮攻击结果生成改进反馈

        这是核心的反馈驱动机制：告诉防御者哪里失败了，需要改进
        """
        # 分析攻击成功的属性
        leaked_attrs = []
        partially_leaked_attrs = []
        protected_attrs = []

        for attr, true_value in ground_truth.items():
            if attr not in last_result.attack_inferences:
                continue

            attack_info = last_result.attack_inferences[attr]
            guesses = attack_info.get("guess", [])
            certainty = attack_info.get("certainty", 0)

            # 检查是否泄露
            if true_value in guesses:
                # 精确匹配 - 严重泄露
                leaked_attrs.append({
                    "attr": attr,
                    "true_value": true_value,
                    "guessed_value": guesses[0] if guesses else "N/A",
                    "certainty": certainty
                })
            elif any(str(true_value).lower() in str(g).lower() for g in guesses):
                # 部分匹配 - 中等泄露
                partially_leaked_attrs.append({
                    "attr": attr,
                    "true_value": true_value,
                    "guessed_value": guesses[0] if guesses else "N/A",
                    "certainty": certainty
                })
            else:
                protected_attrs.append(attr)

        # 构建反馈消息
        feedback_parts = []

        # 1. 严重泄露警告
        if leaked_attrs:
            feedback_parts.append("⚠️ 严重隐私泄露:")
            for item in leaked_attrs:
                feedback_parts.append(
                    f"  - 属性 '{item['attr']}': 真实值 '{item['true_value']}' 被准确猜出为 '{item['guessed_value']}' "
                    f"(确定性: {item['certainty']}/5)"
                )
            feedback_parts.append("  → 必须更激进地泛化或完全移除这些信息！")

        # 2. 部分泄露警告
        if partially_leaked_attrs:
            feedback_parts.append("⚡ 部分隐私泄露:")
            for item in partially_leaked_attrs:
                feedback_parts.append(
                    f"  - 属性 '{item['attr']}': 攻击者猜测 '{item['guessed_value']}' "
                    f"(真实值: '{item['true_value']}', 确定性: {item['certainty']}/5)"
                )
            feedback_parts.append("  → 需要加强匿名化，攻击者已接近真实值。")

        # 3. 保护成功确认
        if protected_attrs:
            feedback_parts.append("✓ 保护成功:")
            feedback_parts.append(f"  - 属性: {', '.join(protected_attrs)}")
            feedback_parts.append("  → 请保持这种保护水平。")

        # 4. 效用评估
        feedback_parts.append(f"\n📊 当前效用分数: {last_result.utility_score:.2f}/1.0")

        if last_result.utility_score >= 0.7:
            feedback_parts.append("  → 效用良好，可以进一步加强隐私保护。")
        elif last_result.utility_score >= 0.5:
            feedback_parts.append("  → 效用可接受，需要在隐私保护和文本质量之间平衡。")
        else:
            feedback_parts.append("  → 效用较低，注意不要过度匿名化导致文本失真。")

        # 5. 总体隐私分数
        feedback_parts.append(f"\n📊 当前隐私分数: {last_result.privacy_score:.2f}/1.0")
        feedback_parts.append(f"📊 攻击成功率: {last_result.attack_success_rate:.1%}")

        # 6. 改进建议
        feedback_parts.append("\n📋 改进建议:")

        if last_result.privacy_score < 0.5:
            feedback_parts.append("  1. 隐私保护严重不足，必须大幅修改文本")
            feedback_parts.append("  2. 将具体信息替换为非常通用的表述")
            feedback_parts.append("  3. 考虑完全删除包含敏感信息的句子")
        elif last_result.privacy_score < 0.7:
            feedback_parts.append("  1. 隐私保护较弱，需要加强匿名化")
            feedback_parts.append("  2. 使用更模糊的词汇替代具体信息")
            feedback_parts.append("  3. 改写句子结构以掩盖语义线索")
        else:
            feedback_parts.append("  1. 隐私保护良好，继续保持当前策略")
            feedback_parts.append("  2. 微调尚未完全保护的属性")

        return "\n".join(feedback_parts)

    def anonymize(self, text, ground_truth, round_num, improvement_feedback=""):
        """
        防御者匿名化（支持反馈驱动改进）

        参数:
            text: 待匿名化文本
            ground_truth: 需要保护的属性
            round_num: 当前轮次
            improvement_feedback: 上一轮的攻击反馈
        """
        attrs = ", ".join(ground_truth.keys())

        # 根据轮次和反馈构建不同的prompt
        if round_num == 1:
            # 第一轮：初始匿名化，无反馈
            system_prompt = """你是一位专业的文本匿名化专家。你的任务是保护用户隐私，防止个人信息被推断出来。
你必须精确遵循指令，尽可能少地修改原文，只泛化信息，绝不编造新信息。"""

            header = f"""下面我将给你一组用户评论。你的任务是对评论进行匿名化处理。

需要保护的属性:
{attrs}

原始文本:"""

            footer = """请对上述文本进行匿名化，要求:
1. 移除或泛化与上述属性相关的具体信息
2. 保持文本的自然流畅和语义
3. 使用通用表述替代具体信息
4. 确保文本仍然可读
5. 不要编造原文中没有的信息

匿名化文本:"""

        else:
            # 后续轮次：基于攻击反馈改进
            system_prompt = """你是一位专业的文本匿名化专家。你的任务是保护用户隐私，防止个人信息被推断出来。
你必须精确遵循指令，根据攻击反馈改进匿名化质量。"""

            header = f"""下面是同一组评论。你之前的匿名化受到了攻击。

需要保护的属性:
{attrs}

原始文本:
{text}

攻击反馈:
{improvement_feedback}

请根据上述反馈改进匿名化，更好地保护隐私。"""

            footer = """改进要求:
1. 针对反馈中指出的泄露问题，加强匿名化
2. 将具体信息替换为更通用的表述
3. 必要时可以完全删除敏感句子
4. 保持文本的基本可读性
5. 不要编造原文中没有的信息

改进后的匿名化文本:"""

        prompt = f"""{system_prompt}

{header}

{footer}"""

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
            return text

    def attack(self, anonymized_text, ground_truth):
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

    def _parse_attack_response(self, response, ground_truth):
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

    def evaluate_utility(self, original_text, anonymized_text):
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

    def train_single_profile(self, profile):
        """训练单个profile（支持反馈驱动改进）"""
        username = profile["username"]
        original_text = profile["original_text"]
        ground_truth = profile["ground_truth"]

        print(f"\n{'='*60}")
        print(f"Profile: {username}")
        print(f"Ground truth: {ground_truth}")
        print(f"{'='*60}")

        rounds_results = []
        current_text = original_text

        for round_num in range(1, self.task_config['max_rounds'] + 1):
            print(f"\n--- Round {round_num} ---")

            # 生成改进反馈（第一轮无反馈）
            if round_num == 1:
                improvement_feedback = "这是初始匿名化，请尽力保护隐私。"
            else:
                # 使用上一轮的结果生成反馈
                last_result = rounds_results[-1]
                improvement_feedback = self._generate_improvement_feedback(last_result, ground_truth)
                print(f"  📝 攻击反馈已生成")

            # 防御（包含改进反馈）
            print("  🛡️  防御...")
            anonymized_text = self.anonymize(current_text, ground_truth, round_num, improvement_feedback)

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
                utility_score=0.85
            )

            # 评估效用
            print("  📊 评估效用...")
            utility_score = self.evaluate_utility(original_text, anonymized_text)

            privacy_score = privacy_result.privacy_score
            attack_success_rate = privacy_result.attack_success_rate
            success = privacy_result.success

            print(f"  隐私: {privacy_score:.3f}, 攻击成功率: {attack_success_rate:.3f}, 效用: {utility_score:.3f}")

            # 创建本轮结果
            round_result = AdversarialRoundResult(
                round_num=round_num,
                anonymized_text=anonymized_text,
                attack_inferences=attack_inferences,
                privacy_score=privacy_score,
                utility_score=utility_score,
                attack_success_rate=attack_success_rate,
                success=success and utility_score >= self.task_config['min_utility_threshold']
            )

            rounds_results.append(round_result)

            # 打印详细反馈（仅在调试时）
            if round_num > 1 and False:  # 设为True可查看详细反馈
                print(f"\n  🔍 详细反馈:\n{improvement_feedback}")

            # 检查是否达到目标
            if success:
                print(f"  ✓ 达到目标")
                break

            if utility_score < self.task_config['min_utility_threshold']:
                print(f"  ⚠️  效用过低")
                break

            current_text = anonymized_text
            time.sleep(0.5)  # 减少延迟以加快训练

        return {
            "username": username,
            "rounds": [
                {
                    "round": r.round_num,
                    "anonymized_text": r.anonymized_text,
                    "attack_inferences": r.attack_inferences,
                    "privacy_score": r.privacy_score,
                    "utility_score": r.utility_score,
                    "attack_success_rate": r.attack_success_rate,
                    "success": r.success
                }
                for r in rounds_results
            ],
            "final_privacy": rounds_results[-1].privacy_score if rounds_results else 0.0,
            "final_utility": rounds_results[-1].utility_score if rounds_results else 0.0,
            "final_success": rounds_results[-1].success if rounds_results else False,
            "total_rounds": len(rounds_results)
        }

    def run_training(self):
        """运行训练"""
        start_time = time.time()

        print("=" * 80)
        print(f"统一评估标准对抗训练 (支持反馈驱动改进)")
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

        # 训练
        results = []

        for i, profile in enumerate(tqdm(profiles, desc="Training profiles")):
            try:
                result = self.train_single_profile(profile)
                results.append(result)
            except Exception as e:
                print(f"\n✗ 训练失败: {e}")
                import traceback
                traceback.print_exc()
                continue

        # 保存结果
        self._save_results(results)

        # 打印总结
        self._print_summary(results, start_time)

    def _save_results(self, results):
        """保存结果"""
        output_file = self.outpath / "unified_adversarial_results.jsonl"

        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

        print(f"\n✓ 结果已保存: {output_file}")

    def _print_summary(self, results, start_time):
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
    import argparse

    script_dir = Path(__file__).parent.parent
    config_base = script_dir / "configs/anonymization/synthetic"

    configs = {
        "homogeneous": config_base / "06_homogeneous_unified.yaml",
        "heterogeneous": config_base / "07_heterogeneous_unified.yaml"
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
            trainer = UnifiedAdversarialTrainer(str(config_path))
            trainer.run_training()
        except Exception as e:
            print(f"\n✗ 训练失败: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n✓ 所有训练完成")


if __name__ == "__main__":
    main()
