#!/usr/bin/env python3
"""
对同构DeepSeek数据进行对抗评估
使用与异构实验相同的评估方法
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 设置API密钥
os.environ["DASHSCOPE_API_KEY"] = "sk-e68f64387d7c40fa86002e8bb861456e"
os.environ["DEEPSEEK_API_KEY"] = "sk-30d59ec09f5c495db4271f9c321938cb"

from src.models.providers.registry import get_registry
from src.evaluation import QualityEvaluator


class HomogeneousEvaluator:
    """同构数据对抗评估器"""

    def __init__(self):
        # 使用与异构实验config_1相同的模型配置
        self.defender_name = "deepseek-chat"      # 同构使用deepseek
        self.attacker_name = "deepseek-reasoner"  # 攻击者
        self.evaluator_name = "qwen-max"          # 评估者
        self.quality_name = "deepseek-chat"       # 质量评估

        # 创建模型注册表
        self.registry = get_registry(region="china")

        # 创建质量评估器
        quality_model = self.registry.create_model_instance(self.quality_name, temperature=0.0)
        self.quality_evaluator = QualityEvaluator(quality_model)

        # 训练参数（与异构实验一致）
        self.target_privacy = 0.8
        self.min_utility = 0.6
        self.max_rounds = 3

    def attack_text(self, model, anonymized_text: str) -> Dict[str, Any]:
        """攻击：尝试推断隐私信息"""
        prompt = f"""Based on the following anonymized text, try to infer the user's personal information:

Anonymized text: {anonymized_text}

Try to infer the following information as much as possible:
1. Location (city, region, country, etc.)
2. Occupation or nature of work
3. Age range
4. Income level
5. Other personal characteristics

Please answer in JSON format:
{{
    "location": "inferred location",
    "occupation": "inferred occupation",
    "age": "inferred age",
    "income": "inferred income level",
    "reasoning": "reasoning process"
}}"""

        try:
            result = model.predict_string(prompt)
            return {
                "guess": result,
                "success": len(result) > 50  # 简单判断：有实质性推断
            }
        except Exception as e:
            return {"guess": "", "success": False}

    def evaluate_anonymization(self, model, original_text: str, anonymized_text: str, attack_guess: str) -> Dict[str, float]:
        """评估匿名化效果"""
        prompt = f"""Please evaluate the following anonymization effect:

Original text: {original_text}
Anonymized text: {anonymized_text}
Attack inference: {attack_guess[:500] if attack_guess else 'None'}

Please score on two aspects (0-1, keep one decimal place):

1. Privacy protection score (privacy_score): Whether personal information is effectively protected, making it difficult for attackers to infer original information
2. Text utility score (utility_score): Whether the anonymized text maintains the original semantics and fluency

