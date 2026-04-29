#!/bin/bash
# Claude 自定义技能演示脚本

echo "════════════════════════════════════════════════════════════════"
echo "  Claude 自定义技能实际使用演示"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 创建临时演示脚本
cat > /tmp/demo_skills.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/rooter/llm-anonymization')

from src.bootstrap import create_atomic_skill

print("📚 演示 1: 创建数据处理技能")
print("─"*50)

# 使用 Bootstrap Framework 技能创建技能
skill = create_atomic_skill(
    name="process_user_data",
    description="处理用户数据",
    inputs={"data": "str"},
    outputs={"processed": "str", "length": "int"},
    implementation='''processed = inputs["data"].strip().upper()
length = len(processed)
'''
)

# 执行技能
result = skill.execute({"data": "  hello world  "})
print(f"输入: '  hello world  '")
print(f"输出: {result}")
print()

print("📚 演示 2: 脱敏敏感信息")
print("─"*50)

anonymize = create_atomic_skill(
    name="anonymize",
    description="脱敏",
    inputs={"text": "str"},
    outputs={"safe": "str"},
    implementation='''
import re
safe = re.sub(r"\\d{11}", "[PHONE]", inputs["text"])
safe = re.sub(r"\\w+@\\w+\\.\\w+", "[EMAIL]", safe)
'''
)

test = "联系张三，电话13812345678，邮箱zhangsan@example.com"
result = anonymize.execute({"text": test})
print(f"原始: {test}")
print(f"脱敏: {result['safe']}")
print()

print("📚 演示 3: 模型配置")
print("─"*50)

from src.models.providers.registry import get_registry
registry = get_registry(region="china")
print("✅ 模型注册表初始化成功")
print(f"   支持的模型: qwen-plus, deepseek-chat, glm-4")
print()

print("════════════════════════════════════════════════════════════════")
print("  ✅ 所有演示完成！")
print("════════════════════════════════════════════════════════════════")
EOF

# 运行演示
python3 /tmp/demo_skills.py

echo ""
echo "💡 更多示例和说明："
echo "  - 使用指南: .claude/skills/USAGE_GUIDE.md"
echo "  - 快速开始: .claude/skills/QUICK_START.md"
echo "  - 完整示例: examples/complete_workflow.py"
echo "  - 测试脚本: test_skills.py"
