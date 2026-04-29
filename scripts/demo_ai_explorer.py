#!/usr/bin/env python3
"""
AI探索器演示

展示：
1. 技能库覆盖分析
2. 识别技能缺口
3. 使用LLM生成新技能
4. 技能改进
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.bootstrap import (
    SkillRepository,
    SkillDefinition,
    SkillCategory,
    create_atomic_skill,
    AIExplorer
)
from src.models.providers.registry import get_registry


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


async def setup_demo_skills(repo: SkillRepository):
    """设置演示用的技能"""
    print("\n📚 设置演示技能库...")

    # 定义一些原子技能
    skills_to_create = [
        create_atomic_skill(
            name="read_json_file",
            description="读取JSON文件并解析为字典",
            inputs={"file_path": "str"},
            outputs={"data": "dict"},
            implementation="""
import json

with open(inputs['file_path'], 'r', encoding='utf-8') as f:
    data = json.load(f)
"""
        ),
        create_atomic_skill(
            name="write_json_file",
            description="将字典数据写入JSON文件",
            inputs={"file_path": "str", "data": "dict"},
            outputs={"success": "bool"},
            implementation="""
import json

with open(inputs['file_path'], 'w', encoding='utf-8') as f:
    json.dump(inputs['data'], f, ensure_ascii=False, indent=2)
success = True
"""
        ),
        create_atomic_skill(
            name="filter_dict_keys",
            description="根据键名前缀过滤字典",
            inputs={"data": "dict", "prefix": "str"},
            outputs={"filtered": "dict"},
            implementation="""
filtered = {
    k: v for k, v in inputs['data'].items()
    if k.startswith(inputs['prefix'])
}
"""
        ),
        create_atomic_skill(
            name="count_dict_items",
            description="统计字典中的项数",
            inputs={"data": "dict"},
            outputs={"count": "int"},
            implementation="""
count = len(inputs['data'])
"""
        ),
        create_atomic_skill(
            name="merge_dicts",
            description="合并多个字典",
            inputs={"dicts": "list"},
            outputs={"merged": "dict"},
            implementation="""
result = {}
for d in inputs['dicts']:
    result.update(d)
merged = result
"""
        ),
        create_atomic_skill(
            name="calculate_list_stats",
            description="计算数值列表的统计信息",
            inputs={"numbers": "list"},
            outputs={"stats": "dict"},
            implementation="""
import statistics

numbers = inputs['numbers']
stats = {
    'count': len(numbers),
    'sum': sum(numbers),
    'mean': statistics.mean(numbers) if numbers else 0,
    'median': statistics.median(numbers) if numbers else 0,
    'min': min(numbers) if numbers else None,
    'max': max(numbers) if numbers else None
}
"""
        )
    ]

    # 保存技能
    for skill in skills_to_create:
        await repo.save(skill)
        print(f"  ✓ {skill.name}")

    print(f"\n已创建 {len(skills_to_create)} 个原子技能")

    return skills_to_create


async def demo_coverage_analysis(explorer: AIExplorer, repo: SkillRepository):
    """演示覆盖分析"""
    print_section("1. 技能库覆盖分析")

    # 获取所有技能
    skills = await repo.get_all()

    # 执行覆盖分析
    analysis = await explorer.analyze_coverage(skills)

    # 详细展示分析结果
    print(f"\n📊 分析详情:")
    print(f"  总技能数: {analysis.total_skills}")
    print(f"  类别分布:")
    for category, count in analysis.by_category.items():
        print(f"    {category}: {count}")

    print(f"\n  功能覆盖率: {analysis.functionality_coverage:.1%}")

    if analysis.identified_gaps:
        print(f"\n  🔍 识别的缺口 ({len(analysis.identified_gaps)} 个):")
        for gap in analysis.identified_gaps:
            print(f"    • [{gap.priority}] {gap.description}")
            print(f"      缺失功能: {gap.missing_functionality}")

    if analysis.underutilized_skills:
        print(f"\n  ⚠️  未充分利用的技能 ({len(analysis.underutilized_skills)} 个):")
        for skill_id in analysis.underutilized_skills[:3]:
            skill = await repo.get(skill_id)
            if skill:
                print(f"    • {skill.name} (ID: {skill_id})")

    return analysis


async def demo_generate_prompts(explorer: AIExplorer, repo: SkillRepository):
    """演示生成探索提示"""
    print_section("2. 生成探索提示")

    skills = await repo.get_all()

    # 生成探索提示
    prompts = await explorer.generate_exploration_prompts(skills)

    print(f"\n📝 生成了 {len(prompts)} 个探索提示:")

    for i, prompt in enumerate(prompts, 1):
        print(f"\n--- 提示 {i} ---")
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)

    return prompts


async def demo_skill_generation(explorer: AIExplorer, repo: SkillRepository):
    """演示技能生成"""
    print_section("3. AI生成新技能")

    skills = await repo.get_all()

    # 创建一个组合提示
    combination_prompt = f"""
基于以下原子技能，创建2-3个有价值的功能技能：

可用技能：
{chr(10).join(f"- {s.name}: {s.description}" for s in skills[:5])}

请生成能够组合这些原子技能的功能技能，特别关注：
1. 数据处理流程（读取→处理→保存）
2. 批量操作能力
3. 错误处理机制

