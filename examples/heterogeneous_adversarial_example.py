"""
异构模型组合示例：qwen-plus + deepseek-reasoner + qwen-max

这个示例展示了如何使用不同提供商的模型进行对抗匿名化：
- 防御者: qwen-plus (高性价比，平衡性能)
- 攻击者: deepseek-reasoner (强推理能力，善于攻击)
- 评估者: qwen-max (最强综合能力，准确评估)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.providers.registry import get_registry


def setup_heterogeneous_composition():
    """设置异构模型组合"""
    print("=" * 80)
    print("设置异构模型组合")
    print("=" * 80)

    # 获取中国区域注册表
    registry = get_registry(region="china")

    # 定义异构组合
    composition = {
        'defender': 'qwen-plus',
        'attacker': 'deepseek-reasoner',
        'evaluator': 'qwen-max'
    }

    print("\n📋 模型组合:")
    for role, model_id in composition.items():
        model_info = registry.get_model_info(model_id)
        availability = registry.check_provider_availability(model_info.provider_id)

        if availability.status.value == 'available':
            role_score = getattr(model_info, f'{role}_score')
            print(f"  {role.upper()}: {model_id}")
            print(f"    提供商: {model_info.provider_id}")
            print(f"    {role}得分: {role_score:.2f}")
            print(f"    成本: ¥{model_info.cost_per_1k_input:.2f}/1k输入 + ¥{model_info.cost_per_1k_output:.2f}/1k输出")
        else:
            print(f"  {role.upper()}: {model_id} - 不可用")
            print(f"    错误: {availability.error_message}")
            return None

    print("\n🔧 创建模型实例...")
    try:
        # 创建模型实例
        defender = registry.create_model_instance("qwen-plus", temperature=0.1)
        attacker = registry.create_model_instance("deepseek-reasoner", temperature=0.1)
        evaluator = registry.create_model_instance("qwen-max", temperature=0.0)

        if not all([defender, attacker, evaluator]):
            print("✗ 模型实例创建失败")
            return None

        print("✓ 所有模型实例创建成功")
        return {
            'defender': defender,
            'attacker': attacker,
            'evaluator': evaluator
        }

    except Exception as e:
        print(f"✗ 创建模型实例时出错: {e}")
        return None


def estimate_cost(num_profiles=100, num_rounds=5):
    """估算实验成本"""
    print("\n" + "=" * 80)
    print("成本估算")
    print("=" * 80)

    registry = get_registry(region="china")

    composition = {
        'defender': 'qwen-plus',
        'attacker': 'deepseek-reasoner',
        'evaluator': 'qwen-max'
    }

    # 每轮的token估算
    tokens_per_round = {
        'defender': {'input': 800, 'output': 400},
        'attacker': {'input': 600, 'output': 300},
        'evaluator': {'input': 1000, 'output': 150}
    }

    total_cost = 0
    total_tokens = 0

    print(f"\n实验参数: {num_profiles}个profile, {num_rounds}轮训练")

    for role, model_id in composition.items():
        model_info = registry.get_model_info(model_id)
        tokens = tokens_per_round[role]

        total_calls = num_profiles * num_rounds
        total_input = total_calls * tokens['input']
        total_output = total_calls * tokens['output']
        role_tokens = total_input + total_output

        cost = (total_input / 1000) * model_info.cost_per_1k_input + \
               (total_output / 1000) * model_info.cost_per_1k_output

        total_cost += cost
        total_tokens += role_tokens

        print(f"\n{role.upper()} ({model_id}):")
        print(f"  调用次数: {total_calls:,}")
        print(f"  Token数: {role_tokens:,}")
        print(f"  成本: ¥{cost:.2f}")

    print(f"\n{'-' * 40}")
    print(f"总Token数: {total_tokens:,}")
    print(f"总成本: ¥{total_cost:.2f}")
    print(f"每个profile成本: ¥{total_cost/num_profiles:.4f}")

    return total_cost


def run_simple_test(models):
    """运行简单的功能测试"""
    print("\n" + "=" * 80)
    print("功能测试")
    print("=" * 80)

    if not models:
        print("✗ 模型不可用，跳过测试")
        return

    test_text = "这是一个测试文本，用于验证模型是否正常工作。"

    for role, model in models.items():
        try:
            print(f"\n测试 {role.upper()} ({model.config.name})...")
            result = model.predict_string(test_text)
            print(f"✓ {role.upper()} 测试成功")
            print(f"  输入: {test_text}")
            print(f"  输出: {result[:100]}...")
        except Exception as e:
            print(f"✗ {role.upper()} 测试失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("异构模型组合示例：qwen-plus + deepseek-reasoner + qwen-max")
    print("=" * 80)

    # 检查环境变量
    required_keys = {
        'DASHSCOPE_API_KEY': 'Qwen (Alibaba Cloud)',
        'DEEPSEEK_API_KEY': 'DeepSeek'
    }

    print("\n🔑 检查API密钥:")
    all_keys_configured = True
    for env_var, provider in required_keys.items():
        key = os.environ.get(env_var)
        if key:
            print(f"  ✓ {provider}: 已配置")
        else:
            print(f"  ✗ {provider}: 未配置 ({env_var})")
            all_keys_configured = False

    if not all_keys_configured:
        print("\n请先配置所有必需的API密钥")
        return

    # 设置异构组合
    models = setup_heterogeneous_composition()

    # 估算成本
    estimate_cost(num_profiles=100, num_rounds=5)

    # 运行测试
    run_simple_test(models)

    print("\n" + "=" * 80)
    print("示例完成！")
    print("=" * 80)

    print("\n💡 使用提示:")
    print("1. 在实际使用时，可以调整temperature参数控制模型创造性")
    print("2. 可以通过修改composition字典尝试不同的模型组合")
    print("3. 建议先用小批量数据测试，验证效果后再大规模运行")
    print("4. 可以通过reduce_redundancy参数控制匿名化强度")


if __name__ == "__main__":
    main()
