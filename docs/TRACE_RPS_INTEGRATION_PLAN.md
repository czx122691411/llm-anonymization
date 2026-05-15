# TRACE-RPS 集成改进策略

> **目标**: 将 TRACE-RPS (ICLR 2026) 的核心思想集成到当前异构多模型对抗匿名化框架中
>
> **日期**: 2026-04-29

---

## 1. 现状分析

### 当前项目 (LLM Anonymization)

| 配置 | 防御模型 | 攻击模型 | 隐私分数 | 效用分数 | 成功率 |
|------|----------|----------|----------|----------|--------|
| 同构 DeepSeek | deepseek-reasoner | deepseek-reasoner | 0.582 | 0.229 | 58.2% |
| 异构配置 1 | qwen-plus | deepseek-reasoner | **0.655** | **0.916** | **70.0%** |
| 异构配置 2 | qwen-plus | qwen-plus | 0.406 | 0.963 | 30.9% |

**问题**:
- 最佳配置仍有 ~35% 隐私泄露
- 缺乏细粒度的隐私元素识别
- 没有显式的推理预防机制

### TRACE-RPS 核心技术

| 组件 | 功能 | 效果 |
|------|------|------|
| **TRACE** | 基于注意力的细粒度匿名化 | 识别并替换隐私泄露词汇 |
| **RPS** | 推理预防优化 | 诱导模型拒绝推断敏感属性 |
| **联合** | TRACE + RPS | 属性推断准确率: 50% → <5% |

---

## 2. 改进策略框架

```
┌─────────────────────────────────────────────────────────────────┐
│                    增强型异构对抗匿名化框架                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │  输入文本        │───→│  TRACE 模块       │                    │
│  │  (用户生成内容)   │    │  (细粒度识别)      │                    │
│  └─────────────────┘    └────────┬─────────┘                    │
│                                   │                              │
│                                   ▼                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           隐私元素提取 (注意力机制)                        │   │
│  │  • 年龄、性别、地点、职业等敏感属性                         │   │
│  │  • 基于 LLM 的推理链分析                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                   │                              │
│                                   ▼                              │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │  异构防御模型     │◄───│  匿名化重写       │                    │
│  │  (qwen-plus)    │    │  (TRACE 输出)     │                    │
│  └────────┬────────┘    └──────────────────┘                    │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           RPS 优化模块 (推理预防)                          │   │
│  │  • 两阶段对抗训练                                          │   │
│  │  • 拒绝行为诱导                                           │   │
│  │  • 属性推断防御                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │  异构攻击模型     │───→│  属性推断评估      │                    │
│  │  (deepseek)      │    │  (隐私泄露检测)    │                    │
│  └─────────────────┘    └──────────────────┘                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 具体实施方案

### Phase 1: TRACE 模块集成

**目标**: 实现细粒度隐私元素识别和匿名化

```python
# src/defense/trace_anonymizer.py

class TRACEAnonymizer:
    """
    基于 TRACE 的细粒度匿名化器
    使用注意力机制和推理链识别隐私元素
    """

    def __init__(self, analyzer_model: str = "qwen-max"):
        self.analyzer = analyzer_model
        self.privacy_vocab = {
            "age": [],      # 年龄相关词汇
            "gender": [],   # 性别相关词汇
            "location": [], # 地点相关词汇
            "occupation": [], # 职业相关词汇
        }

    async def extract_privacy_elements(self, text: str) -> Dict[str, List[Span]]:
        """
        使用注意力机制提取隐私元素

        步骤:
        1. 获取模型的注意力权重
        2. 识别与隐私属性相关的token
        3. 生成推理链确认隐私泄露
        """
        attention_weights = await self._get_attention_weights(text)
        privacy_spans = await self._identify_privacy_spans(attention_weights)
        cot_analysis = await self._generate_cot_analysis(text, privacy_spans)

        return self._merge_analysis(privacy_spans, cot_analysis)

    async def anonymize_with_trace(self, text: str) -> Tuple[str, Dict]:
        """
        TRACE 风格的细粒度匿名化
        """
        privacy_elements = await self.extract_privacy_elements(text)

        anonymized_text = text
        for attr_type, spans in privacy_elements.items():
            for span in spans:
                replacement = self._generate_replacement(span, attr_type)
                anonymized_text = anonymized_text.replace(span.text, replacement)

        return anonymized_text, {
            "privacy_elements": privacy_elements,
            "anonymization_count": sum(len(v) for v in privacy_elements.values())
        }
```

**配置文件**:
```yaml
# configs/anonymization/trace_heterogeneous.yaml

defense:
  model: qwen-plus
  trace_enabled: true
  trace_config:
    attention_threshold: 0.3
    privacy_attributes:
      - age
      - gender
      - location
      - occupation
      - relationship_status
    cot_depth: 3  # 推理链深度

attack:
  model: deepseek-reasoner
  attribute_inference: true

evaluation:
  metrics:
    - privacy_leakage_rate
    - utility_preservation
    - attribute_inference_accuracy
```

### Phase 2: RPS 优化集成

**目标**: 实现推理预防优化，诱导模型拒绝属性推断

```python
# src/defense/rps_optimizer.py

