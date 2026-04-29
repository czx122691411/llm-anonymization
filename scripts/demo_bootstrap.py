#!/usr/bin/env python3
"""
自举框架基础功能演示

展示：
1. 创建原子技能
2. 保存到仓库
3. 技能查询和搜索
4. 技能执行
5. 版本管理
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bootstrap import (
    SkillDefinition,
    SkillCategory,
    GenerationMethod,
    SkillRepository,
    create_atomic_skill,
    BootstrapConfig
)


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


async def demo_basic_operations():
    """演示基础操作"""
    print_section("1. 基础操作演示")

    # 创建仓库
    repo = SkillRepository(storage_path="./demo_repository")

    # 创建一些原子技能
    print("\n📝 创建原子技能...")

    # 技能1: 计算平均值
    calc_average = create_atomic_skill(
        name="calculate_average",
        description="计算数值列表的平均值",
        inputs={"numbers": "list"},
        outputs={"average": "float"},
        implementation="""
# 计算平均值
result = sum(inputs['numbers']) / len(inputs['numbers'])
average = result
"""
    )
    print(f"  ✓ 创建技能: {calc_average.name} (ID: {calc_average.skill_id})")

    # 技能2: 过滤列表
    filter_list = create_atomic_skill(
        name="filter_list",
        description="根据条件过滤列表中的元素",
        inputs={"items": "list", "min_value": "int"},
        outputs={"filtered": "list"},
        implementation="""
# 过滤列表
filtered = [x for x in inputs['items'] if x >= inputs['min_value']]
"""
    )
    print(f"  ✓ 创建技能: {filter_list.name} (ID: {filter_list.skill_id})")

    # 技能3: 统计词频
    word_frequency = create_atomic_skill(
        name="word_frequency",
        description="统计文本中各单词的出现频率",
        inputs={"text": "str"},
        outputs={"frequencies": "dict"},
        implementation="""
import re
from collections import Counter

# 分词并统计
words = re.findall(r'\\w+', inputs['text'].lower())
frequencies = dict(Counter(words))
"""
    )
    print(f"  ✓ 创建技能: {word_frequency.name} (ID: {word_frequency.skill_id})")

    # 保存技能
    print("\n💾 保存技能到仓库...")
    await repo.save(calc_average)
    await repo.save(filter_list)
    await repo.save(word_frequency)
    print("  ✓ 所有技能已保存")

    return repo


async def demo_query_and_search(repo: SkillRepository):
    """演示查询和搜索"""
    print_section("2. 查询和搜索演示")

    # 获取所有技能
    print("\n📋 获取所有技能...")
    all_skills = await repo.get_all()
    print(f"  共有 {len(all_skills)} 个技能:")
    for skill in all_skills:
        print(f"    - {skill.name}: {skill.description}")

    # 按类别查询
    print("\n🔍 按类别查询...")
    atomic_skills = await repo.get_all(category=SkillCategory.ATOMIC)
    print(f"  原子技能: {len(atomic_skills)} 个")

    # 搜索技能
    print("\n🔎 搜索技能...")
    results = await repo.search("计算")
    print(f"  搜索 '计算': {len(results)} 个结果")
    for skill in results:
        print(f"    - {skill.name}: {skill.description}")


async def demo_skill_execution(repo: SkillRepository):
    """演示技能执行"""
    print_section("3. 技能执行演示")

    # 获取技能
    calc_avg = await repo.get_by_name("calculate_average")

    if calc_avg:
        print(f"\n⚡ 执行技能: {calc_avg.name}")

        # 准备输入
        test_inputs = {
            "numbers": [10, 20, 30, 40, 50]
        }
        print(f"  输入: {test_inputs}")

        # 执行技能
        try:
            result = calc_avg.execute(test_inputs)
            print(f"  输出: {result}")
            print(f"  ✓ 执行成功")
        except Exception as e:
            print(f"  ✗ 执行失败: {e}")

    # 测试另一个技能
    filter_skill = await repo.get_by_name("filter_list")

    if filter_skill:
        print(f"\n⚡ 执行技能: {filter_skill.name}")

        test_inputs = {
            "items": [5, 10, 15, 3, 8, 12],
            "min_value": 10
        }
        print(f"  输入: {test_inputs}")

        try:
            result = filter_skill.execute(test_inputs)
            print(f"  输出: {result}")
            print(f"  ✓ 执行成功")
        except Exception as e:
            print(f"  ✗ 执行失败: {e}")


async def demo_version_management(repo: SkillRepository):
    """演示版本管理"""
    print_section("4. 版本管理演示")

    # 获取一个技能
    skill = await repo.get_by_name("calculate_average")

    if skill:
        print(f"\n📚 技能: {skill.name}")
        print(f"  当前版本: v{skill.metadata.get('version', 1)}")
        print(f"  实现代码:")
        for line in skill.implementation.strip().split('\n'):
            print(f"    {line}")

        # 修改技能
        print("\n✏️  修改技能实现...")
        skill.implementation = """
