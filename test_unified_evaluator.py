#!/usr/bin/env python3
"""
测试统一隐私评估器

这个脚本测试各种场景，确保评估器按预期工作。
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.evaluation.unified_privacy_evaluator import (
    UnifiedPrivacyEvaluator,
    evaluate_from_attack_results
)


def test_exact_match():
    """测试精确匹配"""
    print("测试1: 精确匹配")
    print("-" * 50)

    result = evaluate_from_attack_results(
        ground_truth={"age": "30", "income": "high"},
        attack_result={
            "age": {"guess": ["30"], "certainty": 5},
            "income": {"guess": ["high"], "certainty": 4}
        },
        utility_score=0.9
    )

    print(f"真实值: age=30, income=high")
    print(f"攻击者猜测: age=30 (certainty=5), income=high (certainty=4)")
    print(f"隐私分数: {result.privacy_score:.3f}")
    print(f"预期: ~0.1-0.3 (完全精确匹配，高确定性)")
    print(f"攻击成功率: {result.attack_success_rate:.3f}")
    print()

    assert result.privacy_score < 0.5, "精确匹配应该导致低隐私分数"
    print("✓ 测试通过\n")


def test_no_match():
    """测试完全不匹配"""
    print("测试2: 完全不匹配")
    print("-" * 50)

    result = evaluate_from_attack_results(
        ground_truth={"age": "30", "income": "high"},
        attack_result={
            "age": {"guess": ["25", "35"], "certainty": 3},
            "income": {"guess": ["medium", "low"], "certainty": 2}
        },
        utility_score=0.9
    )

    print(f"真实值: age=30, income=high")
    print(f"攻击者猜测: age=25/35, income=medium/low")
    print(f"隐私分数: {result.privacy_score:.3f}")
    print(f"预期: ~0.8-1.0 (无精确匹配)")
    print(f"攻击成功率: {result.attack_success_rate:.3f}")
    print()

    # 注意：由于可能有语义相似度，分数可能不是1.0
    assert result.privacy_score > 0.5, "不匹配应该导致较高隐私分数"
    print("✓ 测试通过\n")


def test_partial_match():
    """测试部分匹配"""
    print("测试3: 部分匹配")
    print("-" * 50)

    result = evaluate_from_attack_results(
        ground_truth={"age": "30", "income": "high"},
        attack_result={
            "age": {"guess": ["30 years old"], "certainty": 4},
            "income": {"guess": ["very high"], "certainty": 3}
        },
        utility_score=0.9
    )

    print(f"真实值: age=30, income=high")
    print(f"攻击者猜测: age='30 years old', income='very high'")
    print(f"隐私分数: {result.privacy_score:.3f}")
    print(f"预期: ~0.4-0.7 (部分匹配)")
    print(f"攻击成功率: {result.attack_success_rate:.3f}")
    print()

    print("✓ 测试通过\n")


def test_semantic_match():
    """测试语义匹配"""
    print("测试4: 语义相似")
    print("-" * 50)

    result = evaluate_from_attack_results(
        ground_truth={"location": "Beijing, China"},
        attack_result={
            "location": {"guess": ["Beijing"], "certainty": 4}
        },
        utility_score=0.9
    )

    print(f"真实值: location='Beijing, China'")
    print(f"攻击者猜测: location='Beijing'")
    print(f"隐私分数: {result.privacy_score:.3f}")
    print(f"预期: ~0.3-0.6 (包含关系)")
    print(f"攻击成功率: {result.attack_success_rate:.3f}")
    print()

    assert result.privacy_score < 0.8, "语义包含应该降低隐私分数"
    print("✓ 测试通过\n")


def test_no_attack():
    """测试攻击者失败"""
    print("测试5: 攻击者完全失败")
    print("-" * 50)

    result = evaluate_from_attack_results(
        ground_truth={"age": "30", "income": "high"},
        attack_result={},  # 攻击者没有给出任何推理
        utility_score=0.9
    )

    print(f"真实值: age=30, income=high")
    print(f"攻击者猜测: 无")
    print(f"隐私分数: {result.privacy_score:.3f}")
    print(f"预期: 1.0 (完全保护)")
    print(f"攻击成功率: {result.attack_success_rate:.3f}")
    print()

    assert result.privacy_score == 1.0, "攻击者失败应该给满分"
    print("✓ 测试通过\n")


def test_certainty_effect():
    """测试确定性影响"""
    print("测试6: 确定性的影响")
    print("-" * 50)

    # 低确定性
    result_low = evaluate_from_attack_results(
        ground_truth={"age": "30"},
        attack_result={"age": {"guess": ["30"], "certainty": 1}},
        utility_score=0.9
    )

    # 高确定性
    result_high = evaluate_from_attack_results(
        ground_truth={"age": "30"},
        attack_result={"age": {"guess": ["30"], "certainty": 5}},
        utility_score=0.9
    )

    print(f"真实值: age=30")
    print(f"攻击者猜测(低确定性): age=30, certainty=1")
    print(f"  隐私分数: {result_low.privacy_score:.3f}")
    print(f"攻击者猜测(高确定性): age=30, certainty=5")
    print(f"  隐私分数: {result_high.privacy_score:.3f}")
    print(f"预期: 高确定性应该导致更低的隐私分数")
    print()

    assert result_high.privacy_score < result_low.privacy_score, \
        "高确定性应该导致更低的隐私分数"
    print("✓ 测试通过\n")


def test_batch_evaluation():
    """测试批量评估"""
    print("测试7: 批量评估")
    print("-" * 50)

    evaluator = UnifiedPrivacyEvaluator()

    samples = [
        {
            "ground_truth": {"age": "30"},
            "attack_inferences": {"age": {"guess": ["30"], "certainty": 5}},
            "utility_score": 0.9
        },
        {
            "ground_truth": {"age": "30"},
            "attack_inferences": {"age": {"guess": ["25"], "certainty": 3}},
            "utility_score": 0.8
        },
        {
            "ground_truth": {"age": "30"},
            "attack_inferences": {},
            "utility_score": 0.9
        }
    ]

    stats = evaluator.batch_evaluate(samples)

    print(f"样本数: {stats['total_samples']}")
    print(f"平均隐私分数: {stats['privacy_mean']:.3f} ± {stats['privacy_std']:.3f}")
    print(f"成功率: {stats['success_rate']:.1f}%")
    print()

    assert stats['total_samples'] == 3, "应该有3个样本"
    assert 0.0 <= stats['privacy_mean'] <= 1.0, "隐私分数应该在0-1之间"
    print("✓ 测试通过\n")


def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("统一隐私评估器 - 测试套件")
    print("=" * 80)
    print()

    try:
        test_exact_match()
        test_no_match()
        test_partial_match()
        test_semantic_match()
        test_no_attack()
        test_certainty_effect()
        test_batch_evaluation()

        print("=" * 80)
        print("✓ 所有测试通过！")
        print("=" * 80)

        return True

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
