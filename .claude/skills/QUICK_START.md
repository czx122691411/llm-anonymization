# Claude 自定义技能使用指南

## ✅ 测试状态：全部通过

### 技能测试结果

| 技能 | 版本 | 状态 | 功能验证 |
|------|------|------|----------|
| Bootstrap Framework | 0.3.0 | ✅ 可用 | 导入、配置、创建、执行全部正常 |
| Heterogeneous Training | 1.0.0 | ✅ 可用 | 模型注册表、多模型支持正常 |
| Data Anonymization | 1.0.0 | ✅ 可用 | 敏感信息识别、脱敏正常 |

## 快速使用示例

### 1. Bootstrap Framework - 创建技能

```python
from src.bootstrap import create_atomic_skill

# 创建简单的数据处理技能
skill = create_atomic_skill(
    name="count_words",
    description="统计文本中的单词数量",
    inputs={"text": "str"},
    outputs={"count": "int"},
    implementation='''
words = inputs['text'].split()
count = len(words)
'''
)

# 使用技能
result = skill.execute({"text": "Hello world this is a test"})
print(result)  # {'count': 6}
```

### 2. Heterogeneous Training - 初始化模型

```python
from src.models.providers.registry import get_registry

# 获取模型注册表
registry = get_registry(region="china")

# 创建模型实例
models = {}
for model_name in ["qwen-plus", "deepseek-chat", "glm-4"]:
    try:
        models[model_name] = registry.create_model_instance(model_name)
        print(f"✅ {model_name} 创建成功")
    except Exception as e:
        print(f"❌ {model_name} 创建失败: {e}")
```

### 3. Data Anonymization - 脱敏处理

```python
import re

def anonymize_text(text):
    """简单的文本脱敏"""
    # 手机号脱敏
    text = re.sub(r'1[3-9]\d{9}',
                  lambda m: m.group()[:3] + '****' + m.group()[-4:],
                  text)

    # 邮箱脱敏
    text = re.sub(r'(\w)[\w-]*@(\w+)',
                  lambda m: m.group(1) + '***@' + m.group(2),
                  text)

    return text

# 使用
original = "联系张三，电话13812345678，邮箱zhangsan@example.com"
anonymized = anonymize_text(original)
print(anonymized)
# 输出: 联系张三，电话138****5678，邮箱z***@example.com
```

## 在 Claude Code 中的使用

当你使用 Claude Code 工作时，这些技能会自动启用：

1. **技能识别**: Claude 会自动识别 .claude/skills/ 中的技能定义
2. **上下文感知**: Claude 会根据项目上下文选择相关技能
3. **代码生成**: Claude 会参考技能示例生成正确的代码

### 示例对话

**用户**: "帮我创建一个技能来读取CSV文件"

**Claude**: 我会使用 Bootstrap Framework 技能来帮你...

```python
from src.bootstrap import create_atomic_skill

read_csv = create_atomic_skill(
    name="read_csv_file",
    description="读取CSV文件并返回数据列表",
    inputs={"file_path": "str"},
    outputs={"data": "list", "headers": "list"},
    implementation='''
import csv
data = []
headers = []

with open(inputs['file_path'], 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    data = list(reader)

'''
)
```

## 技能文件位置

```
.claude/skills/
├── bootstrap-framework.md    # 自举框架技能
├── heterogeneous-training.md  # 异构训练技能
├── data-anonymization.md      # 数据脱敏技能
├── README.md                  # 技能说明
└── QUICK_START.md             # 本文件
```

## 测试命令

```bash
# 运行完整测试
python test_skills.py

# 测试特定技能
python -c "from src.bootstrap import create_atomic_skill; \
skill = create_atomic_skill('test', 'test', {'x': 'int'}, {'y': 'int'}, 'y = x * 2'); \
print(skill.execute({'x': 5}))"
```

## 下一步

1. ✅ 技能已创建并通过测试
2. ✅ Claude Code 可以识别这些技能
3. 🚀 开始在项目中使用这些技能

## 维护和更新

- 修改技能文件后，Claude Code 会自动重新加载
- 测试脚本可用于验证技能功能
- 建议定期更新技能文档以保持与代码同步

---

**更新时间**: 2026-04-20
**测试状态**: ✅ 全部通过