# 计算平均值（改进版，增加空值检查）
numbers = [x for x in inputs['numbers'] if x is not None]
if not numbers:
    average = 0.0
else:
    average = sum(numbers) / len(numbers)
"""

        # 创建新版本
        print("💾 保存新版本...")
        version_info = await repo.create_version(
            skill,
            change_description="添加空值检查，提高鲁棒性"
        )
        print(f"  ✓ 版本 {version_info.version} 已创建")
        print(f"  变更说明: {version_info.change_description}")

        # 查看版本历史
        print("\n📜 版本历史:")
        history = await repo.get_version_history(skill.skill_id)
        for v in history:
            print(f"  v{v.version} - {v.created_at}")
            print(f"    创建方式: {v.created_by}")
            print(f"    说明: {v.change_description}")


async def demo_statistics(repo: SkillRepository):
    """演示统计分析"""
    print_section("5. 统计分析演示")

    # 获取仓库统计
    stats = await repo.get_statistics()

    print(f"\n📊 仓库统计:")
    print(f"  总技能数: {stats['total_skills']}")
    print(f"  按类别:")
    for category, count in stats['by_category'].items():
        print(f"    {category}: {count}")
    print(f"  按状态:")
    for status, count in stats['by_status'].items():
        print(f"    {status}: {count}")
    print(f"  按生成方式:")
    for method, count in stats['by_generation_method'].items():
        print(f"    {method}: {count}")
    print(f"  平均质量分数: {stats['avg_quality']:.2f}")
    print(f"  孤立技能数: {stats['orphans']}")


async def demo_composite_skill(repo: SkillRepository):
    """演示组合技能创建"""
    print_section("6. 组合技能演示")

    print("\n🔧 创建组合技能...")

    # 创建一个组合技能：处理数据流水线
    from src.bootstrap.models import SkillDefinition, ParameterSpec

    process_pipeline = SkillDefinition(
        skill_id="",  # 将自动生成
        name="data_processing_pipeline",
        description="数据处理流水线：过滤 → 计算平均值",
        category=SkillCategory.FUNCTIONAL,
        inputs={
            "data": ParameterSpec(
                name="data",
                type="list",
                description="原始数据列表"
            ),
            "threshold": ParameterSpec(
                name="threshold",
                type="int",
                description="过滤阈值",
                default=10
            )
        },
        outputs={
            "filtered_count": ParameterSpec(name="filtered_count", type="int"),
            "average": ParameterSpec(name="average", type="float")
        },
        implementation="""
# 步骤1: 过滤数据
filter_skill = context['skills']['filter_list']
filter_result = filter_skill.execute({
    'items': inputs['data'],
    'min_value': inputs['threshold']
})
filtered = filter_result['filtered']

# 步骤2: 计算平均值
calc_skill = context['skills']['calculate_average']
calc_result = calc_skill.execute({
    'numbers': filtered
})

# 输出结果
filtered_count = len(filtered)
average = calc_result['average']
""",
        dependencies=["filter_list", "calculate_average"],
        generation_method=GenerationMethod.MANUAL
    )

    print(f"  ✓ 创建组合技能: {process_pipeline.name}")
    print(f"    描述: {process_pipeline.description}")
    print(f"    依赖: {', '.join(process_pipeline.dependencies)}")

    # 保存
    skill_id = await repo.save(process_pipeline)
    print(f"  ✓ 已保存 (ID: {skill_id})")

    # 执行组合技能
    print(f"\n⚡ 执行组合技能...")

    # 准备上下文（包含依赖的技能）
    exec_context = {
        'skills': {
            'filter_list': await repo.get_by_name('filter_list'),
            'calculate_average': await repo.get_by_name('calculate_average')
        }
    }

    test_inputs = {
        'data': [5, 15, 8, 20, 12, 3, 25, 18],
        'threshold': 10
    }
    print(f"  输入: {test_inputs}")

    try:
        result = process_pipeline.execute(test_inputs, context=exec_context)
        print(f"  输出: {result}")
        print(f"  ✓ 执行成功")
        print(f"    过滤后数量: {result['filtered_count']}")
        print(f"    平均值: {result['average']}")
    except Exception as e:
        print(f"  ✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("  🚀 人机协作自举框架 - 基础功能演示")
    print("="*70)

    try:
        # 1. 基础操作
        repo = await demo_basic_operations()

        # 2. 查询和搜索
        await demo_query_and_search(repo)

        # 3. 技能执行
        await demo_skill_execution(repo)

        # 4. 版本管理
        await demo_version_management(repo)

        # 5. 统计分析
        await demo_statistics(repo)

        # 6. 组合技能
        await demo_composite_skill(repo)

        print("\n" + "="*70)
        print("  ✅ 演示完成！")
        print("="*70)
        print(f"\n💾 技能仓库位置: ./demo_repository/")
        print(f"   可以查看保存的技能文件和版本历史\n")

    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
