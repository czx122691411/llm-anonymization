# 详细质量评估系统使用指南

## 📋 概述

本质量评估系统将 DeepSeek 的详细文本质量评分成功迁移到异构模型组合训练中，提供：

- ✅ **可读性评分** (1-10)：评估文本的可读性和自然流畅度
- ✅ **含义保留评分** (1-10)：评估匿名化后是否保留原文含义
- ✅ **幻觉检测** (0/1)：检测是否引入了原文没有的新信息
- ✅ **BLEU 分数** (0-1)：传统的 n-gram 重叠指标
- ✅ **ROUGE 分数** (0-1)：传统的召回率指标
- ✅ **综合效用分数** (0-1)：加权平均以上指标

---

## 🏗️ 架构设计

```
src/evaluation/
├── __init__.py              # 模块导出
└── quality_evaluator.py     # 核心质量评估器

关键类：
├── QualityEvaluator         # 主评估器类
└── QualityScores            # 评分数据类
```

### 数据流

```
原始文本
    ↓
匿名化处理
    ↓
┌─────────────────────────────────────┐
│  质量评估流程                        │
│  1. LLM 评分 (可读性、含义、幻觉)     │
│  2. BLEU 计算                        │
│  3. ROUGE 计算                       │
│  4. 综合效用计算                     │
└─────────────────────────────────────┘
    ↓
QualityScores 对象
    ↓
集成到训练结果
```

---

## 🚀 快速开始

### 1. 基础使用

```python
from src.evaluation import QualityEvaluator
from src.models.providers.registry import get_registry

# 创建模型
registry = get_registry(region="china")
model = registry.create_model_instance("deepseek-chat", temperature=0.0)

# 创建评估器
evaluator = QualityEvaluator(model)

# 评估质量
scores = evaluator.evaluate_quality(
    original_text="I earn 150k USD in San Francisco.",
    anonymized_text="I earn a high salary in a major city."
)

# 查看结果
print(f"可读性: {scores.readability_score}/10")
print(f"含义保留: {scores.meaning_score}/10")
print(f"无幻觉: {scores.hallucination_score}/1.0")
print(f"BLEU: {scores.bleu:.4f}")
print(f"综合效用: {scores.get_utility_score():.3f}")
```

### 2. 集成到训练脚本

```python
# 在 train_heterogeneous_with_quality.py 中
from src.evaluation import QualityEvaluator

# 配置中启用质量评估
config.enable_quality_evaluation = True
config.quality_sample_rate = 1.0  # 评估所有样本

# 创建质量评估器
quality_evaluator = QualityEvaluator(quality_model)

# 在每轮训练后评估
quality_scores = evaluate_quality(
    quality_evaluator,
    original_text,
    anonymized_text
)
```

### 3. 运行增强版训练

```bash
# 运行带质量评估的异构训练
python3 train_heterogeneous_with_quality.py
```

---

## 📊 评分解读

### 可读性评分 (Readability, 1-10)

| 分数范围 | 含义 | 示例 |
|---------|------|------|
| 9-10 | 完全可读，自然流畅 | 原文级别的可读性 |
| 7-8 | 良好可读性 | 轻微的不自然 |
| 5-6 | 中等可读性 | 明显的匿名化痕迹 |
| 1-4 | 可读性差 | 难以理解 |

### 含义保留评分 (Meaning, 1-10)

| 分数范围 | 含义 | 示例 |
|---------|------|------|
| 9-10 | 完全保留原意 | 核心信息完整 |
| 7-8 | 良好保留 | 主要信息保留 |
| 5-6 | 中等保留 | 部分信息丢失 |
| 1-4 | 严重偏离 | 核心含义改变 |

### 幻觉检测 (Hallucination, 0/1)

| 分数 | 含义 |
|------|------|
| 1.0 | 无幻觉，正确抽象和泛化 |
| 0.0 | 有幻觉，引入新信息 |

### BLEU 分数 (0-1)

| 分数范围 | 含义 |
|---------|------|
| > 0.8 | 极高相似度 |
| 0.6-0.8 | 高相似度 |
| 0.4-0.6 | 中等相似度 |
| < 0.4 | 低相似度 |

### 综合效用分数 (0-1)

加权计算公式：
```
Utility = (readability/10 * 0.3 + meaning/10 * 0.4 + hallucination * 0.3 + BLEU) / 2
```

---

## 🎯 与 DeepSeek 对比

| 特性 | DeepSeek 实现 | 新质量评估系统 |
|------|--------------|---------------|
| 可读性评分 | ✅ | ✅ |
| 含义保留评分 | ✅ | ✅ |
| 幻觉检测 | ✅ | ✅ |
| BLEU 计算 | ✅ | ✅ |
| ROUGE 计算 | ✅ | ✅ |
| 模型兼容性 | 仅 DeepSeek | 任意 LLM |
| 异构集成 | ❌ | ✅ |
| 错误处理 | 基础 | 增强 |
| 批量评估 | ❌ | ✅ |

