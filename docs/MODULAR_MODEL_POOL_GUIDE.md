# 多模型异构对抗匿名化平台 - 模块化架构指南

## 概述

本文档介绍了多模型异构对抗匿名化平台的模块化架构设计。该架构允许灵活组合不同LLM提供商的模型作为防御者、攻击者和评估者，同时确保某个API不可用时不影响其他模型的使用。

## 架构设计原则

### 1. 模块化独立性
- **每个提供商独立运行**：DeepSeek、OpenAI、Anthropic等各自独立
- **独立的可用性检查**：每个提供商有自己的检测逻辑
- **优雅的降级**：不可用的提供商不会导致系统崩溃

### 2. 现有集成
- **与现有model_factory集成**：复用现有的模型创建机制
- **配置兼容**：使用现有的ModelConfig系统
- **对抗框架兼容**：与现有的AdversarialAnonymizer无缝集成

## 目录结构

```
src/
├── models/
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── registry.py          # 提供商注册表（核心）
│   │   └── base.py              # 基础接口定义
│   ├── model_factory.py         # 现有模型工厂
│   ├── open_ai.py              # OpenAI实现
│   ├── deepseek.py             # DeepSeek实现
│   └── ...
├── api_cost_analyzer.py        # 成本分析模块
└── anonymized/
    └── adversarial.py          # 现有对抗框架

examples/
└── modular_model_pool_usage.py  # 使用示例
```

## 核心组件

### 1. ProviderRegistry（提供商注册表）

位置：`src/models/providers/registry.py`

这是核心组件，负责：
- 管理所有提供商的信息
- 检查每个提供商的可用性
- 提供模型选择功能
- 成本估算

**主要功能：**

```python
from src.models.providers.registry import get_registry

# 获取注册表实例
registry = get_registry(region="international")

# 检查提供商可用性
availability = registry.check_provider_availability("deepseek")

# 获取所有可用提供商
all_providers = registry.get_available_providers()

# 获取特定角色的最佳模型
defender_models = registry.get_available_models(role="defender")

# 创建模型实例
model = registry.create_model_instance("deepseek-chat", temperature=0.1)
```

### 2. APICostAnalyzer（API成本分析器）

位置：`src/api_cost_analyzer.py`

提供详细的成本分析：
- 各提供商的定价信息
- 中国vs国际地区的可获取性
- 注册难度评估
- 实验成本估算

**主要功能：**

```python
from src.api_cost_analyzer import APICostAnalyzer

analyzer = APICostAnalyzer(region=Region.CHINA)

# 比较不同模型的成本
costs = analyzer.compare_costs()

# 估算实验成本
estimate = analyzer.estimate_run_cost(
    defender_model="deepseek-chat",
    attacker_model="deepseek-reasoner",
    evaluator_model="qwen-max",
    num_profiles=100,
    num_rounds=5
)
```

## 使用方式

### 方式1：快速检查提供商状态

```python
from src.models.providers.registry import print_provider_status

# 打印所有提供商状态
print_provider_status(region="international")
print_provider_status(region="china")
```

输出示例：
```
============================================================
Provider Status (Region: international)
============================================================

✓ DeepSeek (deepseek)
   Status: available
   Region: china
   China Accessible: Yes
   Available Models: deepseek-chat, deepseek-reasoner
   Cost: $0.14 input / $0.28 output per 1k tokens

✗ OpenAI (openai)
   Status: unconfigured
   Error: OPENAI_API_KEY not found in environment
```

### 方式2：创建异构模型组合

```python
from src.models.providers.registry import get_registry

registry = get_registry(region="international")

# 策略：使用不同提供商的模型
composition = {}
used_providers = set()

for role in ["defender", "attacker", "evaluator"]:
    models = registry.get_available_models(role=role)

    # 选择来自未使用提供商的最佳模型
    for model in models:
        if model.provider_id not in used_providers:
            composition[role] = model
            used_providers.add(model.provider_id)
            break

# 创建模型实例
instances = {}
for role, model_info in composition.items():
    instance = registry.create_model_instance(
        model_info.model_id,
        temperature=0.1
    )
    instances[role] = instance
```

### 方式3：与现有对抗框架集成

```python
from src.anonymized.adversarial import run_adversarial_anonymization
from src.models.providers.registry import get_registry

# 获取模型实例
registry = get_registry(region="china")

defender = registry.create_model_instance("deepseek-chat")
attacker = registry.create_model_instance("deepseek-reasoner")
evaluator = registry.create_model_instance("qwen-max")

# 使用现有框架
results = run_adversarial_anonymization(
    profiles=profiles,
    defender_model=defender,
    attacker_model=attacker,
    evaluator_model=evaluator,
    config=anonymization_config,
    max_rounds=5
)
```

