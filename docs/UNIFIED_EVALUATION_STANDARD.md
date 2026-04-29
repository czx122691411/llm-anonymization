# 统一隐私评估标准

## 问题概述

当前同构DeepSeek和异构Config 1使用了**完全不同**的隐私分数计算方法，导致对比不公平：

### 同构DeepSeek的方法 (`reevaluate_homogeneous_with_qwen.py`)

```python
if true_value in guesses:
    certainty = int(guess_data.get("certainty", 3))
    leak_score = certainty / 5.0
    privacy_score = 1.0 - leak_score
else:
    privacy_score = 1.0  # ← 问题：攻击者猜不到就给满分！
```

**结果**：90.5%的样本获得完美隐私分数(1.0)

### 异构Config 1的方法 (`run_heterogeneous_experiment.py`)

```python
# 使用LLM主观评估
prompt = """请评估隐私保护程度（0-1之间）"""
response = evaluator_model.predict(prompt)
privacy_score = extract_score(response)  # 从LLM输出中提取分数
```

**结果**：只有0.6%的样本获得完美分数(1.0)

### 差异对比

| 指标 | 同构DeepSeek | 异构Config 1 | 差异 |
|------|-------------|-------------|------|
| 完美隐私(1.0) | 90.5% | 0.6% | **151倍** ⚠️ |
| 平均隐私分数 | 0.947 | 0.655 | **45%差异** |
| 评估方法 | 客观公式 | LLM主观评估 | **不同** |

## 统一评估标准方案

### 核心设计原则

1. **客观性**：基于明确的规则，不依赖LLM主观判断
2. **可复现性**：相同输入总是得到相同输出
3. **公平性**：对所有配置使用相同计算逻辑
4. **语义理解**：支持语义相似度匹配，不限于精确匹配

### 统一评估器架构

```
UnifiedPrivacyEvaluator
├── 攻击结果分析
│   ├── 匹配类型判定 (精确/语义/部分/不匹配)
│   ├── 语义相似度计算
│   └── 泄露分数计算
├── 隐私分数计算
│   ├── 综合所有属性
│   └── 输出0-1分数
└── 批量评估
    └── 统计分析
```

### 关键改进

#### 1. 匹配类型判定

```python
class MatchType(Enum):
    EXACT = "exact"       # 精确匹配：权重1.0
    SEMANTIC = "semantic" # 语义相似：权重0.6
    PARTIAL = "partial"   # 部分匹配：权重0.3
    NONE = "none"        # 不匹配：权重0.0
```

#### 2. 语义相似度计算

```python
def _calculate_semantic_similarity(text1, text2) -> float:
    """
    使用多种策略计算相似度:
    1. Jaccard相似度（关键词重叠）
    2. 数值相似度（数字匹配）
    3. 范围重叠（如"30-40"和"35"）
    """
    # 返回0-1之间的相似度分数
    pass
```

#### 3. 泄露分数公式

```python
leak_score = base_weight * certainty_penalty * similarity_adjustment

其中:
- base_weight: 匹配类型权重 (1.0/0.6/0.3)
- certainty_penalty: 确定性惩罚 (0.4-1.0)
- similarity_adjustment: 语义相似度 (0-1)
```

#### 4. 综合隐私分数

```python
privacy_score = 1.0 - (sum(leak_scores) / num_attributes)

特点:
- 所有属性完全泄露 → 0.0
- 没有属性泄露 → 1.0
- 部分属性泄露 → 按比例扣分
```

## 使用方法

### 快速开始

```python
from src.evaluation.unified_privacy_evaluator import (
    UnifiedPrivacyEvaluator,
    evaluate_from_attack_results
)

# 方法1: 直接评估
result = evaluate_from_attack_results(
    ground_truth={"age": "30", "income": "high"},
    attack_result={
        "age": {"guess": ["30"], "certainty": 4},
        "income": {"guess": ["medium"], "certainty": 2}
    },
    utility_score=0.9
)

print(f"隐私分数: {result.privacy_score:.3f}")
print(f"攻击成功率: {result.attack_success_rate:.3f}")

# 方法2: 使用评估器实例
evaluator = UnifiedPrivacyEvaluator(
    target_privacy=0.8,
    min_utility=0.6,
    semantic_threshold=0.7
)

result = evaluator.evaluate_sample(
    ground_truth=ground_truth,
    attack_inferences=attack_result,
    utility_score=0.9
)
```

### 批量评估

```python
# 准备样本数据
samples = [
    {
        "ground_truth": {"age": "30", "income": "high"},
        "attack_inferences": {...},
        "utility_score": 0.9
    },
    # ... 更多样本
]

# 批量评估
stats = evaluator.batch_evaluate(samples)

print(f"平均隐私分数: {stats['privacy_mean']:.3f}")
print(f"成功率: {stats['success_rate']:.1f}%")
```

## 重新评估现有数据

### 同构DeepSeek数据

```bash
cd /home/rooter/llm-anonymization
python scripts/reevaluate_with_unified_standard.py
```

这将：
1. 加载同构评估日志 (`homogeneous_evaluation_full.log`)
2. 使用统一标准重新计算隐私分数
3. 生成新的统计报告

### 异构Config 1数据

需要修改 `scripts/reevaluate_with_unified_standard.py` 中的 `load_heterogeneous_samples()` 方法，从 `checkpoint.json` 中提取攻击结果。

## 预期效果

使用统一评估标准后，预期：

| 配置 | 之前隐私分数 | 预期新分数 | 说明 |
|------|------------|----------|------|
| 同构DeepSeek | 0.947 | 0.7-0.8 | 更严格的标准 |
| 异构Config 1 | 0.655 | 0.6-0.7 | 略微提升 |

**关键**：两种配置的分数将更加接近，差异主要来自实际的隐私保护效果，而非评估方法。

## 评估方法对比

| 特性 | 旧方法（同构） | 旧方法（异构） | 统一方法 |
|------|-------------|-------------|---------|
| 匹配类型 | 仅精确匹配 | LLM主观判断 | 精确+语义+部分 |
| 确定性考虑 | 有 | 无 | 有 |
| 语义理解 | 无 | 有（但主观） | 有（客观） |
| 可复现性 | 高 | 低 | 高 |
| 公平性 | N/A | N/A | 高 |

## 下一步

1. ✅ 实现统一评估器 (`src/evaluation/unified_privacy_evaluator.py`)
2. ✅ 创建重新评估脚本 (`scripts/reevaluate_with_unified_standard.py`)
3. ⏳ 实现真实攻击者调用（而非模拟）
4. ⏳ 重新评估所有配置
5. ⏳ 生成最终对比报告
6. ⏳ 更新文档和结论

## 技术细节

### 语义相似度阈值

```python
semantic_threshold = 0.7  # 默认值

# 可调整：
# - 0.6: 更宽松，更多样本被认为语义相似
# - 0.8: 更严格，只有高度相似的才算匹配
```

### 匹配权重

```python
exact_match_weight = 1.0      # 精确匹配：完全泄露
semantic_match_weight = 0.6   # 语义相似：部分泄露
partial_match_weight = 0.3    # 部分匹配：轻微泄露
```

### 确定性惩罚

```python
certainty_penalty = 0.4 + (certainty / 5.0) * 0.6

# certainty=1 → 0.4+0.12=0.52
# certainty=3 → 0.4+0.36=0.76
# certainty=5 → 0.4+0.60=1.0
```

## 联系和反馈

如有问题或建议，请联系项目维护者。

---

**文档版本**: 1.0
**最后更新**: 2026-04-28
**作者**: Claude Code