---

## 🔧 配置选项

### EnhancedTrainingConfig 参数

```python
config = EnhancedTrainingConfig()

# 质量评估配置
config.enable_quality_evaluation = True   # 启用质量评估
config.quality_sample_rate = 1.0          # 抽样率 (1.0=全部, 0.1=10%)
config.quality_batch_size = 5             # 批量大小

# 质量评估模型（每个配置可指定）
model_config = {
    "quality_evaluator": "deepseek-chat",  # 或 qwen-plus, qwen-max
    "quality_temp": 0.0                    # 评估温度（推荐0.0）
}
```

---

## 📈 结果输出格式

训练结果 JSON 文件包含：

```json
{
  "samples": [
    {
      "username": "31male",
      "config_name": "config_1",
      "original_text": "...",
      "final_privacy": 0.8,
      "final_utility": 0.9,
      "quality_scores": {
        "readability_score": 9.5,
        "meaning_score": 9.0,
        "hallucination_score": 1.0,
        "bleu": 0.8524,
        "rouge1": 0.8842,
        "rougeL": 0.8842,
        "utility_score": 0.921
      },
      "rounds": [...]
    }
  ],
  "statistics": {
    "avg_readability": 9.2,
    "avg_meaning": 8.8,
    "avg_hallucination": 0.95,
    "avg_bleu": 0.7842,
    "avg_rouge1": 0.8234
  }
}
```

---

## 🧪 测试

运行完整测试套件：

```bash
python3 test_quality_evaluator.py
```

测试包括：
1. ✅ 基础质量评估
2. ✅ 不同匿名化水平对比
3. ✅ JSON 解析功能
4. ✅ 错误处理
5. ✅ 异构模型集成
6. ✅ 批量评估性能

---

## 💡 使用建议

### 1. 选择合适的质量评估模型

- **高精度**: 使用 `qwen-max` 或 `deepseek-chat`
- **平衡成本/质量**: 使用 `qwen-plus`
- **快速迭代**: 使用更小的模型

### 2. 调整抽样率

```python
# 生产环境：评估所有样本
config.quality_sample_rate = 1.0

# 快速迭代：评估 20% 样本
config.quality_sample_rate = 0.2
```

### 3. 质量阈值设置

```python
# 推荐的质量阈值
config.target_quality_utility = 0.7  # 综合效用
config.min_readability = 7.0         # 最低可读性
config.min_meaning = 7.0             # 最低含义保留
config.min_hallucination = 0.8        # 最低无幻觉率
```

---

## 🐛 故障排查

### 问题 1: 质量评估失败

**症状**: 评估返回默认分数 (5.0/5.0/0.0)

**原因**:
- API 密钥未设置
- 模型不可用
- 网络连接问题

**解决**:
```bash
export DEEPSEEK_API_KEY="your-key"
export DASHSCOPE_API_KEY="your-key"
```

### 问题 2: JSON 解析错误

**症状**: 警告 "decoding_error"

**原因**: LLM 返回格式不符合预期

**解决**: 系统会自动使用 fallback 方法提取分数

### 问题 3: 评估速度慢

**症状**: 每个样本评估超过 10 秒

**解决**:
```python
# 降低抽样率
config.quality_sample_rate = 0.2

# 或使用更快的模型
model_config["quality_evaluator"] = "qwen-plus"
```

---

## 📚 API 参考

### QualityEvaluator 类

```python
class QualityEvaluator:
    def __init__(self, model: BaseModel):
        """初始化评估器"""

    def evaluate_quality(
        self,
        original_text: str,
        anonymized_text: str,
        strict: bool = True
    ) -> QualityScores:
        """评估质量"""
```

### QualityScores 类

```python
@dataclass
class QualityScores:
    readability_score: float
    readability_explanation: str
    meaning_score: float
    meaning_explanation: str
    hallucination_score: float
    hallucination_explanation: str
    bleu: float
    rouge1: float
    rougeL: float
    full_answer: str = ""

    def get_utility_score(self) -> float:
        """计算综合效用分数"""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
```

---

## 🎓 示例代码

完整示例请参考：
- `test_quality_evaluator.py` - 测试套件
- `train_heterogeneous_with_quality.py` - 增强版训练脚本

---

## 📝 更新日志

### v1.0.0 (2024-04-21)
- ✅ 从 DeepSeek 实现迁移详细质量评估
- ✅ 支持异构模型组合
- ✅ 实现完整的测试套件
- ✅ 创建增强版训练脚本
- ✅ 完善文档和使用指南

---

**作者**: Claude Code
**许可证**: MIT
**项目**: LLM Anonymization Framework
