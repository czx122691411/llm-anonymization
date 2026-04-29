#!/usr/bin/env python3
"""
完整示例：使用自定义技能构建数据处理流程

这个示例展示了如何在实际项目中使用 Claude 自定义技能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bootstrap import (
    BootstrapEngine,
    BootstrapConfig,
    AISkillExecutor,
    SkillRepository,
    create_atomic_skill
)
from src.models.providers.registry import get_registry


# ============================================================================
# 示例 1: 使用 Bootstrap Framework 技能创建数据处理技能
# ============================================================================

def example_1_create_skills():
    """示例1: 创建基础数据处理技能"""
    print("\n" + "="*70)
    print("示例 1: 使用 Bootstrap Framework 创建技能")
    print("="*70)

    # 创建读取文本文件技能
    read_file = create_atomic_skill(
        name="read_text_file",
        description="读取文本文件内容",
        inputs={"file_path": "str"},
        outputs={"content": "str", "line_count": "int", "success": "bool"},
        implementation='''
try:
    with open(inputs["file_path"], "r", encoding="utf-8") as f:
        content = f.read()
    line_count = len(content.split("\\n"))
    success = True
except Exception as e:
    content = str(e)
    line_count = 0
    success = False
'''
    )

    # 创建文本分析技能
    analyze_text = create_atomic_skill(
        name="analyze_text",
        description="分析文本的基本统计信息",
        inputs={"text": "str"},
        outputs={
            "char_count": "int",
            "word_count": "int",
            "line_count": "int",
            "avg_word_length": "float"
        },
        implementation='''
char_count = len(inputs["text"])
words = inputs["text"].split()
word_count = len(words)
line_count = len(inputs["text"].split("\\n"))
avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0
'''
    )

    # 创建数据脱敏技能（使用 Data Anonymization 技能的脱敏策略）
    anonymize_data = create_atomic_skill(
        name="anonymize_data",
        description="脱敏文本中的敏感信息",
        inputs={"text": "str"},
        outputs={"anonymized": "str", "items_found": "int"},
        implementation='''
import re

anonymized = inputs["text"]
items_found = 0

# 手机号脱敏
phones = re.findall(r"1[3-9]\\d{9}", anonymized)
items_found += len(phones)
anonymized = re.sub(
    r"1[3-9]\\d{9}",
    lambda m: m.group()[:3] + "****" + m.group()[-4:],
    anonymized
)

# 邮箱脱敏
emails = re.findall(r"\\w+@\\w+\\.\\w+", anonymized)
items_found += len(emails)
anonymized = re.sub(
    r"\\w+@\\w+\\.\\w+",
    lambda m: m.group()[0] + "***@" + m.group().split("@")[1],
    anonymized
)
'''
    )

    # 测试技能
    print("\n✅ 技能创建成功:")
    print(f"  - {read_file.name}")
    print(f"  - {analyze_text.name}")
    print(f"  - {anonymize_data.name}")

    # 执行测试
    print("\n🧪 测试技能执行:")

    test_data = "联系张三，电话13812345678，邮箱zhangsan@example.com"
    result = anonymize_data.execute({"text": test_data})
    print(f"  原始: {test_data}")
    print(f"  脱敏: {result['anonymized']}")
    print(f"  发现敏感信息: {result['items_found']} 处")

    return [read_file, analyze_text, anonymize_data]


# ============================================================================
# 示例 2: 使用 Heterogeneous Training 技能配置模型
# ============================================================================

def example_2_configure_models():
    """示例2: 配置异构模型训练"""
    print("\n" + "="*70)
    print("示例 2: 使用 Heterogeneous Training 配置模型")
    print("="*70)

    # 获取模型注册表
    registry = get_registry(region="china")

    # 定义要使用的模型（参考 heterogeneous-training.md）
    model_configs = [
        {"name": "qwen-plus", "temperature": 0.7, "max_tokens": 2000},
        {"name": "deepseek-chat", "temperature": 0.8, "max_tokens": 2000},
        {"name": "glm-4", "temperature": 0.6, "max_tokens": 2000}
    ]

    models = {}
    for config in model_configs:
        try:
            model = registry.create_model_instance(
                config["name"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
            models[config["name"]] = model
            print(f"✅ {config['name']} 创建成功")
        except Exception as e:
            print(f"⚠️  {config['name']} 创建失败: {e}")

    print(f"\n📊 成功初始化 {len(models)} 个模型")

    return models


# ============================================================================
# 示例 3: 完整的数据处理流程
# ============================================================================

def example_3_complete_pipeline():
    """示例3: 组合使用多个技能的完整流程"""
    print("\n" + "="*70)
    print("示例 3: 完整数据处理流程")
    print("="*70)

    # 步骤1: 创建技能
    print("\n📝 步骤1: 创建处理技能")

    extract_info = create_atomic_skill(
        name="extract_contact_info",
        description="从文本中提取联系信息",
        inputs={"text": "str"},
        outputs={"phones": "list", "emails": "list", "count": "int"},
        implementation='''
import re

phones = re.findall(r"1[3-9]\\d{9}", inputs["text"])
emails = re.findall(r"\\w+@\\w+\\.\\w+", inputs["text"])
count = len(phones) + len(emails)
'''
    )

    validate_data = create_atomic_skill(
        name="validate_contact_info",
        description="验证联系信息的格式",
        inputs={"phones": "list", "emails": "list"},
        outputs={
            "valid_phones": "list",
            "valid_emails": "list",
            "invalid_count": "int"
        },
        implementation='''
import re

valid_phones = [p for p in inputs["phones"] if re.match(r"^1[3-9]\\d{9}$", p)]
valid_emails = [e for e in inputs["emails"] if "@" in e and "." in e]
invalid_count = len(inputs["phones"]) + len(inputs["emails"]) - len(valid_phones) - len(valid_emails)
'''
    )

    format_output = create_atomic_skill(
        name="format_contact_report",
        description="格式化联系信息报告",
        inputs={
            "valid_phones": "list",
            "valid_emails": "list",
            "invalid_count": "int"
        },
        outputs={"report": "str"},
        implementation='''
report = f"""联系信息报告
{'='*40}
有效手机号: {len(inputs['valid_phones'])} 个
有效邮箱: {len(inputs['valid_emails'])} 个
无效数量: {inputs['invalid_count']} 个