## API成本和可获取性总结

### 成本对比（每1K tokens，USD）

| 提供商 | 模型 | 输入 | 输出 | 总计 | 中国可用 |
|--------|------|------|------|------|----------|
| DeepSeek | deepseek-chat | $0.14 | $0.28 | $0.42 | ✓ |
| DeepSeek | deepseek-reasoner | $0.55 | $2.19 | $2.74 | ✓ |
| Qwen | qwen-turbo | $0.30 | $0.60 | $0.90 | ✓ |
| Qwen | qwen-plus | $0.40 | $1.00 | $1.40 | ✓ |
| Qwen | qwen-max | $1.20 | $2.00 | $3.20 | ✓ |
| Zhipu | glm-4 | $0.50 | $0.50 | $1.00 | ✓ |
| Zhipu | glm-4-plus | $0.70 | $0.70 | $1.40 | ✓ |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | $0.75 | ✗ |
| OpenAI | gpt-4o | $2.50 | $10.00 | $12.50 | ✗ |
| Anthropic | claude-3-haiku | $0.25 | $1.25 | $1.50 | ✗ |
| Anthropic | claude-3.5-sonnet | $3.00 | $15.00 | $18.00 | ✗ |

### 注册难度

**非常简单（无需信用卡）：**
- DeepSeek：中文文档，支持支付宝/微信支付
- Qwen：阿里云服务，免费额度
- Zhipu：免费额度，中文文档
- Ollama：本地运行，完全免费

**中等（需要信用卡但较容易）：**
- Google Gemini：免费额度

**困难（需要VPN + 国际信用卡）：**
- OpenAI：无免费额度
- Anthropic：无免费额度

### 推荐配置

**中国用户推荐：**
```python
# 性价比配置
composition = {
    "defender": "deepseek-chat",      # $0.42/1k
    "attacker": "deepseek-reasoner",  # $2.74/1k
    "evaluator": "qwen-plus"          # $1.40/1k
}
# 总成本：约$4.58/1k tokens

# 最优性能配置
composition = {
    "defender": "qwen-max",
    "attacker": "deepseek-reasoner",
    "evaluator": "glm-4-plus"
}
```

**国际用户推荐：**
```python
# 性价比配置
composition = {
    "defender": "gpt-4o-mini",        # $0.75/1k
    "attacker": "deepseek-chat",      # $0.42/1k
    "evaluator": "claude-3-haiku"     # $1.50/1k
}
# 总成本：约$2.67/1k tokens

# 最优性能配置
composition = {
    "defender": "gpt-4o",
    "attacker": "claude-3.5-sonnet",
    "evaluator": "gpt-4o"
}
```

## 成本估算示例

对于100个profile，5轮对抗训练：

使用中国友好配置（DeepSeek + Qwen）：
- 输入token：500,000 × 3 = 1,500,000
- 输出token：250,000 × 3 = 750,000
- 预计成本：约$380-500

使用国际配置（GPT-4o-mini + Claude）：
- 相同token量
- 预计成本：约$600-800

## 扩展性

### 添加新的提供商

1. 在`registry.py`的`PROVIDERS`中添加提供商信息
2. 在`MODELS`中添加模型定义
3. 实现提供商特定的可用性检查

### 添加新的选择策略

```python
def custom_selection_strategy(registry, role):
    """自定义选择策略"""
    models = registry.get_available_models(role=role)

    # 实现自定义逻辑
    # 例如：优先选择成本最低的模型
    return sorted(models, key=lambda m: m.cost_per_1k_input)[0]
```

## 错误处理

系统采用优雅降级策略：

1. **API密钥未配置**：返回UNCONFIGURED状态，显示需要设置的环境变量
2. **网络问题**：返回UNREACHABLE状态，显示错误信息
3. **模型不支持**：自动跳过，尝试下一个模型
4. **提供商全部不可用**：返回友好的错误消息和建议

## 最佳实践

1. **始终检查可用性**：在使用模型前检查提供商状态
2. **使用回退机制**：准备多个备选模型
3. **监控成本**：使用成本估算功能避免意外开销
4. **区域优化**：根据用户位置选择合适的提供商
5. **测试配置**：在小规模数据上测试模型组合

## 故障排除

**问题：提供商显示UNCONFIGURED**
- 解决：设置相应的API密钥环境变量

**问题：在中国无法访问OpenAI**
- 解决：使用VPN或切换到中国友好提供商（DeepSeek、Qwen等）

**问题：成本过高**
- 解决：使用成本优化策略选择更便宜的模型组合

**问题：模型性能不佳**
- 解决：查看模型的capability scores，选择更高分数的模型
