# 攻击反馈驱动的对抗训练 - 完整文档

## 概述

增强版的对抗训练实现了**攻击反馈驱动的防御改进**机制，使防御者能够根据上一轮的攻击结果动态调整匿名化策略。

## 核心改进

### 1. 攻击反馈生成 (`_generate_improvement_feedback`)

**功能**: 分析上一轮攻击结果，生成详细的改进反馈

**反馈内容包括**:

```python
# 严重泄露警告
⚠️ 严重隐私泄露:
  - 属性 'age': 真实值 '30' 被准确猜出为 '30' (确定性: 5/5)
  → 必须更激进地泛化或完全移除这些信息！

# 部分泄露警告
⚡ 部分隐私泄露:
  - 属性 'location': 攻击者猜测 '北京' (真实值: 'Beijing, China', 确定性: 3/5)
  → 需要加强匿名化，攻击者已接近真实值。

# 保护成功确认
✓ 保护成功:
  - 属性: income, education
  → 请保持这种保护水平。

# 效用评估
📊 当前效用分数: 0.75/1.0
  → 效用良好，可以进一步加强隐私保护。

# 改进建议
📋 改进建议:
  1. 隐私保护较弱，需要加强匿名化
  2. 使用更模糊的词汇替代具体信息
  3. 改写句子结构以掩盖语义线索
```

### 2. 反馈驱动的防御prompt

**第一轮（初始匿名化）**:
```
你是一位专业的文本匿名化专家。
你的任务是对评论进行匿名化处理。

需要保护的属性: age, location, income

原始文本:
[用户评论]

请对上述文本进行匿名化，要求:
1. 移除或泛化与上述属性相关的具体信息
2. 保持文本的自然流畅和语义
```

**第二轮及以后（包含攻击反馈）**:
```
你是一位专业的文本匿名化专家。
下面是同一组评论。你之前的匿名化受到了攻击。

攻击反馈:
⚠️ 严重隐私泄露:
  - 属性 'age': 真实值 '30' 被准确猜出 (确定性: 5/5)
  → 必须更激进地泛化这些信息！

📊 当前隐私分数: 0.35/1.0
📊 攻击成功率: 85.0%

请根据上述反馈改进匿名化，更好地保护隐私。

改进要求:
1. 针对反馈中指出的泄露问题，加强匿名化
2. 将具体信息替换为更通用的表述
3. 必要时可以完全删除敏感句子
```

### 3. 多轮对抗循环

```
┌─────────────────────────────────────────────────────┐
│  Round 1: 初始匿名化                                │
│  ├─ 防御者: 首次匿名化                              │
│  ├─ 攻击者: 尝试推断属性                            │
│  ├─ 评估器: 计算隐私分数 (0.35)                     │
│  └─ 生成反馈: "age属性严重泄露"                     │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Round 2: 反馈驱动改进                              │
│  ├─ 反馈: "age被准确猜出，必须加强匿名化"           │
│  ├─ 防御者: 根据反馈重新匿名化                      │
│  ├─ 攻击者: 再次尝试推断                            │
│  ├─ 评估器: 计算隐私分数 (0.72) ← 改善！            │
│  └─ 生成反馈: "保护改善，继续加强"                  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Round 3: 持续优化                                  │
│  ├─ 反馈: "隐私保护良好，继续保持"                  │
│  ├─ 防御者: 微调匿名化策略                          │
│  ├─ 攻击者: 最后一次尝试                            │
│  └─ 评估器: 隐私分数 0.91 ✓ 达到目标！              │
└─────────────────────────────────────────────────────┘
```

## 与原有框架的对比

| 方面 | 原有 `adversarial.py` | 简化版 | **增强版（当前）** |
|------|---------------------|--------|-------------------|
| **攻击反馈** | ✅ 有 | ❌ 无 | ✅ **增强版** |
| **反馈详细度** | 简单文本 | N/A | **结构化分析** |
| **隐私评估** | LLM主观 | UnifiedEvaluator | **UnifiedEvaluator** |
| **数据结构** | Profile对象 | dict | **dict + AdversarialRoundResult** |
| **反馈分类** | 无 | N/A | **严重/部分/保护成功** |

## 增强版反馈机制的特点

### 1. 精确的泄露分类

