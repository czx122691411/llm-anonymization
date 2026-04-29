#!/usr/bin/env python3
"""
使用千问模型重新评估同构DeepSeek实验结果
确保与异构实验使用相同的评估方法，实现公平对比

控制变量：
- 攻击者：deepseek-reasoner（与异构Config 1相同）
- 评估者：qwen-max（与异构Config 1相同）
- 防御者：deepseek-chat（同构实验使用的模型）
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import numpy as np

from src.models.providers.registry import get_registry


class HomogeneousQwenEvaluator:
    """使用千问模型评估同构DeepSeek结果"""

    def __init__(self):
        # 使用与异构Config 1完全相同的模型配置
        self.attacker_name = "deepseek-reasoner"  # 与异构相同
        self.evaluator_name = "qwen-max"          # 与异构相同
        self.defender_name = "deepseek-chat"      # 同构防御者

        self.target_privacy = 0.8
        self.min_utility = 0.6

        # 获取模型实例
        registry = get_registry(region="china")
        self.attacker_model = registry.create_model_instance(self.attacker_name)
        self.evaluator_model = registry.create_model_instance(self.evaluator_name)

        # 数据路径
        self.data_dir = Path("/home/rooter/llm-anonymization/anonymized_results/synthetic/deepseek_full")
        self.output_dir = Path("/home/rooter/llm-anonymization/homogeneous_results_qwen")

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_samples(self) -> List[Dict[str, Any]]:
        """加载所有样本数据"""
        samples = []

        # 读取4轮匿名化结果
        for round_num in range(1, 5):
            file_path = self.data_dir / f"anonymized_{round_num}.jsonl"

            if not file_path.exists():
                print(f"警告: 文件不存在 {file_path}")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        username = data.get("username")

                        # 提取原始文本和匿名化文本
                        comments = data.get("comments", [])

                        if len(comments) < 2:
                            continue

                        # comments[0] 是原始文本
                        original_comments = comments[0].get("comments", [])

                        # comments[1] 是第一轮匿名化，comments[2] 是第二轮，等等
                        if round_num < len(comments):
                            anonymized_comments = comments[round_num].get("comments", [])
                        else:
                            continue

                        if not original_comments or not anonymized_comments:
                            continue

                        # 提取真实标签
                        reviews = data.get("reviews", {})
                        ground_truth = {}

                        for category, category_data in reviews.items():
                            for attr, attr_data in category_data.items():
                                ground_truth[attr] = attr_data.get("estimate")

                        if not ground_truth:
                            continue

                        # 构建样本
                        sample = {
                            "username": username,
                            "round": round_num,
                            "original_text": " ".join([c.get("text", "") for c in original_comments]),
                            "anonymized_text": " ".join([c.get("text", "") for c in anonymized_comments]),
                            "ground_truth": ground_truth,
                            "line_num": line_num
                        }

                        samples.append(sample)

                    except Exception as e:
                        print(f"解析错误 (行 {line_num}): {e}")
                        continue

        print(f"成功加载 {len(samples)} 个样本")
        return samples

    def attack_anonymized_text(self, anonymized_text: str, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """使用攻击者模型推断隐私信息"""
        # 构建攻击提示词
        ground_truth_str = json.dumps(ground_truth, ensure_ascii=False)

        prompt = f"""你是一个隐私攻击者，试图从以下匿名化文本中推断用户的真实信息。

目标属性类型（请推断这些）:
{list(ground_truth.keys())}

匿名化文本:
{anonymized_text}

请对每个目标属性进行推断，输出格式为JSON:
{{
    "属性名": {{
        "inference": "推理过程",
        "guess": ["推测1", "推测2", "推测3"],
        "certainty": "1-5的确定性评分"
    }}
}}

