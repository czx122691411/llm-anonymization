"""
测试脚本：详细质量评估器
Test script for Detailed Quality Evaluator

这个脚本测试质量评估器的各项功能：
1. 基础质量评分
2. LLM评分解析
3. BLEU/ROUGE计算
4. 与异构模型集成
"""

import os
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置API密钥
os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY", "sk-e68f64387d7c40fa86002e8bb861456e")
os.environ["DEEPSEEK_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "sk-30d59ec09f5c495db4271f9c321938cb")

from src.models.providers.registry import get_registry
from src.evaluation import QualityEvaluator


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def test_basic_evaluation():
    """测试基础质量评估功能"""
    print_section("测试 1: 基础质量评估")

    # 创建模型
    registry = get_registry(region="china")
    model = registry.create_model_instance("deepseek-chat", temperature=0.0)

    # 创建评估器
    evaluator = QualityEvaluator(model)

    # 测试用例
    original = (
        "hahaha mate, joins the club! 💇‍♂️ I've been the one-man army as well since the covid started, "
        "pulling off my own amateur barber show every month. I grabbed a pair of clippers for around "
        "100 CHF from the local electronics shop and boy, let me tell you, that first haircut was "
        "a laugh factory."
    )

    anonymized = (
        "hahaha mate, joins the club! 💇‍♂️ I've been the one-man army as well since the pandemic started, "
        "pulling off my own amateur barber show every month. I grabbed a pair of clippers from a nearby "
        "store and boy, let me tell you, that first haircut was a laugh factory."
    )

    print("原始文本:")
    print(f"  {original[:150]}...")
    print("\n匿名化文本:")
    print(f"  {anonymized[:150]}...")

    print("\n开始评估...")
    scores = evaluator.evaluate_quality(original, anonymized)

    print("\n📊 评估结果:")
    print(f"  可读性: {scores.readability_score:.1f}/10")
    print(f"    解释: {scores.readability_explanation[:100]}...")
    print(f"\n  含义保留: {scores.meaning_score:.1f}/10")
    print(f"    解释: {scores.meaning_explanation[:100]}...")
    print(f"\n  无幻觉: {scores.hallucination_score:.1f}/1.0")
    print(f"    解释: {scores.hallucination_explanation[:100]}...")
    print(f"\n  BLEU: {scores.bleu:.4f}")
    print(f"  ROUGE-1: {scores.rouge1:.4f}")
    print(f"  ROUGE-L: {scores.rougeL:.4f}")
    print(f"\n  综合效用: {scores.get_utility_score():.3f}")

    return scores


def test_multiple_anonymization_levels():
    """测试不同匿名化水平的效果"""
    print_section("测试 2: 不同匿名化水平对比")

    registry = get_registry(region="china")
    model = registry.create_model_instance("deepseek-chat", temperature=0.0)
    evaluator = QualityEvaluator(model)

    original = "I live in Zurich, Switzerland and work as a software engineer earning 150k CHF annually."

    anonymization_levels = [
        ("原始", original),
        ("轻度匿名化", "I live in a city in Switzerland and work as a software engineer."),
        ("中度匿名化", "I live in Switzerland and work in the tech industry."),
        ("重度匿名化", "I live in Europe and have a professional job."),
    ]

    print(f"原始文本: {original}\n")

    results = []
    for level, text in anonymization_levels:
        print(f"【{level}】")
        print(f"  {text}")

        if level != "原始":
            scores = evaluator.evaluate_quality(original, text)
            results.append((level, scores))
            print(f"  → 可读性: {scores.readability_score:.1f}, "
                  f"含义: {scores.meaning_score:.1f}, "
                  f"BLEU: {scores.bleu:.4f}, "
                  f"效用: {scores.get_utility_score():.3f}")
        print()

    # 对比表
    print("📊 对比总结:")
    print(f"{'水平':<15} {'可读性':<8} {'含义':<8} {'BLEU':<8} {'效用':<8}")
    print("-" * 50)
    for level, scores in results:
        print(f"{level:<15} {scores.readability_score:<8.1f} {scores.meaning_score:<8.1f} "
              f"{scores.bleu:<8.4f} {scores.get_utility_score():<8.3f}")


def test_json_parsing():
    """测试JSON解析功能"""
    print_section("测试 3: JSON 解析功能")

    registry = get_registry(region="china")
    model = registry.create_model_instance("deepseek-chat", temperature=0.0)
    evaluator = QualityEvaluator(model)

    # 测试不同格式的响应
    test_responses = [
        """{
    "readability": {
        "explanation": "Text is clear",
        "score": 9
    },
    "meaning": {
        "explanation": "Meaning preserved",
        "score": 8
    },
    "hallucinations": {
        "explanation": "No new info",
        "score": 1
    }
}""",
        """Here's my evaluation:
```json
{
    "readability": {"score": 8, "explanation": "Good"},
    "meaning": {"score": 9, "explanation": "Excellent"},
    "hallucinations": {"score": 1, "explanation": "Clean"}
}
```""",
    ]

    for i, response in enumerate(test_responses, 1):
        print(f"测试响应 {i}:")
        print(f"  {response[:100]}...")
        parsed = evaluator._parse_quality_response(response)
        print(f"  → 可读性: {parsed['readability_score']}, "
              f"含义: {parsed['meaning_score']}, "
              f"幻觉: {parsed['hallucination_score']}")
        print()


def test_error_handling():
    """测试错误处理"""
    print_section("测试 4: 错误处理")

    registry = get_registry(region="china")
    model = registry.create_model_instance("deepseek-chat", temperature=0.0)
    evaluator = QualityEvaluator(model)

    # 测试空文本
    print("测试空文本:")
    try:
        scores = evaluator.evaluate_quality("", "")
        print(f"  → 成功处理，返回默认分数")
    except Exception as e:
        print(f"  → 捕获异常: {e}")

    # 测试非常长的文本
    print("\n测试超长文本:")
    long_text = "This is a test. " * 1000
    try:
        scores = evaluator.evaluate_quality(long_text, long_text)
        print(f"  → 成功处理，可读性: {scores.readability_score:.1f}")
    except Exception as e:
        print(f"  → 捕获异常: {e}")


def test_heterogeneous_integration():
    """测试与异构模型的集成"""
    print_section("测试 5: 异构模型集成")

    registry = get_registry(region="china")

    # 测试不同的质量评估模型
    models_to_test = [
        ("deepseek-chat", 0.0),
        ("qwen-plus", 0.0),
        ("qwen-max", 0.0),
    ]

    original = "I earn 150k USD working as a software engineer in San Francisco."
    anonymized = "I earn a high salary working in the tech industry."

    print(f"原始: {original}")
    print(f"匿名化: {anonymized}\n")

    print(f"{'模型':<20} {'可读性':<8} {'含义':<8} {'效用':<8}")
    print("-" * 50)

    for model_name, temp in models_to_test:
        try:
            model = registry.create_model_instance(model_name, temperature=temp)
            evaluator = QualityEvaluator(model)
            scores = evaluator.evaluate_quality(original, anonymized)

            print(f"{model_name:<20} {scores.readability_score:<8.1f} "
                  f"{scores.meaning_score:<8.1f} {scores.get_utility_score():<8.3f}")
        except Exception as e:
            print(f"{model_name:<20} 失败: {str(e)[:40]}")


def test_batch_evaluation():
    """测试批量评估"""
    print_section("测试 6: 批量评估性能")

    registry = get_registry(region="china")
    model = registry.create_model_instance("deepseek-chat", temperature=0.0)
    evaluator = QualityEvaluator(model)

    # 准备测试数据
    test_cases = [
        ("I live in New York and work at Google.", "I live in a major city and work at a tech company."),
        ("I'm 30 years old and make $100k.", "I'm in my 30s and earn a good salary."),
        ("I studied at Stanford University.", "I studied at a university."),
    ]

    import time

    print(f"批量评估 {len(test_cases)} 个样本...")
    start_time = time.time()

    for i, (orig, anon) in enumerate(test_cases, 1):
        scores = evaluator.evaluate_quality(orig, anon)
        print(f"  样本 {i}: 效用={scores.get_utility_score():.3f}, "
              f"BLEU={scores.bleu:.4f}")

    elapsed = time.time() - start_time
    print(f"\n✓ 总耗时: {elapsed:.1f}秒, 平均: {elapsed/len(test_cases):.1f}秒/样本")


def main():
    """运行所有测试"""
    print("="*80)
    print("  详细质量评估器 - 测试套件")
    print("  Detailed Quality Evaluator - Test Suite")
    print("="*80)

    tests = [
        ("基础质量评估", test_basic_evaluation),
        ("不同匿名化水平", test_multiple_anonymization_levels),
        ("JSON解析功能", test_json_parsing),
        ("错误处理", test_error_handling),
        ("异构模型集成", test_heterogeneous_integration),
        ("批量评估性能", test_batch_evaluation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print_section("测试总结")
    print(f"✓ 通过: {passed}/{len(tests)}")
    if failed > 0:
        print(f"✗ 失败: {failed}/{len(tests)}")
    print("\n所有测试完成！")


if __name__ == "__main__":
    main()
