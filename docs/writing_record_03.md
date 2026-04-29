# 毕业设计写作记录卡（三）

**学生姓名**: [待填写]
**学号**: [待填写]
**专业班级**: [待填写]
**指导教师**: [待填写]
**记录日期**: 2024年4月

---

## 一、本周工作概述

### 1.1 完成内容
- ✅ 模型注册表 (`src/models/providers/registry.py`)
- ✅ 基础匿名化模块 (`src/anonymized/anonymizers/`)
- ✅ 配置管理系统 (`src/configs/`)
- ✅ 第一轮单元测试

### 1.2 代码统计
```
文件数: 23个
代码行数: ~3500行
测试覆盖: 65%
```

---

## 二、核心模块实现

### 2.1 模型注册表设计

#### 架构设计
采用**工厂模式+策略模式**实现多模型统一管理：

```python
# src/models/providers/registry.py

class ProviderRegistry:
    """LLM服务提供商注册表"""

    def __init__(self, region: str = "china"):
        self._providers = {
            "deepseek": DeepSeekProvider,
            "qwen": QwenProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
        }
        self.region = region

    def create_model_instance(
        self,
        model_name: str,
        temperature: float = 0.7,
        **kwargs
    ) -> BaseModel:
        """创建模型实例"""
        provider_name = self._parse_provider(model_name)
        provider_class = self._providers[provider_name]
        return provider_class(model_name, temperature, **kwargs)
```

#### 设计亮点
1. **区域适配**: 自动选择国内/国际API
2. **类型安全**: 使用Protocol定义统一接口
3. **环境变量管理**: 统一的API密钥管理

### 2.2 匿名化模块实现

#### 类层次结构
```
BaseAnonymizer (抽象基类)
    ├── SpanAnonymizer (基于规则)
    ├── AzureAnonymizer (Azure API)
    └── LLMAnonymizer (LLM生成)
```

#### LLM匿名化流程
```python
# src/anonymized/anonymizers/llm_anonymizers.py

class LLMAnonymizer(BaseAnonymizer):
    def anonymize(self, text: str, level: int = 3) -> dict:
        """
        多级匿名化
        level 0: 不匿名（基准）
        level 1: 移除直接标识符
        level 2: 替换为泛化标签
        level 3: 深度重写
        """
        # 1. 构建提示词
        prompt = self._build_prompt(text, level)

        # 2. LLM生成
        response = self.model.generate(prompt)

        # 3. 后处理验证
        anonymized = self._post_process(response, text)

        # 4. 返回元数据
        return {
            "original": text,
            "anonymized": anonymized,
            "level": level,
            "model": self.model.name,
            "timestamp": datetime.now().isoformat()
        }
```

#### 提示词工程
```python
# src/prompts/prompt.py

ANONYMIZATION_PROMPT = """
你是一个专业的文本匿名化助手。你的任务是：
1. 移除或替换所有个人身份信息（PII）
2. 保持原文的核心含义
3. 维持文本的自然流畅度

需处理的PII类型：
- 姓名、年龄、性别
- 地址、位置信息
- 电话、邮箱
- 职业、工作单位
- 财务信息

原文: {original_text}

匿名化等级: {level}
- 等级1: 仅移除直接标识符
- 等级2: 替换为泛化标签（如[姓名]、[地址]）
- 等级3: 深度重写，完全消除可推断信息

请输出匿名化后的文本，不要添加任何解释。
"""
```

### 2.3 配置管理系统

#### 配置文件结构
```yaml
# configs/anonymization/synthetic/base_config.yaml
experiment:
  name: "synthetic_baseline"
  description: "SynthPAI dataset with Qwen anonymizer"

dataset:
  type: "synthetic"
  path: "data/synthpai/test.jsonl"
  samples: 525

anonymization:
  model: "qwen-plus"
  levels: [0, 1, 2, 3]
  temperature: 0.3
  max_tokens: 2000

adversarial:
  enabled: true
  max_rounds: 3
  attack_model: "deepseek-chat"
  convergence_threshold: 0.05

evaluation:
  privacy_metrics: ["attack_success_rate"]
  utility_metrics: ["bleu", "rouge", "readability"]
  quality_threshold: 0.7
```

#### 配置加载器
```python
# src/configs/config.py

@dataclass
class AnonymizationConfig:
    """匿名化配置"""
    model: str
    levels: List[int]
    temperature: float
    max_tokens: int

    @classmethod
    def from_yaml(cls, path: str) -> "AnonymizationConfig":
        """从YAML加载配置"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data["anonymization"])
```

---

## 三、技术难点攻克

### 3.1 问题：JSON解析稳定性

**现象**: LLM返回的JSON格式不规范，导致解析失败

**解决方案**: 多级Fallback机制
```python
def parse_llm_json(response: str) -> dict:
    """解析LLM返回的JSON，带多级fallback"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # 尝试提取JSON块
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
        # 尝试修复常见错误
        return fix_common_json_errors(response)
```

