#!/usr/bin/env python3
"""
从日志文件中提取评估结果并生成统计报告
"""

import re
import numpy as np

log_file = "/home/rooter/llm-anonymization/homogeneous_evaluation_full.log"

privacy_scores = []
utility_scores = []
success_count = 0
total_count = 0

# 从日志中提取评估结果
with open(log_file, 'r') as f:
    for line in f:
        # 查找包含隐私和效用分数的行
        if "隐私:" in line and "效用:" in line:
            # 提取隐私分数
            privacy_match = re.search(r'隐私:\s*([\d.]+)', line)
            # 提取效用分数
            utility_match = re.search(r'效用:\s*([\d.]+)', line)
            # 提取成功状态
            success_match = re.search(r'成功:\s*(\w+)', line)

            if privacy_match and utility_match:
                privacy = float(privacy_match.group(1))
                utility = float(utility_match.group(1))

                # 只统计有效的评估结果（效用 > 0）
                if utility > 0:
                    privacy_scores.append(privacy)
                    utility_scores.append(utility)
                    if success_match:
                        if success_match.group(1) == 'True':
                            success_count += 1
                    total_count += 1

print("=" * 80)
print("同构DeepSeek大规模评估结果统计（从日志提取）")
print("=" * 80)
print(f"\n有效评估样本数: {total_count}")
print(f"成功样本数: {success_count}")
print(f"成功率: {success_count/total_count*100:.1f}%")

print(f"\n隐私分数:")
print(f"  平均: {np.mean(privacy_scores):.3f}")
print(f"  标准差: {np.std(privacy_scores):.3f}")
print(f"  最小值: {np.min(privacy_scores):.3f}")
print(f"  最大值: {np.max(privacy_scores):.3f}")

print(f"\n效用分数:")
print(f"  平均: {np.mean(utility_scores):.3f}")
print(f"  标准差: {np.std(utility_scores):.3f}")
print(f"  最小值: {np.min(utility_scores):.3f}")
print(f"  最大值: {np.max(utility_scores):.3f}")

print(f"\n隐私达标率 (≥0.8): {sum(1 for p in privacy_scores if p >= 0.8) / len(privacy_scores) * 100:.1f}%")
print(f"效用达标率 (≥0.6): {sum(1 for u in utility_scores if u >= 0.6) / len(utility_scores) * 100:.1f}%")

print("\n" + "=" * 80)

# 保存统计结果
import json
stats = {
    "total_samples": total_count,
    "successful_samples": success_count,
    "success_rate": success_count/total_count*100,
    "privacy": {
        "mean": float(np.mean(privacy_scores)),
        "std": float(np.std(privacy_scores)),
        "min": float(np.min(privacy_scores)),
        "max": float(np.max(privacy_scores)),
        "target_achievement_rate": sum(1 for p in privacy_scores if p >= 0.8) / len(privacy_scores) * 100
    },
    "utility": {
        "mean": float(np.mean(utility_scores)),
        "std": float(np.std(utility_scores)),
        "min": float(np.min(utility_scores)),
        "max": float(np.max(utility_scores)),
        "target_achievement_rate": sum(1 for u in utility_scores if u >= 0.6) / len(utility_scores) * 100
    }
}

with open("homogeneous_results_qwen_263/final_statistics.json", 'w') as f:
    json.dump(stats, f, indent=2)

print("✓ 统计结果已保存至: homogeneous_results_qwen_263/final_statistics.json")
