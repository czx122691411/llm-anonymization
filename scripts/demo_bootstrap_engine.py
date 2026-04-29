#!/usr/bin/env python3
"""
自举引擎完整演示

展示完整的五阶段自举循环：
1. 初始化 - 人类定义种子技能
2. 探索与生成 - AI生成新技能
3. 测试与评估 - 自动测试评估
4. 反馈与迭代 - AI改进技能
5. 注入与验证 - 人类审核（可选）
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bootstrap import (
    SkillRepository,
    BootstrapConfig,
    BootstrapEngine,
    create_atomic_skill
)
from src.models.providers.registry import get_registry


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


async def demo_full_bootstrap_cycle():
    """演示完整的自举循环"""
    print("\n" + "="*70)
    print("  🚀 人机协作自举引擎 - 完整演示")
    print("  五阶段自举循环")
    print("="*70)

    # 1. 初始化配置
    print_section("1. 初始化配置")

    config = BootstrapConfig(
        storage_path="./bootstrap_demo_repository",
        improvement_threshold=0.6,
        validation_threshold=0.8,
        target_quality=0.85,
        max_iterations=2,  # 演示用，减少迭代次数
        enable_auto_testing=True,
        enable_human_interaction=False,  # 演示时禁用人类交互
        log_level="INFO"
    )

    print("配置参数:")
    print(f"  存储路径: {config.storage_path}")
    print(f"  目标质量: {config.target_quality}")
    print(f"  最大迭代: {config.max_iterations}")
    print(f"  自动测试: {config.enable_auto_testing}")

    # 2. 初始化LLM客户端
    print_section("2. 初始化LLM客户端")

    try:
        registry = get_registry(region="china")
        llm_client = registry.create_model_instance("qwen-plus", temperature=0.7)

        if not llm_client:
            raise Exception("LLM客户端创建失败")

        print("✓ LLM客户端创建成功")
    except Exception as e:
        print(f"⚠️  LLM客户端初始化失败: {e}")
        print("  使用模拟LLM客户端...")

        # 创建模拟客户端
        class MockLLMClient:
            def predict_string(self, prompt):
                # 返回模拟的技能生成响应
                return """```json
[
  {
    "name": "process_data_pipeline",
    "description": "数据处理流水线：读取、验证、转换、保存",
    "inputs": {"input_file": "str", "output_file": "str"},
    "outputs": {"records_processed": "int", "success": "bool"},
    "implementation": "import json\\n\\n# 读取文件\\nwith open(inputs['input_file'], 'r') as f:\\n    data = json.load(f)\\n\\n# 验证数据\\nif not isinstance(data, list):\\n    data = [data]\\n\\n# 处理数据\\nprocessed = []\\nfor item in data:\\n    processed.append({**item, 'processed': True})\\n\\n# 保存结果\\nwith open(inputs['output_file'], 'w') as f:\\n    json.dump(processed, f)\\n\\nrecords_processed = len(processed)\\nsuccess = True"
  }
]
```"""

        llm_client = MockLLMClient()
        print("  ✓ 模拟LLM客户端已创建")

    # 3. 创建自举引擎
    print_section("3. 创建自举引擎")

    engine = BootstrapEngine(config, llm_client)
    print("✓ 自举引擎初始化完成")

    # 4. 运行自举循环
    print_section("4. 运行自举循环")

    objective = """
    构建数据处理相关的技能库，包括：
    - 文件读写能力
    - 数据验证能力
    - 数据转换能力
    - 批处理能力
    - 错误处理能力

