# 🚀 Claude 自定义技能 - 快速参考

## ✅ 技能状态

| 技能 | 状态 | 测试 |
|------|------|------|
| Bootstrap Framework | ✅ 可用 | ✅ 通过 |
| Heterogeneous Training | ✅ 可用 | ✅ 通过 |
| Data Anonymization | ✅ 可用 | ✅ 通过 |

## 🎯 三种使用方式

### 方式 1: 直接提问（推荐）

```
问题示例:
✅ "使用 Bootstrap Framework 技能，创建一个数据验证技能"
✅ "按照 Heterogeneous Training 的方式配置模型"
✅ "使用 Data Anonymization 的策略脱敏这段文本"

Claude 会自动:
- 识别相关技能
- 参考技能定义
- 生成符合规范的代码
```

### 方式 2: 运行示例脚本

```bash
# 快速演示
bash examples/demo_skills.sh

# 完整示例
python examples/complete_workflow.py

# 测试技能
python test_skills.py
```

### 方式 3: 查阅技能文档

```bash
# 查看使用指南
cat .claude/skills/USAGE_GUIDE.md

# 查看快速开始
cat .claude/skills/QUICK_START.md

# 查看具体技能
cat .claude/skills/bootstrap-framework.md
cat .claude/skills/heterogeneous-training.md
cat .claude/skills/data-anonymization.md
```

## 💡 常用代码片段

### 创建技能

```python
from src.bootstrap import create_atomic_skill

skill = create_atomic_skill(
    name="your_skill_name",
    description="技能描述",
    inputs={"input_name": "str"},
    outputs={"output_name": "int"},
    implementation="output = len(inputs['input_name'])"
)

# 使用
result = skill.execute({"input_name": "test"})
```

### 配置模型

```python
from src.models.providers.registry import get_registry

registry = get_registry(region="china")
model = registry.create_model_instance("qwen-plus", temperature=0.7)
```

### 脱敏数据

```python
import re

def anonymize(text):
    # 手机号
    text = re.sub(r'1[3-9]\d{9}', lambda m: m.group()[:3] + '****' + m.group()[-4:], text)
    # 邮箱
    text = re.sub(r'\w+@\w+\.\w+', lambda m: m.group()[0] + '***@' + m.group().split('@')[1], text)
    return text
```

## 📁 文件位置

```
.claude/skills/
├── bootstrap-framework.md    # 自举框架技能
├── heterogeneous-training.md  # 异构训练技能
├── data-anonymization.md      # 数据脱敏技能
├── USAGE_GUIDE.md             # 详细使用指南 ⭐
├── QUICK_START.md             # 快速开始
└── README.md                  # 技能说明

examples/
├── complete_workflow.py       # 完整工作流示例
└── demo_skills.sh             # 快速演示脚本 ⭐

test_skills.py                 # 技能测试脚本
```

## 🧪 验证技能

```bash
# 一键测试
python test_skills.py

# 快速演示
bash examples/demo_skills.sh
```

## 📚 学习路径

1. **新手**: 运行 `bash examples/demo_skills.sh` 看效果
2. **入门**: 阅读 `.claude/skills/QUICK_START.md`
3. **进阶**: 阅读 `.claude/skills/USAGE_GUIDE.md`
4. **专家**: 查看具体技能文件学习最佳实践

## ⚡ 快速命令

```bash
# 查看所有技能
ls -lh .claude/skills/

# 运行演示
bash examples/demo_skills.sh

# 测试功能
python test_skills.py

# 查看指南
cat .claude/skills/USAGE_GUIDE.md
```

## 🎓 技能自动识别

Claude Code 会自动:
- ✅ 扫描 `.claude/skills/` 目录
- ✅ 读取技能定义
- ✅ 在对话中使用这些知识
- ✅ 生成符合规范的代码

无需额外配置，技能即开即用！

---

**提示**: 技能文件会自动生效，在与 Claude Code 对话时会自动使用这些知识。