只输出JSON，不要其他内容。"""

        try:
            from src.prompts import Prompt
            prompt_obj = Prompt(prompt)
            response_text = self.attacker_model.predict(prompt_obj)

            # 解析攻击结果
            try:
                # 尝试提取JSON
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                attack_result = json.loads(response_text)
                return attack_result
            except:
                return {}

        except Exception as e:
            print(f"攻击错误: {e}")
            return {}

    def evaluate_with_qwen(self, original_text: str, anonymized_text: str,
                                 ground_truth: Dict[str, Any], attack_result: Dict[str, Any]) -> Dict[str, Any]:
        """使用千问模型评估隐私和效用"""

        # 计算隐私分数
        privacy_scores = []

        for attr, true_value in ground_truth.items():
            if attr not in attack_result:
                # 攻击者未能推断，说明隐私保护成功
                privacy_scores.append(1.0)
                continue

            guess_data = attack_result[attr]
            guesses = guess_data.get("guess", [])

            # 检查是否推断出真实值
            if true_value in guesses:
                # 推断成功，隐私泄露
                # 根据确定性调整分数
                certainty = int(guess_data.get("certainty", 3))
                leak_score = certainty / 5.0  # 确定性越高，泄露越严重
                privacy_score = 1.0 - leak_score
                privacy_scores.append(privacy_score)
            else:
                # 推断失败，隐私保护成功
                privacy_scores.append(1.0)

        # 平均隐私分数
        avg_privacy = np.mean(privacy_scores) if privacy_scores else 0.0

        # 使用千问评估效用
        utility_prompt = f"""请评估以下匿名化文本的效用质量。

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
}}

