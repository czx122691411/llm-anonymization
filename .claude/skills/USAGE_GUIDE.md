# Claude 自定义技能使用指南

## 🎯 技能工作原理

### 自动识别机制

Claude Code 会在启动时自动扫描 `.claude/skills/` 目录，读取所有 `.md` 文件中的技能定义，并在后续对话中使用这些知识来：

1. **理解项目架构**: 知道项目有哪些核心模块
2. **生成正确代码**: 参考技能中的代码示例
3. **遵循最佳实践**: 按照技能定义的方式处理问题
4. **提供精准建议**: 基于项目特定的功能模块

## 📖 实际使用场景

### 场景 1: 开发新技能

**你的问题**: "帮我创建一个读取CSV文件的技能"

**Claude 的回答**（基于 bootstrap-framework 技能）:

```python
from src.bootstrap import create_atomic_skill

# 使用 Bootstrap Framework 的技能定义方式
read_csv_skill = create_atomic_skill(
    name="read_csv_file",
    description="读取CSV文件并返回数据和表头",
    inputs={"file_path": "str"},
    outputs={"data": "list", "headers": "list", "row_count": "int"},
    implementation='''
import csv

data = []
headers = []
row_count = 0

with open(inputs['file_path'], 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames if reader.fieldnames else []
    data = list(reader)
    row_count = len(data)

'''
)

# 使用技能
result = read_csv_skill.execute({"file_path": "data.csv"})
print(f"读取了 {result['row_count']} 行数据")
```

### 场景 2: 配置异构训练

**你的问题**: "我需要配置3个模型的异构训练"

**Claude 的回答**（基于 heterogeneous-training 技能）:

```python
from src.models.providers.registry import get_registry

# 使用 Heterogeneous Training 的模型配置方式
registry = get_registry(region="china")

# 配置要使用的模型
model_configs = [
    {"name": "qwen-plus", "temperature": 0.7},
    {"name": "deepseek-chat", "temperature": 0.8},
    {"name": "glm-4", "temperature": 0.6}
]

# 创建模型实例
models = []
for config in model_configs:
    try:
        model = registry.create_model_instance(
            config["name"],
            temperature=config["temperature"]
        )
        models.append(model)
        print(f"✅ {config['name']} 创建成功")
    except Exception as e:
        print(f"❌ {config['name']} 创建失败: {e}")

# 现在可以进行异构训练
```

### 场景 3: 数据脱敏处理

**你的问题**: "处理用户数据时需要脱敏手机号和邮箱"

**Claude 的回答**（基于 data-anonymization 技能）:

```python
import re
from typing import Dict, Any

def anonymize_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用 Data Anonymization 技能定义的脱敏策略
    """
    result = data.copy()

    # 手机号脱敏（保留前3后4位）
    if 'phone' in result:
        phone = result['phone']
        result['phone'] = phone[:3] + '****' + phone[-4:]

    # 邮箱脱敏（保留首字母和域名）
    if 'email' in result:
        email = result['email']
        name, domain = email.split('@')
        result['email'] = name[0] + '***@' + domain

    # 身份证脱敏（保留前6后4位）
    if 'id_card' in result:
        id_card = result['id_card']
        result['id_card'] = id_card[:6] + '********' + id_card[-4:]

    return result

# 使用示例
user_data = {
    "name": "张三",
    "phone": "13812345678",
    "email": "zhangsan@example.com",
    "id_card": "110101199001011234"
}

anonymized = anonymize_user_data(user_data)
print(anonymized)
# {'name': '张三', 'phone': '138****5678', 'email': 'z***@example.com',
#  'id_card': '110101********1234'}
```

## 🔄 完整工作流程示例

### 示例：构建一个完整的自举循环

```python
#!/usr/bin/env python3
"""
完整的自举循环示例
结合 Bootstrap Framework 和 Data Anonymization 技能
"""

import asyncio
from src.bootstrap import (
    BootstrapEngine,
    BootstrapConfig,
    create_atomic_skill
)
from src.models.providers.registry import get_registry

async def main():
    # 1. 创建种子技能（使用 Bootstrap Framework 方式）
    seed_skills = [
        create_atomic_skill(
            name="anonymize_text",
            description="对文本中的敏感信息进行脱敏",
            inputs={"text": "str"},
            outputs={"anonymized_text": "str"},
            implementation='''
import re

anonymized_text = inputs["text"]

# 手机号脱敏
anonymized_text = re.sub(
    r"1[3-9]\d{9}",
    lambda m: m.group()[:3] + "****" + m.group()[-4:],
    anonymized_text
)

# 邮箱脱敏
anonymized_text = re.sub(
    r"\w+@\w+\.\w+",
    lambda m: m.group()[0] + "***@" + m.group().split("@")[1],
    anonymized_text
)
'''
        ),
        create_atomic_skill(
            name="validate_phone",
            description="验证手机号格式",
            inputs={"phone": "str"},
            outputs={"is_valid": "bool"},
            implementation='''
import re
is_valid = bool(re.match(r"^1[3-9]\d{9}$", inputs["phone"]))
'''
        )
    ]

    # 2. 初始化配置
    config = BootstrapConfig(
        storage_path="./anonymization_skills",
        target_quality=0.85,
        max_iterations=3,
        enable_auto_testing=True
    )

    # 3. 初始化 LLM（使用 Heterogeneous Training 的模型配置）
    registry = get_registry(region="china")
    llm_client = registry.create_model_instance("qwen-plus", temperature=0.7)

    # 4. 创建自举引擎
    engine = BootstrapEngine(config, llm_client)

    # 5. 运行自举循环
    objective = """
    构建数据脱敏相关的技能库，包括：
    - 敏感信息识别能力
    - 多种脱敏策略
    - 数据格式保持
    - 批量处理能力
    - 质量验证能力
    """

    result = await engine.run_bootstrap_cycle(
        objective=objective,
        max_iterations=3
    )

    # 6. 查看结果
    print(f"✅ 生成新技能: {result.total_new_skills}")
    print(f"✅ 平均质量: {result.final_avg_quality:.2f}")
    print(f"✅ 平均成功率: {result.final_avg_success_rate:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 💡 使用技巧

### 1. 明确引用技能

在提问时明确提到相关技能，Claude 会更精准地使用相关知识：

```
✅ 好的提问方式：
"使用 Bootstrap Framework 技能，帮我创建一个XX技能"
"按照 Heterogeneous Training 的配置方式，设置模型"