详细列表:
"""
if inputs['valid_phones']:
    report += "\\n手机号:\\n  " + "\\n  ".join(inputs['valid_phones'])
if inputs['valid_emails']:
    report += "\\n邮箱:\\n  " + "\\n  ".join(inputs['valid_emails'])

if inputs['invalid_count'] > 0:
    report += f"\\n⚠️  警告: 发现 {inputs['invalid_count']} 条无效信息"
'''
    )

    # 步骤2: 准备测试数据
    print("\n📄 步骤2: 准备测试数据")

    sample_text = """
    客户信息列表:
    1. 张三 - 电话:13812345678, 邮箱:zhangsan@example.com
    2. 李四 - 电话:15987654321, 邮箱:lisi@company.com
    3. 王五 - 电话:12345678901(无效), 邮箱:wangwu@invalid
    """

    # 步骤3: 执行处理流程
    print("\n⚙️  步骤3: 执行处理流程")

    # 3.1 提取信息
    print("  3.1 提取联系信息...")
    extracted = extract_info.execute({"text": sample_text})
    print(f"      提取到: {extracted['count']} 条信息")

    # 3.2 验证信息
    print("  3.2 验证信息格式...")
    validated = validate_data.execute({
        "phones": extracted["phones"],
        "emails": extracted["emails"]
    })
    print(f"      有效: {extracted['count'] - validated['invalid_count']} 条")
    print(f"      无效: {validated['invalid_count']} 条")

    # 3.3 生成报告
    print("  3.3 生成报告...")
    report = format_output.execute({
        "valid_phones": validated["valid_phones"],
        "valid_emails": validated["valid_emails"],
        "invalid_count": validated["invalid_count"]
    })

    print("\n📊 处理结果:")
    print(report["report"])


# ============================================================================
# 示例 4: 自举引擎实际应用
# ============================================================================

async def example_4_bootstrap_cycle():
    """示例4: 运行完整的自举循环"""
    print("\n" + "="*70)
    print("示例 4: 运行完整的自举循环")
    print("="*70)

    # 配置自举引擎
    config = BootstrapConfig(
        storage_path="./example_skills_repository",
        target_quality=0.75,
        max_iterations=2,
        enable_auto_testing=True,
        enable_human_interaction=False
    )

    # 创建模拟LLM客户端（演示用）
    class MockLLM:
        def predict_string(self, prompt):
            return """```json
[
  {
    "name": "count_words_in_text",
    "description": "统计文本中的单词数量",
    "inputs": {"text": "str"},
    "outputs": {"word_count": "int"},
    "implementation": "words = inputs['text'].split()\\nword_count = len(words)"
  }
]
```"""

    # 创建引擎
    engine = BootstrapEngine(config, MockLLM())

    # 定义目标
    objective = "构建文本处理相关的技能库"

    print(f"\n🎯 自举目标: {objective}")
    print(f"📦 存储路径: {config.storage_path}")
    print(f"🎯 目标质量: {config.target_quality}")

    # 运行自举
    print("\n🚀 开始自举循环...")
    result = await engine.run_bootstrap_cycle(
        objective=objective,
        max_iterations=2
    )

    # 显示结果
    print("\n📊 自举结果:")
    print(f"  迭代次数: {result.iterations}")
    print(f"  新增技能: {result.total_new_skills}")
    print(f"  平均质量: {result.final_avg_quality:.2f}")
    print(f"  总耗时: {result.total_duration:.1f}秒")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数：运行所有示例"""
    print("\n" + "="*70)
    print("  Claude 自定义技能使用示例")
    print("  展示如何在实际项目中使用 .claude/skills/ 中定义的技能")
    print("="*70)

    try:
        # 运行示例1
        skills = example_1_create_skills()

        # 运行示例2
        models = example_2_configure_models()

        # 运行示例3
        example_3_complete_pipeline()

        # 运行示例4（异步）
        print("\n" + "="*70)
        print("是否运行示例4 (完整自举循环)? [y/N]: ", end="")
        choice = input().strip().lower()

        if choice == 'y':
            asyncio.run(example_4_bootstrap_cycle())

        print("\n" + "="*70)
        print("✅ 所有示例运行完成！")
        print("="*70)

        print("\n💡 提示:")
        print("  - 查看 .claude/skills/README.md 了解更多")
        print("  - 查看 .claude/skills/USAGE_GUIDE.md 学习详细用法")
        print("  - 运行 python test_skills.py 验证技能功能")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