以JSON格式返回。
"""

    print(f"\n🤖 使用LLM生成新技能...")
    print(f"提示: {combination_prompt[:100]}...")

    try:
        # 执行探索
        result = await explorer.explore_direction(combination_prompt, skills)

        print(f"\n✅ 探索完成:")
        print(f"  生成新技能: {len(result.new_skills)} 个")
        print(f"  耗时: {result.generation_time:.2f} 秒")

        # 展示生成的技能
        if result.new_skills:
            print(f"\n📦 生成的技能:")
            for skill in result.new_skills:
                print(f"\n  • {skill.name}")
                print(f"    描述: {skill.description}")
                print(f"    类别: {skill.category.value}")
                if skill.parent_skills:
                    print(f"    依赖: {', '.join(skill.parent_skills)}")

                # 保存生成的技能
                skill_id = await repo.save(skill)
                print(f"    ✓ 已保存 (ID: {skill_id})")

        return result

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def demo_skill_improvement(explorer: AIExplorer, repo: SkillRepository):
    """演示技能改进"""
    print_section("4. 技能改进")

    # 获取一个技能
    skill = await repo.get_by_name("merge_dicts")

    if not skill:
        print("⚠️  找不到merge_dicts技能，跳过改进演示")
        return

    print(f"\n🔧 原始技能: {skill.name}")
    print(f"  描述: {skill.description}")
    print(f"  当前实现:")
    for line in skill.implementation.strip().split('\n'):
        print(f"    {line}")

    # 模拟反馈
    feedback = {
        "quality_score": 0.6,
        "success_rate": 0.7,
        "common_errors": ["ValueError when non-dict items in list"],
        "improvement_suggestion": "添加类型检查和错误处理"
    }

    print(f"\n📝 性能反馈:")
    print(f"  质量分数: {feedback['quality_score']}")
    print(f"  成功率: {feedback['success_rate']}")
    print(f"  常见错误: {feedback['common_errors']}")
    print(f"  改进建议: {feedback['improvement_suggestion']}")

    print(f"\n🤖 AI正在改进技能...")

    try:
        improved = await explorer.improve_skill(skill, feedback)

        if improved:
            print(f"\n✅ 改进完成:")
            print(f"  新描述: {improved.description}")
            print(f"  新实现:")
            for line in improved.implementation.strip().split('\n'):
                print(f"    {line}")

            # 创建版本
            await repo.create_version(
                improved,
                change_description="AI改进: 添加错误处理"
            )

            print(f"\n  ✓ 已保存改进版本")
        else:
            print(f"\n  ⚠️  改进失败")

    except Exception as e:
        print(f"\n❌ 改进过程出错: {e}")


async def demo_summary(explorer: AIExplorer, repo: SkillRepository):
    """演示摘要"""
    print_section("5. 探索摘要")

    # 获取探索摘要
    summary = explorer.get_exploration_summary()

    print(f"\n📊 AI探索摘要:")
    print(f"  总探索次数: {summary['total_explorations']}")
    print(f"  生成技能总数: {summary['total_skills_generated']}")
    if summary['total_explorations'] > 0:
        print(f"  平均每次生成: {summary['avg_skills_per_exploration']:.1f} 个技能")
        print(f"  平均耗时: {summary['avg_time_per_exploration']:.1f} 秒")

    # 获取仓库统计
    stats = await repo.get_statistics()

    print(f"\n📊 仓库统计:")
    print(f"  总技能数: {stats['total_skills']}")
    print(f"  按类别: {stats['by_category']}")
    print(f"  按生成方式: {stats['by_generation_method']}")


async def main():
    """主函数"""
    print("\n" + "="*70)
    print("  🤖 AI探索器演示")
    print("  基于LLM的技能分析与生成")
    print("="*70)

    try:
        # 1. 初始化仓库
        print("\n📁 初始化技能仓库...")
        repo = SkillRepository(storage_path="./explorer_demo_repository")

        # 2. 设置演示技能
        await setup_demo_skills(repo)

        # 3. 初始化LLM客户端
        print("\n🤖 初始化LLM客户端...")
        try:
            registry = get_registry(region="china")
            llm_client = registry.create_model_instance("qwen-plus", temperature=0.7)

            if not llm_client:
                print("⚠️  无法创建LLM客户端，使用模拟模式")
                # 创建模拟客户端
                class MockLLMClient:
                    def predict_string(self, prompt):
                        # 返回模拟响应
                        return """```json
[
  {
    "name": "batch_process_files",
    "description": "批量处理多个JSON文件",
    "inputs": {"file_paths": "list", "operation": "str"},
    "outputs": {"results": "list", "success_count": "int"},
    "implementation": "# 批量处理文件\\nresults = []\\nsuccess_count = 0\\nfor path in inputs['file_paths']:\\n    try:\\n        # 读取和处理文件\\n        with open(path, 'r') as f:\\n            data = json.load(f)\\n        results.append(data)\\n        success_count += 1\\n    except Exception as e:\\n        pass"
  }
]
```"""

                llm_client = MockLLMClient()
                print("  ✓ 使用模拟LLM客户端")

            else:
                print("  ✓ LLM客户端创建成功")

        except Exception as e:
            print(f"⚠️  LLM初始化失败: {e}，使用模拟模式")
            # 使用模拟客户端
            class MockLLMClient:
                def predict_string(self, prompt):
                    return """[]"""
            llm_client = MockLLMClient()

        # 4. 创建AI探索器
        explorer = AIExplorer(llm_client)

        # 5. 运行演示
        await demo_coverage_analysis(explorer, repo)
        await demo_generate_prompts(explorer, repo)
        await demo_skill_generation(explorer, repo)
        await demo_skill_improvement(explorer, repo)
        await demo_summary(explorer, repo)

        print("\n" + "="*70)
        print("  ✅ 演示完成！")
        print("="*70)
        print(f"\n💾 仓库位置: ./explorer_demo_repository/")
        print(f"   可以查看生成的技能文件\n")

    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