❌ 不够明确的提问：
"帮我创建一个技能"
"配置一下模型"
```

### 2. 利用代码示例

技能文件中包含大量代码示例，可以直接参考或修改：

```bash
# 查看技能文件中的代码示例
cat .claude/skills/bootstrap-framework.md | grep -A 20 "### 1. 基础训练配置"
```

### 3. 组合使用技能

多个技能可以组合使用来解决复杂问题：

```python
# 组合示例：数据处理 + 脱敏 + 训练
from src.bootstrap import create_atomic_skill
import re

# 技能1: 数据清洗
clean_data = create_atomic_skill(
    "clean_data",
    "清洗数据",
    {"raw": "str"},
    {"cleaned": "str"},
    "cleaned = inputs['raw'].strip()"
)

# 技能2: 脱敏
anonymize = create_atomic_skill(
    "anonymize",
    "脱敏",
    {"text": "str"},
    {"safe": "str"},
    '''safe = re.sub(r'\\d{11}', '[PHONE]', inputs['text'])'''
)

# 组合使用
def process_pipeline(raw_data):
    # 步骤1: 清洗
    cleaned = clean_data.execute({"raw": raw_data})["cleaned"]
    # 步骤2: 脱敏
    safe = anonymize.execute({"text": cleaned})["safe"]
    return safe
```

## 🔧 调试和验证

### 验证技能是否生效

```python
# 测试技能是否被正确识别
python -c "
from src.bootstrap import create_atomic_skill
skill = create_atomic_skill('test', 'test', {'x': 'int'}, {'y': 'int'}, 'y = x * 2')
print('✅ Bootstrap Framework 技能正常')
print(f'结果: {skill.execute({\"x\": 5})}')
"

from src.models.providers.registry import get_registry
registry = get_registry(region='china')
print('✅ Heterogeneous Training 技能正常')

import re
text = '13812345678'
masked = re.sub(r'1[3-9]\\d{9}', lambda m: m.group()[:3] + '****' + m.group()[-4:], text)
print('✅ Data Anonymization 技能正常')
print(f'脱敏结果: {masked}')
```

### 查看技能加载状态

```bash
# 检查技能文件
ls -lh .claude/skills/

# 验证技能格式
for file in .claude/skills/*.md; do
    echo "检查: $file"
    head -10 "$file" | grep -E "^(name:|description:|version:)"
done
```

## 📚 进阶使用

### 1. 扩展技能定义

根据项目需要，可以添加新的技能文件：

```bash
# 创建新技能
nano .claude/skills/your-custom-skill.md
```

### 2. 更新现有技能

定期更新技能文件以保持与代码同步：

```bash
# 更新版本号
vim .claude/skills/bootstrap-framework.md

# 添加新的代码示例
```

### 3. 技能测试

使用提供的测试脚本验证技能功能：

```bash
# 运行完整测试
python test_skills.py

# 测试特定功能
python -c "from src.bootstrap import *; ..."
```

## 🎓 学习路径

1. **初学者**: 从 QUICK_START.md 开始，运行基本示例
2. **进阶**: 阅读完整的技能定义文件，理解各项功能
3. **专家**: 参考技能文件中的最佳实践，自定义开发

## 💬 与 Claude 的交互示例

### 优秀提问示例

```
Q1: "使用 Bootstrap Framework 技能定义的方式，创建一个数据验证技能"
Q2: "参考 Heterogeneous Training 的模型配置，帮我设置5个模型的并行训练"
Q3: "按照 Data Anonymization 的脱敏策略，处理这个用户数据"
Q4: "结合 Bootstrap 和 Anonymization 两个技能，构建一个隐私保护的数据处理流程"
```

### 避免的提问方式

```
❌ "写个函数"
❌ "怎么训练"
❌ "脱敏怎么做"
```

## 📞 获取帮助

- 查看技能文件: `.claude/skills/*.md`
- 运行测试: `python test_skills.py`
- 参考文档: `CLAUDE.md`
- 快速开始: `.claude/skills/QUICK_START.md`

---

**记住**: 这些技能文件已经就绪，当你与 Claude Code 交互时，它会自动使用这些知识来提供更准确、更符合项目规范的答案和代码。