目标是创建一个高质量、可复用的技能集合。
    """

    print(f"自举目标: {objective.strip()}")

    result = await engine.run_bootstrap_cycle(
        objective=objective,
        max_iterations=config.max_iterations
    )

    # 5. 展示结果
    print_section("5. 自举结果")

    print(f"\n状态: {result.final_state.value}")
    print(f"迭代次数: {result.iterations}")
    print(f"总耗时: {result.total_duration:.1f} 秒")
    print(f"\n技能统计:")
    print(f"  新增技能: {result.total_new_skills}")
    print(f"  修改技能: {result.total_modified_skills}")
    print(f"  废弃技能: {result.total_deprecated_skills}")
    print(f"\n质量指标:")
    print(f"  平均质量分数: {result.final_avg_quality:.2f}")
    print(f"  平均成功率: {result.final_avg_success_rate:.2%}")

    if result.key_insights:
        print(f"\n关键洞察:")
        for insight in result.key_insights:
            print(f"  • {insight}")

    if result.recommendations:
        print(f"\n改进建议:")
        for rec in result.recommendations:
            print(f"  • {rec}")

    # 6. 查看生成的技能
    print_section("6. 查看生成的技能")

    repo = SkillRepository(config.storage_path)
    all_skills = await repo.get_all()

    print(f"\n仓库中的技能 ({len(all_skills)} 个):")

    for skill in all_skills:
        print(f"\n  • {skill.name}")
        print(f"    描述: {skill.description}")
        print(f"    类别: {skill.category.value}")
        print(f"    质量: {skill.quality.score:.2f}")
        print(f"    生成方式: {skill.generation_method.value}")

    # 7. 展示阶段详情
    print_section("7. 阶段执行详情")

    for phase_result in result.phase_results:
        status = "✓" if phase_result.is_successful() else "✗"
        print(f"\n{status} 阶段: {phase_result.phase.value}")
        print(f"  耗时: {phase_result.duration:.2f}秒")
        print(f"  新技能: {len(phase_result.new_skills)}")
        print(f"  修改: {len(phase_result.modified_skills)}")
        print(f"  废弃: {len(phase_result.deprecated_skills)}")

        if phase_result.metrics:
            print(f"  指标: {phase_result.metrics}")

        if phase_result.insights:
            print(f"  洞察:")
            for insight in phase_result.insights[:3]:
                print(f"    - {insight}")

        if phase_result.errors:
            print(f"  错误:")
            for error in phase_result.errors[:3]:
                print(f"    - {error}")

    # 8. 查看仓库文件
    print_section("8. 仓库文件")

    print(f"\n仓库位置: {config.storage_path}")
    print("文件结构:")

    import subprocess
    result = subprocess.run(
        ["find", config.storage_path, "-type", "f", "-name", "*.json"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        files = result.stdout.strip().split('\n')
        for file_path in files[:10]:  # 显示前10个文件
            file_path = file_path.replace(config.storage_path + "/", "")
            print(f"  • {file_path}")

        if len(files) > 10:
            print(f"  ... 还有 {len(files) - 10} 个文件")

    print("\n" + "="*70)
    print("  ✅ 演示完成！")
    print("="*70)

    print(f"\n💾 结果已保存到: {config.storage_path}")
    print(f"   查看技能: {config.storage_path}/atomic/")
    print(f"   查看循环: {config.storage_path}/_cycles/")
    print(f"   查看审核: {config.storage_path}/_review/")

    return result


async def demo_simple_cycle():
    """演示简化的自举循环（快速版）"""
    print("\n" + "="*70)
    print("  🚀 快速演示 - 单轮自举")
    print("="*70)

    # 使用快速配置
    config = BootstrapConfig(
        storage_path="./quick_demo_repository",
        max_iterations=1,
        enable_auto_testing=False,
        enable_human_interaction=False,
        log_level="WARNING"  # 减少日志输出
    )

    # 模拟LLM
    class MockLLM:
        def predict_string(self, prompt):
            return """[]"""  # 返回空，模拟没有生成新技能

    engine = BootstrapEngine(config, MockLLM())

    objective = "创建基础的文件处理技能"
    print(f"目标: {objective}")

    result = await engine.run_bootstrap_cycle(objective, max_iterations=1)

    print(f"\n结果:")
    print(f"  成功: {result.success}")
    print(f"  状态: {result.final_state.value}")
    print(f"  迭代: {result.iterations}")

    return result


async def main():
    """主函数"""
    try:
        # 运行完整演示
        await demo_full_bootstrap_cycle()

        # 可选：运行快速演示
        # await demo_simple_cycle()

    except KeyboardInterrupt:
        print("\n⚠️  演示被中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
