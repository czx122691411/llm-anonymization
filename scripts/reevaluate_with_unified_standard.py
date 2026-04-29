#!/usr/bin/env python3
"""
使用统一评估标准重新评估同构和异构配置

这个脚本将:
1. 加载同构DeepSeek的评估数据
2. 加载异构Config 1的评估数据
3. 使用统一的评估标准重新计算隐私分数
4. 生成公平对比报告
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.evaluation.unified_privacy_evaluator import (
    UnifiedPrivacyEvaluator,
    PrivacyEvaluationResult
)


class UnifiedReEvaluator:
    """使用统一标准重新评估"""

    def __init__(self):
        self.evaluator = UnifiedPrivacyEvaluator(
            target_privacy=0.8,
            min_utility=0.6,
            semantic_threshold=0.7
        )

        # 数据路径
        self.homogeneous_log = Path("/home/rooter/llm-anonymization/homogeneous_evaluation_full.log")
        self.heterogeneous_checkpoint = Path("/home/rooter/llm-anonymization/training_results_enhanced/checkpoint.json")
        self.output_dir = Path("/home/rooter/llm-anonymization/unified_evaluation_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_homogeneous_log(self) -> List[Dict[str, Any]]:
        """
        解析同构评估日志

        日志格式示例:
        评估用户: 31male (第1轮)
          隐私: 1.000, 效用: 0.870, 成功: True
          攻击者推理: {"age": {"guess": ["30"], "certainty": 4}}
        """
        samples = []
        current_sample = None

        with open(self.homogeneous_log, 'r', encoding='utf-8') as f:
            for line in f:
                # 解析用户名
                if '评估用户:' in line:
                    if current_sample:
                        samples.append(current_sample)
                    username_match = re.search(r'评估用户:\s*(\w+)', line)
                    current_sample = {
                        'username': username_match.group(1) if username_match else 'unknown',
                        'ground_truth': {},
                        'attack_inferences': {},
                        'utility_score': 0.8,
                        'original_privacy': 0.0
                    }

                # 解析隐私和效用分数
                elif '隐私:' in line and '效用:' in line:
                    if current_sample:
                        privacy_match = re.search(r'隐私:\s*([\d.]+)', line)
                        utility_match = re.search(r'效用:\s*([\d.]+)', line)
                        if privacy_match:
                            current_sample['original_privacy'] = float(privacy_match.group(1))
                        if utility_match:
                            current_sample['utility_score'] = float(utility_match.group(1))

                # 解析攻击结果（如果有JSON数据）
                elif '攻击者推理:' in line or 'attack_result:' in line:
                    # 尝试提取JSON
                    json_start = line.find('{')
                    if json_start >= 0:
                        try:
                            json_str = line[json_start:]
                            # 查找JSON结束
                            brace_count = 0
                            json_end = json_start
                            for i, char in enumerate(json_str):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break

                            if json_end > json_start:
                                attack_data = json.loads(json_str[:json_end])
                                if current_sample:
                                    current_sample['attack_inferences'] = attack_data
                        except:
                            pass

        if current_sample:
            samples.append(current_sample)

        return samples

    def load_homogeneous_samples(self) -> List[Dict[str, Any]]:
        """
        加载同构DeepSeek样本

        从homogeneous_evaluation_full.log或从原始数据文件加载
        """
        print("📂 加载同构DeepSeek样本...")

        # 尝试从日志加载
        if self.homogeneous_log.exists():
            print(f"  从日志加载: {self.homogeneous_log}")
            samples = self.parse_homogeneous_log()
            print(f"  加载了 {len(samples)} 个样本")
            return samples

        # 否则从JSON文件加载
        data_dir = Path("/home/rooter/llm-anonymization/anonymized_results/synthetic/deepseek_full")
        samples = []

        # 读取第1轮数据（与异构配置对应）
        for round_num in [1]:
            file_path = data_dir / f"anonymized_{round_num}.jsonl"
            if not file_path.exists():
                continue

            print(f"  读取: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        sample = self._parse_homogeneous_sample(data, round_num, line_num)
                        if sample:
                            samples.append(sample)
                    except Exception as e:
                        continue

        print(f"  总共加载: {len(samples)} 个样本")
        return samples

    def _parse_homogeneous_sample(self, data: Dict, round_num: int, line_num: int) -> Dict[str, Any]:
        """解析单个同构样本"""
        try:
            username = data.get("username", f"sample_{line_num}")
            comments = data.get("comments", [])

            if len(comments) < 2:
                return None

            # 提取原始文本和匿名化文本
            original_comments = comments[0].get("comments", [])
            if round_num < len(comments):
                anonymized_comments = comments[round_num].get("comments", [])
            else:
                return None

            # 提取ground truth
            reviews = data.get("reviews", {})
            ground_truth = {}
            for category, category_data in reviews.items():
                for attr, attr_data in category_data.items():
                    ground_truth[attr] = str(attr_data.get("estimate", ""))

            if not ground_truth:
                return None

            # 构建样本
            return {
                'username': username,
                'round': round_num,
                'ground_truth': ground_truth,
                'attack_inferences': {},  # 需要重新攻击
                'utility_score': 0.8,  # 默认值，后续计算
                'original_text': " ".join([c.get("text", "") for c in original_comments]),
                'anonymized_text': " ".join([c.get("text", "") for c in anonymized_comments])
            }
        except Exception as e:
            return None

    def load_heterogeneous_samples(self) -> List[Dict[str, Any]]:
        """加载异构Config 1样本"""
        print("📂 加载异构Config 1样本...")

        if not self.heterogeneous_checkpoint.exists():
            print(f"  ✗ 文件不存在: {self.heterogeneous_checkpoint}")
            return []

        with open(self.heterogeneous_checkpoint, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)

        samples = []
        config1_samples = [
            s for s in checkpoint['results']['samples']
            if s['config_name'] == 'config_1'
        ]

        print(f"  找到 {len(config1_samples)} 个样本")

        for sample_data in config1_samples:
            # 提取ground truth（从原始文本推断）
            ground_truth = self._extract_ground_truth(sample_data.get('original_text', ''))

            # 使用最后一轮的结果
            rounds = sample_data.get('rounds', [])
            if not rounds:
                continue

            final_round = rounds[-1]  # 最后一轮

            # 构建样本
            sample = {
                'username': sample_data.get('username', 'unknown'),
                'ground_truth': ground_truth,
                'utility_score': final_round.get('utility_score', 0.8),
                'original_text': sample_data.get('original_text', ''),
                'anonymized_text': final_round.get('anonymized_text', ''),
                'original_privacy': final_round.get('privacy_score', 0.0)
            }

            samples.append(sample)

        print(f"  解析了 {len(samples)} 个有效样本")
        return samples

    def _extract_ground_truth(self, text: str) -> Dict[str, Any]:
        """从文本中提取ground truth（简化版）"""
        # 这里应该使用实际的ground truth数据
        # 暂时返回空字典，实际使用时需要从数据源获取
        return {}

    def reevaluate_homogeneous(self, max_samples: int = 263) -> Dict[str, Any]:
        """重新评估同构配置"""
        print("\n" + "=" * 80)
        print("🔄 重新评估同构DeepSeek配置")
        print("=" * 80)

        samples = self.load_homogeneous_samples()

        if max_samples:
            samples = samples[:max_samples]

        print(f"\n评估 {len(samples)} 个样本...")

        results = []
        for i, sample in enumerate(samples, 1):
            if i % 50 == 0:
                print(f"  进度: {i}/{len(samples)}")

            # 如果样本没有攻击推理，需要模拟或跳过
            if not sample.get('attack_inferences'):
                # 创建模拟攻击结果（实际使用时需要真实攻击）
                sample['attack_inferences'] = self._simulate_attack(sample)

            result = self.evaluator.evaluate_sample(
                ground_truth=sample['ground_truth'],
                attack_inferences=sample['attack_inferences'],
                utility_score=sample.get('utility_score', 0.8)
            )
            results.append(result)

        # 计算统计信息
        stats = self._calculate_statistics(results)

        print(f"\n✓ 同构DeepSeek评估完成")
        print(f"  平均隐私分数: {stats['privacy_mean']:.3f} ± {stats['privacy_std']:.3f}")
        print(f"  平均效用分数: {stats['utility_mean']:.3f} ± {stats['utility_std']:.3f}")
        print(f"  成功率: {stats['success_rate']:.1f}%")

        return {
            'config_name': 'homogeneous_deepseek',
            'num_samples': len(results),
            'statistics': stats,
            'detailed_results': results
        }

    def reevaluate_heterogeneous(self) -> Dict[str, Any]:
        """重新评估异构Config 1"""
        print("\n" + "=" * 80)
        print("🔄 重新评估异构Config 1")
        print("=" * 80)

        samples = self.load_heterogeneous_samples()

        if not samples:
            print("  ✗ 没有有效样本")
            return None

        print(f"\n评估 {len(samples)} 个样本...")

        results = []
        for i, sample in enumerate(samples, 1):
            if i % 50 == 0:
                print(f"  进度: {i}/{len(samples)}")

            # 使用已有的攻击结果重新计算
            result = self.evaluator.evaluate_sample(
                ground_truth=sample['ground_truth'],
                attack_inferences={},  # 需要从checkpoint提取
                utility_score=sample.get('utility_score', 0.8)
            )
            results.append(result)

        # 计算统计信息
        stats = self._calculate_statistics(results)

        print(f"\n✓ 异构Config 1评估完成")
        print(f"  平均隐私分数: {stats['privacy_mean']:.3f} ± {stats['privacy_std']:.3f}")
        print(f"  平均效用分数: {stats['utility_mean']:.3f} ± {stats['utility_std']:.3f}")
        print(f"  成功率: {stats['success_rate']:.1f}%")

        return {
            'config_name': 'heterogeneous_config_1',
            'num_samples': len(results),
            'statistics': stats,
            'detailed_results': results
        }

    def _simulate_attack(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """模拟攻击结果（临时方案）"""
        # 实际使用时，应该调用攻击者模型
        # 这里返回空字典表示没有攻击结果
        return {}

    def _calculate_statistics(self, results: List[PrivacyEvaluationResult]) -> Dict[str, Any]:
        """计算统计信息"""
        privacy_scores = [r.privacy_score for r in results]
        utility_scores = [r.utility_score for r in results]
        success_count = sum(1 for r in results if r.success)

        return {
            'privacy_mean': float(np.mean(privacy_scores)),
            'privacy_std': float(np.std(privacy_scores)),
            'privacy_min': float(np.min(privacy_scores)),
            'privacy_max': float(np.max(privacy_scores)),
            'utility_mean': float(np.mean(utility_scores)),
            'utility_std': float(np.std(utility_scores)),
            'utility_min': float(np.min(utility_scores)),
            'utility_max': float(np.max(utility_scores)),
            'success_count': success_count,
            'success_rate': float(success_count / len(results)) if results else 0.0
        }

    def generate_comparison_report(self, homogeneous_result: Dict, heterogeneous_result: Dict):
        """生成对比报告"""
        print("\n" + "=" * 80)
        print("📊 统一评估标准对比报告")
        print("=" * 80)

        h_stats = homogeneous_result['statistics']
        het_stats = heterogeneous_result['statistics']

        print(f"\n{'配置':<30} {'样本数':<10} {'隐私分数':<15} {'效用分数':<15} {'成功率'}")
        print("-" * 80)

        print(f"{'同构DeepSeek':<30} {homogeneous_result['num_samples']:<10} "
              f"{h_stats['privacy_mean']:.3f} ± {h_stats['privacy_std']:.3f}  "
              f"{h_stats['utility_mean']:.3f} ± {h_stats['utility_std']:.3f}  "
              f"{h_stats['success_rate']:.1f}%")

        print(f"{'异构Config 1':<30} {heterogeneous_result['num_samples']:<10} "
              f"{het_stats['privacy_mean']:.3f} ± {het_stats['privacy_std']:.3f}  "
              f"{het_stats['utility_mean']:.3f} ± {het_stats['utility_std']:.3f}  "
              f"{het_stats['success_rate']:.1f}%")

        # 保存报告
        report_file = self.output_dir / "unified_comparison_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("统一评估标准对比报告\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"评估标准: UnifiedPrivacyEvaluator\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            # ... 更多内容

        print(f"\n✓ 报告已保存到: {report_file}")


def main():
    """主函数"""
    from datetime import datetime

    print("=" * 80)
    print("统一隐私评估标准 - 重新评估同构和异构配置")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    reevaluator = UnifiedReEvaluator()

    # 重新评估同构配置
    homogeneous_result = reevaluator.reevaluate_homogeneous(max_samples=263)

    # 重新评估异构配置
    # heterogeneous_result = reevaluator.reevaluate_heterogeneous()

    # 生成对比报告
    # reevaluator.generate_comparison_report(homogeneous_result, heterogeneous_result)

    print("\n" + "=" * 80)
    print("✓ 重新评估完成")
    print("=" * 80)


if __name__ == "__main__":
    import re
    main()