class RPSOptimizer:
    """
    推理预防系统 (RPS)
    两阶段优化策略诱导拒绝行为
    """

    def __init__(self, defender_model: str, attacker_model: str):
        self.defender = defender_model
        self.attacker = attacker_model

    async def two_stage_optimization(self, text: str, anonymized_text: str):
        """
        两阶段优化
        """
        # Stage 1: 拒绝诱导训练
        refusal_prompts = self._generate_refusal_prompts(anonymized_text)

        # Stage 2: 属性推断防御
        defense_examples = await self._generate_defense_examples(
            text, anonymized_text
        )

        return {
            "refusal_prompts": refusal_prompts,
            "defense_examples": defense_examples
        }

    def _generate_refusal_prompts(self, text: str) -> List[str]:
        """
        生成诱导拒绝的提示词
        """
        templates = [
            "Based on the text, the user's age cannot be determined.",
            "The text does not contain sufficient information to infer gender.",
            "Privacy considerations prevent attribute inference from this text.",
        ]
        return [f"{text}\n\nQ: Can you infer {attr}?\nA: {tpl}"
                for attr, tpl in zip(["age", "gender", "location"], templates)]

    async def evaluate_inference_resistance(self, text: str) -> Dict:
        """
        评估对属性推断的抵抗力
        """
        inference_attempts = await self._attempt_inference(text)

        return {
            "inference_blocked": sum(1 for x in inference_attempts if x["blocked"]),
            "inference_total": len(inference_attempts),
            "resistance_rate": sum(1 for x in inference_attempts if x["blocked"]) / len(inference_attempts)
        }
```

### Phase 3: 统一评估框架

```python
# src/evaluation/unified_trace_evaluator.py

class TRACERespEvaluator:
    """
    TRACE-RPS 统一评估器
    """

    async def evaluate(self, original: str, anonymized: str) -> Dict:
        """
        综合评估
        """
        return {
            # TRACE 指标
            "privacy_coverage": await self._check_coverage(anonymized),
            "fine_grained_accuracy": await self._check_fine_grained(original, anonymized),

            # RPS 指标
            "inference_resistance": await self._check_inference_resistance(anonymized),
            "refusal_rate": await self._check_refusal_rate(anonymized),

            # 传统指标
            "utility_score": await self._check_utility(original, anonymized),
            "quality_score": await self._check_quality(anonymized),
        }

    async def attribute_inference_test(self, anonymized: str) -> Dict:
        """
        属性推断攻击测试
        """
        attributes = ["age", "gender", "location", "occupation"]
        results = {}

        for attr in attributes:
            inference = await self._attempt_attribute_inference(anonymized, attr)
            results[attr] = {
                "inferred": inference.get("inferred"),
                "confidence": inference.get("confidence"),
                "blocked": inference.get("blocked", False)
            }

        return {
            "inference_accuracy": sum(1 for r in results.values() if not r["blocked"]) / len(results),
            "detailed_results": results
        }
```

---

## 4. 预期效果

| 指标 | 当前 (异构配置1) | 目标 (TRACE-RPS集成) | 提升 |
|------|------------------|---------------------|------|
| 隐私分数 | 0.655 | 0.90+ | +37% |
| 属性推断准确率 | ~35% | <10% | -71% |
| 效用分数 | 0.916 | 0.90+ | 保持 |
| 成功率 | 70% | 85%+ | +21% |

---

## 5. 实施步骤

### Step 1: 基础设施准备 (1-2天)
- [ ] 克隆 TRACE-RPS 仓库到本地
- [ ] 分析其代码结构
- [ ] 提取可复用的 TRACE 和 RPS 模块

### Step 2: TRACE 模块实现 (3-5天)
- [ ] 实现注意力机制隐私提取
- [ ] 实现推理链分析
- [ ] 集成到现有防御流程

### Step 3: RPS 优化实现 (3-5天)
- [ ] 实现两阶段优化策略
- [ ] 实现拒绝行为诱导
- [ ] 集成到对抗训练循环

### Step 4: 评估和调优 (2-3天)
- [ ] 实现统一评估框架
- [ ] 运行对比实验
- [ ] 调优超参数

### Step 5: 文档和部署 (1-2天)
- [ ] 更新配置文件
- [ ] 编写使用文档
- [ ] 前端展示集成

---

## 6. 参考资源

### TRACE-RPS 相关

- **论文**: [Stop Tracking Me! Proactive Defense Against Attribute Inference Attack in LLMs](https://arxiv.org/abs/2602.11528)
- **代码**: [Jasper-Yan/TRACE-RPS](https://github.com/Jasper-Yan/TRACE-RPS)
- **PDF**: `/mnt/f/daily_work/graduation project/translatepapers/TRACE-RPS.pdf`

### 当前项目

- **最佳配置**: `configs/anonymization/synthetic/07_heterogeneous_unified.yaml`
- **训练结果**: `training_results_enhanced/`

---

## 7. 下一步行动

1. **立即**: 阅读 TRACE-RPS 论文 PDF
2. **本周**: 克隆代码仓库，分析实现
3. **下周**: 开始 TRACE 模块集成

---

**作者**: Claude AI Assistant
**日期**: 2026-04-29
**版本**: v1.0