```python
if true_value in guesses:
    # 严重泄露: 攻击者准确猜出真实值
    leaked_attrs.append({
        "attr": attr,
        "true_value": true_value,
        "guessed_value": guesses[0],
        "certainty": certainty
    })
elif any(str(true_value).lower() in str(g).lower() for g in guesses):
    # 部分泄露: 攻击者接近真实值
    partially_leaked_attrs.append(...)
else:
    # 保护成功
    protected_attrs.append(attr)
```

### 2. 分级改进建议

```python
if privacy_score < 0.5:
    建议 = [
        "1. 隐私保护严重不足，必须大幅修改文本",
        "2. 将具体信息替换为非常通用的表述",
        "3. 考虑完全删除包含敏感信息的句子"
    ]
elif privacy_score < 0.7:
    建议 = [
        "1. 隐私保护较弱，需要加强匿名化",
        "2. 使用更模糊的词汇替代具体信息",
        "3. 改写句子结构以掩盖语义线索"
    ]
else:
    建议 = [
        "1. 隐私保护良好，继续保持当前策略",
        "2. 微调尚未完全保护的属性"
    ]
```

### 3. 效用感知的反馈

```python
if utility_score >= 0.7:
    反馈 += "→ 效用良好，可以进一步加强隐私保护。"
elif utility_score >= 0.5:
    反馈 += "→ 效用可接受，需要在隐私保护和文本质量之间平衡。"
else:
    反馈 += "→ 效用较低，注意不要过度匿名化导致文本失真。"
```

## 使用方法

### 1. 本地测试

```bash
# 使用测试配置（5个样本）
cd /root/llm-anonymization
export DASHSCOPE_API_KEY='your_key'
export DEEPSEEK_API_KEY='your_key'

python3 test_feedback_training.py
```

### 2. 完整训练

```bash
# 修改配置文件中的 num_profiles
# 然后运行:
python3 scripts/run_unified_training_with_feedback.py --config homogeneous
```

### 3. 云服务器部署

```bash
# 上传脚本
scp scripts/run_unified_training_with_feedback.py root@server:/root/llm-anonymization/scripts/

# 创建启动脚本
cat > start_training.sh << 'EOF'
#!/bin/bash
export DASHSCOPE_API_KEY='sk-xxx'
export DEEPSEEK_API_KEY='sk-xxx'
cd /root/llm-anonymization
python3 scripts/run_unified_training_with_feedback.py --config both > training.log 2>&1
EOF

# 后台运行
nohup bash start_training.sh &
```

## 输出格式

每个样本的结果包含：

```json
{
    "username": "sample_123",
    "rounds": [
        {
            "round": 1,
            "anonymized_text": "匿名化后的文本...",
            "attack_inferences": {
                "age": {
                    "inference": "根据语气判断...",
                    "guess": ["30-40岁"],
                    "certainty": 3
                }
            },
            "privacy_score": 0.65,
            "utility_score": 0.82,
            "attack_success_rate": 0.33,
            "success": false
        },
        {
            "round": 2,
            "anonymized_text": "改进后的匿名化文本...",
            "attack_inferences": {
                "age": {
                    "inference": "难以确定...",
                    "guess": ["中年"],
                    "certainty": 1
                }
            },
            "privacy_score": 0.92,
            "utility_score": 0.78,
            "attack_success_rate": 0.0,
            "success": true
        }
    ],
    "final_privacy": 0.92,
    "final_utility": 0.78,
    "final_success": true,
    "total_rounds": 2
}
```

## 测试结果

```
总样本数: 5
成功样本数: 4
成功率: 80.0%

隐私分数: 1.000 ± 0.000
效用分数: 0.726 ± 0.250

耗时: 5.8 分钟
```

## 关键优势

| 优势 | 说明 |
|------|------|
| **智能反馈** | 精确识别泄露类型，提供针对性建议 |
| **渐进改进** | 每轮基于上轮结果动态调整 |
| **效用平衡** | 在加强隐私保护的同时保持文本质量 |
| **统一评估** | 使用UnifiedPrivacyEvaluator确保公平对比 |
| **可解释性** | 详细的反馈日志便于分析训练过程 |

## 下一步优化方向

1. **自适应反馈强度**: 根据泄露严重程度调整反馈的激进程度
2. **历史反馈整合**: 考虑多轮反馈的累积效果
3. **多属性关联分析**: 识别属性间的语义关联导致的泄露
4. **反馈模板库**: 针对不同类型的泄露提供专门的反馈模板