只输出JSON，不要其他内容。"""

        try:
            from src.prompts import Prompt
            prompt_obj = Prompt(utility_prompt)
            response_text = self.evaluator_model.predict(prompt_obj)

            # 解析效用结果
            try:
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                utility_result = json.loads(response_text)

                # 计算综合效用分数
                readability = utility_result.get("readability", {}).get("score", 0) / 10.0
                meaning = utility_result.get("meaning", {}).get("score", 0) / 10.0
                hallucinations = utility_result.get("hallucinations", {}).get("score", 0)

                # 效用公式：综合可读性、含义保留、无幻觉
                utility_score = (readability * 0.3 + meaning * 0.5 + hallucinations * 0.2)

                return {
                    "privacy_score": avg_privacy,
                    "utility_score": utility_score,
                    "privacy_details": privacy_scores,
                    "utility_details": utility_result,
                    "attack_result": attack_result
                }
            except Exception as e:
                print(f"解析效用结果错误: {e}")
                return {
                    "privacy_score": avg_privacy,
                    "utility_score": 0.0,
                    "privacy_details": privacy_scores,
                    "utility_details": {},
                    "attack_result": attack_result
                }
        except Exception as e:
            print(f"效用评估错误: {e}")
            return {
                "privacy_score": avg_privacy,
                "utility_score": 0.0,
                "privacy_details": privacy_scores,
                "utility_details": {},
                "attack_result": attack_result
            }

    def evaluate_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个样本"""
        username = sample["username"]

        print(f"\n评估用户: {username} (第{sample['round']}轮)")

        # 步骤1: 攻击
        attack_result = self.attack_anonymized_text(
            sample["anonymized_text"],
            sample["ground_truth"]
        )

        # 步骤2: 评估
        evaluation = self.evaluate_with_qwen(
            sample["original_text"],
            sample["anonymized_text"],
            sample["ground_truth"],
            attack_result
        )

        # 构建结果
        result = {
            "username": username,
            "round": sample["round"],
            "ground_truth": sample["ground_truth"],
            "privacy_score": evaluation["privacy_score"],
            "utility_score": evaluation["utility_score"],
            "success": evaluation["privacy_score"] >= self.target_privacy and
                      evaluation["utility_score"] >= self.min_utility,
            "attack_result": evaluation["attack_result"],
            "evaluation_details": evaluation["utility_details"]
        }

        print(f"  隐私: {evaluation['privacy_score']:.3f}, 效用: {evaluation['utility_score']:.3f}, "
              f"成功: {result['success']}")

        return result

    def run_evaluation(self, max_samples: int = None):
        """运行评估"""
        print("=" * 80)
        print("同构DeepSeek - 千问模型重新评估")
        print("=" * 80)
        print(f"攻击者: {self.attacker_name}")
        print(f"评估者: {self.evaluator_name}")
        print(f"防御者: {self.defender_name}")
        print(f"目标隐私: {self.target_privacy}, 最小效用: {self.min_utility}")
        print("=" * 80)

        # 加载样本
        samples = self.load_samples()

        if max_samples:
            samples = samples[:max_samples]
            print(f"评估前 {max_samples} 个样本")

        # 评估所有样本
        results = []
        for i, sample in enumerate(samples, 1):
            print(f"\n进度: {i}/{len(samples)}")

            try:
                result = self.evaluate_sample(sample)
                results.append(result)

                # 每10个样本保存一次
                if i % 10 == 0:
                    self.save_intermediate_results(results, i)

            except Exception as e:
                print(f"评估样本 {i} 失败: {e}")
                continue

        # 保存最终结果
        self.save_final_results(results)

        # 生成统计报告
        self.generate_statistics(results)

    def save_intermediate_results(self, results: List[Dict], count: int):
        """保存中间结果"""
        checkpoint_file = self.output_dir / f"checkpoint_{count}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "count": count,
                "results": results
            }, f, ensure_ascii=False, indent=2)
        print(f"保存中间结果: {checkpoint_file}")

    def save_final_results(self, results: List[Dict]):
        """保存最终结果"""
        # 完整结果
        results_file = self.output_dir / "evaluation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "defender": self.defender_name,
                    "attacker": self.attacker_name,
                    "evaluator": self.evaluator_name,
                    "target_privacy": self.target_privacy,
                    "min_utility": self.min_utility,
                    "timestamp": datetime.now().isoformat()
                },
                "results": results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n保存最终结果: {results_file}")

    def generate_statistics(self, results: List[Dict]):
        """生成统计报告"""
        if not results:
            print("没有结果可统计")
            return

        privacy_scores = [r["privacy_score"] for r in results]
        utility_scores = [r["utility_score"] for r in results]
        success_count = sum(1 for r in results if r["success"])

        stats = {
            "total_samples": len(results),
            "privacy": {
                "mean": np.mean(privacy_scores),
                "std": np.std(privacy_scores),
                "min": np.min(privacy_scores),
                "max": np.max(privacy_scores)
            },
            "utility": {
                "mean": np.mean(utility_scores),
                "std": np.std(utility_scores),
                "min": np.min(utility_scores),
                "max": np.max(utility_scores)
            },
            "success": {
                "count": success_count,
                "rate": success_count / len(results) * 100
            },
            "privacy_success_rate": sum(1 for p in privacy_scores if p >= self.target_privacy) / len(privacy_scores) * 100,
            "utility_success_rate": sum(1 for u in utility_scores if u >= self.min_utility) / len(utility_scores) * 100
        }

        # 保存统计
        stats_file = self.output_dir / "statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        # 打印报告
        print("\n" + "=" * 80)
        print("评估统计报告")
        print("=" * 80)
        print(f"总样本数: {stats['total_samples']}")
        print(f"\n隐私分数:")
        print(f"  平均: {stats['privacy']['mean']:.3f} ± {stats['privacy']['std']:.3f}")
        print(f"  范围: [{stats['privacy']['min']:.3f}, {stats['privacy']['max']:.3f}]")
        print(f"  达标率 (≥{self.target_privacy}): {stats['privacy_success_rate']:.1f}%")

        print(f"\n效用分数:")
        print(f"  平均: {stats['utility']['mean']:.3f} ± {stats['utility']['std']:.3f}")
        print(f"  范围: [{stats['utility']['min']:.3f}, {stats['utility']['max']:.3f}]")
        print(f"  达标率 (≥{self.min_utility}): {stats['utility_success_rate']:.1f}%")

        print(f"\n综合成功率:")
        print(f"  数量: {stats['success']['count']}/{stats['total_samples']}")
        print(f"  比率: {stats['success']['rate']:.1f}%")

        print("=" * 80)


def main():
    """主函数"""
    evaluator = HomogeneousQwenEvaluator()

    # 可以设置max_samples限制评估数量，None表示评估所有样本
    # 扩大评估规模以提高统计显著性（目标：263个样本，与异构配置相同）
    # 设置为263以匹配异构配置的样本量，确保统计对比的公平性
    target_samples = 263  # 与异构配置相同的样本量
    evaluator.run_evaluation(max_samples=target_samples)


if __name__ == "__main__":
    main()