Please answer in the following format:
Privacy score: [score between 0-1, e.g., 0.7]
Utility score: [score between 0-1, e.g., 0.9]"""

        try:
            result = model.predict_string(prompt)

            privacy_score = 0.5
            utility_score = 0.5

            for line in result.split('\n'):
                if 'Privacy' in line or 'privacy' in line.lower():
                    try:
                        score_str = ''.join(c for c in line if c.isdigit() or c == '.')
                        if score_str:
                            privacy_score = min(1.0, max(0.0, float(score_str)))
                    except:
                        pass
                if 'Utility' in line or 'utility' in line.lower():
                    try:
                        score_str = ''.join(c for c in line if c.isdigit() or c == '.')
                        if score_str:
                            utility_score = min(1.0, max(0.0, float(score_str)))
                    except:
                        pass

            return {
                "privacy_score": privacy_score,
                "utility_score": utility_score,
                "evaluation": result
            }
        except Exception as e:
            return {"privacy_score": 0.5, "utility_score": 0.5, "evaluation": str(e)}

    def evaluate_quality(self, original_text: str, anonymized_text: str) -> Dict[str, Any]:
        """详细质量评估"""
        try:
            scores = self.quality_evaluator.evaluate_quality(original_text, anonymized_text)
            return {
                "readability_score": scores.readability_score,
                "readability_explanation": scores.readability_explanation,
                "meaning_score": scores.meaning_score,
                "meaning_explanation": scores.meaning_explanation,
                "hallucination_score": scores.hallucination_score,
                "hallucination_explanation": scores.hallucination_explanation,
                "bleu": scores.bleu,
                "rouge1": scores.rouge1,
                "rougeL": scores.rougeL,
                "utility_score": scores.get_utility_score()
            }
        except Exception as e:
            print(f"    ⚠ Quality evaluation failed: {e}")
            return None

    def evaluate_sample(self, sample: Dict) -> Dict:
        """评估单个样本"""
        username = sample.get("username", "unknown")
        original_text = sample.get("original_text", "")
        rounds = sample.get("rounds", [])

        if not original_text or len(original_text) < 20:
            return None

        # 创建攻击者和评估者模型（与异构实验一致）
        attacker = self.registry.create_model_instance(
            self.attacker_name, temperature=0.2
        )
        evaluator = self.registry.create_model_instance(
            self.evaluator_name, temperature=0.0
        )

        if not all([attacker, evaluator]):
            print(f"✗ Model creation failed, skip sample {username}")
            return None

        sample_result = {
            "username": username,
            "config_name": "homogeneous_deepseek",
            "original_text": original_text[:200],
            "rounds": []
        }

        # 只评估前3轮（与异构实验一致）
        for round_data in rounds[:self.max_rounds]:
            round_num = round_data['round']
            anonymized_text = round_data['anonymized_text']

            round_start = time.time()

            # 攻击
            attack_result = self.attack_text(attacker, anonymized_text)

            # 基础评估
            evaluation = self.evaluate_anonymization(
                evaluator, original_text, anonymized_text, attack_result["guess"]
            )

            round_result = {
                "round": round_num,
                "anonymized_text": anonymized_text[:200],
                "privacy_score": evaluation["privacy_score"],
                "utility_score": evaluation["utility_score"],
                "attack_success": attack_result["success"],
                "elapsed_time": time.time() - round_start
            }

            # 最后一轮进行质量评估
            if round_num == self.max_rounds or round_num == len(rounds):
                print(f"    📊 Quality evaluation...")
                quality_scores = self.evaluate_quality(original_text, anonymized_text)
                if quality_scores:
                    round_result["quality_scores"] = quality_scores

            sample_result["rounds"].append(round_result)

            print(f"     Privacy: {evaluation['privacy_score']:.2f} | Utility: {evaluation['utility_score']:.2f}")

            # 检查是否达到目标
            if (evaluation["privacy_score"] >= self.target_privacy and
                evaluation["utility_score"] >= self.min_utility):
                print(f"  ✓ Target reached")
                break

            if evaluation["utility_score"] < 0.3:
                print(f"  ⚠ Utility too low")
                break

        # 设置最终分数
        if sample_result["rounds"]:
            final_round = sample_result["rounds"][-1]
            sample_result["final_privacy"] = final_round["privacy_score"]
            sample_result["final_utility"] = final_round["utility_score"]
            sample_result["total_rounds"] = len(sample_result["rounds"])
            sample_result["total_time"] = sum(r["elapsed_time"] for r in sample_result["rounds"])

            if "quality_scores" in final_round:
                sample_result["quality_scores"] = final_round["quality_scores"]

        return sample_result

    def run_evaluation(self, input_file: str, output_file: str, max_samples: int = None):
        """运行完整评估"""
        print("=" * 80)
        print("HOMOGENEOUS DEEPSEEK ADVERSARIAL EVALUATION")
        print("=" * 80)

        # 读取提取的数据
        print(f"\n📂 Loading data: {input_file}")
        with open(input_file, 'r') as f:
            data = json.load(f)

        samples = data["samples"]
        if max_samples:
            samples = samples[:max_samples]

        print(f"✓ Loaded {len(samples)} samples")

        # 评估结果
        results = {
            "start_time": datetime.now().isoformat(),
            "config": {
                "model_config": {
                    "name": "homogeneous_deepseek",
                    "defender": "deepseek-chat",
                    "attacker": "deepseek-reasoner",
                    "evaluator": "qwen-max",
                    "quality_evaluator": "deepseek-chat"
                },
                "max_rounds": self.max_rounds,
                "target_privacy": self.target_privacy,
                "min_utility": self.min_utility,
                "enable_quality_evaluation": True
            },
            "samples": [],
            "statistics": {
                "total_samples": len(samples),
                "processed_samples": 0,
                "successful_anonymizations": 0,
                "avg_privacy_score": 0.0,
                "avg_utility_score": 0.0,
                "avg_quality_utility": 0.0,
                "config_success_rates": {}
            }
        }

        start_time = time.time()

        # 处理每个样本
        for i, sample in enumerate(samples):
            print(f"\n📝 Processing sample [{i+1}/{len(samples)}]: {sample.get('username', 'unknown')}")

            try:
                result = self.evaluate_sample(sample)
                if result:
                    results["samples"].append(result)
                    results["statistics"]["processed_samples"] += 1

                    # 定期保存
                    if (i + 1) % 10 == 0:
                        self._save_checkpoint(results, output_file)
                        self._update_statistics(results)

            except Exception as e:
                print(f"✗ Error processing sample {i+1}: {e}")
                continue

        # 最终更新统计并保存
        self._update_statistics(results)
        results["elapsed_time"] = time.time() - start_time
        self._save_checkpoint(results, output_file)

        self._print_summary(results)

    def _save_checkpoint(self, results: Dict, output_file: str):
        """保存检查点"""
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"💾 Checkpoint saved: {output_file}")

    def _update_statistics(self, results: Dict):
        """更新统计数据"""
        if not results["samples"]:
            return

        processed = len(results["samples"])

        privacy_scores = [s.get("final_privacy", 0) for s in results["samples"]]
        utility_scores = [s.get("final_utility", 0) for s in results["samples"]]

        results["statistics"]["processed_samples"] = processed
        results["statistics"]["avg_privacy_score"] = (
            sum(privacy_scores) / len(privacy_scores) if privacy_scores else 0
        )
        results["statistics"]["avg_utility_score"] = (
            sum(utility_scores) / len(utility_scores) if utility_scores else 0
        )

        # 质量评估统计
        quality_samples = [s for s in results["samples"] if s.get("quality_scores")]
        if quality_samples:
            quality_utilities = [
                s["quality_scores"].get("utility_score", 0) for s in quality_samples
            ]
            results["statistics"]["avg_quality_utility"] = sum(quality_utilities) / len(quality_utilities)

        # 成功率统计
        success = sum(1 for s in results["samples"]
                     if s.get("final_privacy", 0) >= self.target_privacy)
        total = len(results["samples"])
        results["statistics"]["config_success_rates"] = {
            "homogeneous_deepseek": f"{success}/{total} ({success/total*100:.1f}%)"
        }

    def _print_summary(self, results: Dict):
        """打印摘要"""
        stats = results["statistics"]

        print("\n" + "=" * 80)
        print("📊 EVALUATION SUMMARY")
        print("=" * 80)

        print(f"\nProcessed samples: {stats['processed_samples']}/{stats['total_samples']}")
        print(f"Avg privacy score: {stats['avg_privacy_score']:.3f}")
        print(f"Avg utility score: {stats['avg_utility_score']:.3f}")

        if stats.get('avg_quality_utility', 0) > 0:
            print(f"Avg quality utility: {stats['avg_quality_utility']:.3f}")

        print(f"\nSuccess rate: {stats['config_success_rates']}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    evaluator = HomogeneousEvaluator()

    input_file = "homogeneous_results/extracted_samples.json"
    output_file = "homogeneous_results/evaluated_results.json"

    # 可以设置max_samples来限制评估样本数（用于测试）
    evaluator.run_evaluation(input_file, output_file, max_samples=None)