### 3.2 问题：API调用稳定性

**现象**: 网络波动导致API调用失败

**解决方案**: 指数退避重试
```python
# src/utils/limiter.py

class APIRateLimiter:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def call_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                wait_time = 2 ** attempt  # 1, 2, 4秒
                time.sleep(wait_time)
        raise MaxRetriesExceeded()
```

### 3.3 问题：成本控制

**现象**: API调用成本快速增长

**解决方案**:
1. 实现结果缓存机制
2. 添加成本追踪器
3. 抽样评估策略

```python
# src/api_cost_analyzer.py

class APICostAnalyzer:
    def __init__(self):
        self.costs = defaultdict(float)
        self.costs_per_model = {
            "qwen-plus": 0.004,  # per 1K tokens
            "deepseek-chat": 0.001,
        }

    def log_call(self, model: str, input_tokens: int, output_tokens: int):
        cost = (
            input_tokens * self.costs_per_model[model] / 1000 +
            output_tokens * self.costs_per_model[model] * 2 / 1000
        )
        self.costs[model] += cost

    def get_total_cost(self) -> float:
        return sum(self.costs.values())
```

---

## 四、测试策略

### 4.1 单元测试

```python
# tests/test_registry.py

def test_registry_creation():
    """测试注册表创建"""
    registry = ProviderRegistry(region="china")
    assert registry is not None

def test_model_instantiation():
    """测试模型实例化"""
    registry = ProviderRegistry()
    model = registry.create_model_instance("qwen-plus")
    assert isinstance(model, QwenModel)

def test_model_generation():
    """测试模型生成"""
    model = registry.create_model_instance("qwen-plus", temperature=0.0)
    response = model.generate("Hello")
    assert len(response) > 0
```

### 4.2 集成测试

```python
# tests/test_anonymization.py

def test_end_to_end_anonymization():
    """端到端匿名化测试"""
    config = AnonymizationConfig.from_yaml("configs/test.yaml")
    anonymizer = LLMAnonymizer(config)

    result = anonymizer.anonymize(
        text="I'm John, 25 years old, living in New York.",
        level=2
    )

    assert "John" not in result["anonymized"]
    assert result["level"] == 2
    assert "original" in result
```

### 4.3 测试覆盖率

| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| registry.py | 85% | ✅ |
| llm_anonymizers.py | 72% | ✅ |
| config.py | 90% | ✅ |
| limiter.py | 65% | 🔄 |

---

## 五、中间成果展示

### 5.1 第一轮匿名化结果

```json
{
  "original": "My name is Sarah, I'm a 28-year-old software engineer earning $120k in San Francisco.",
  "anonymized": "My name is [NAME], I'm a [AGE]-year-old professional earning a high salary in a major city.",
  "level": 2,
  "model": "qwen-plus",
  "timestamp": "2024-04-15T10:30:00"
}
```

### 5.2 性能基准

| 指标 | 数值 |
|------|------|
| 平均响应时间 | 2.3秒 |
| 成功率 | 94.5% |
| 平均token数 | 输入180/输出120 |
| 成本/样本 | ¥0.0015 |

---

## 六、遇到的问题与解决

| 问题 | 原因 | 解决方案 | 状态 |
|------|------|----------|------|
| 模块导入错误 | 路径问题 | 添加`__init__.py` | ✅ |
| API密钥泄漏 | 硬编码 | 环境变量管理 | ✅ |
| 测试数据缺失 | 无测试集 | 使用SynthPAI | ✅ |
| 日志混乱 | 无统一格式 | 配置logging模块 | 🔄 |

---

## 七、下周计划

1. **对抗训练模块**实现
2. **质量评估系统**开发
3. **前端界面**原型设计
4. **中期报告**准备

---

## 八、指导记录

### 教师反馈
- ✅ 代码结构清晰，模块化设计合理
- ✅ 测试覆盖率达到要求
- 建议：加强错误处理和日志记录

### 待改进项
1. 添加更详细的API调用日志
2. 完善异常处理机制
3. 考虑添加进度条显示

---

## 九、论文写作进展

### 已完成章节
- ✅ 第一章：绪论（约3000字）
- ✅ 第二章：相关技术与研究现状（约4000字）
- 🔄 第三章：系统设计（进行中）

### 待完成章节
- ⏳ 第四章：系统实现
- ⏳ 第五章：实验与评估
- ⏳ 第六章：总结与展望

---

**记录编号**: WR-2024-003
**下次记录日期**: 2024年4月

**本周代码提交**:
```
commit 8f2abb0: feat: Add enhanced heterogeneous training with quality evaluation
commit 3ff3f98: feat: Add synthetic experiment configs and training scripts
commit d65f495: Merge remote README with local version
```

