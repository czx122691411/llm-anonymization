---
name: data-anonymization
description: LLM数据匿名化处理技能，支持敏感信息识别和脱敏
author: Claude & Human Collaboration
version: 1.0.0
category: privacy
tags: [privacy, anonymization, pii, data-protection, gdpr]
capabilities:
  - 敏感信息识别
  - 多种脱敏策略
  - 数据格式保持
  - 批量处理
  - 质量验证
---

# LLM数据匿名化技能

保护隐私的LLM训练数据处理，支持多种敏感信息识别和脱敏策略。

## 核心概念

### 敏感信息类型

1. **个人身份信息 (PII)**
   - 姓名、身份证号、护照号
   - 电话号码、邮箱地址
   - 地址、位置信息

2. **财务信息**
   - 银行卡号、账号
   - 交易记录、金额

3. **健康信息**
   - 病历、诊断
   - 医疗记录

4. **其他敏感信息**
   - 密码、密钥
   - 商业机密
   - 法律文档

### 脱敏策略

| 策略 | 说明 | 示例 |
|------|------|------|
| 替换 | 用固定值替换 | 张三 → [姓名] |
| 掩码 | 部分隐藏 | 13812345678 → 138****5678 |
| 哈希 | 单向哈希 | 原值 → 固定长度哈希 |
| 噪声 | 添加噪声 | 精确值 → 近似值 |
| 删除 | 完全移除 | 保留上下文但移除敏感值 |
| 伪造 | 合成假值 | 真实值 → 合成但合理的值 |

## 使用指南

### 1. 基础脱敏

```python
from src.anonymization import Anonymizer, AnonymizerConfig

# 配置
config = AnonymizerConfig(
    strategies={
        "name": "replace",
        "phone": "mask",
        "email": "replace",
        "id_card": "hash"
    }
)

# 创建脱敏器
anonymizer = Anonymizer(config)

# 处理文本
text = "张三的电话是13812345678，邮箱是zhangsan@example.com"
anonymized = anonymizer.anonymize(text)
print(anonymized)
# 输出: [姓名]的电话是138****5678，邮箱是[邮箱]
```

### 2. 批量处理

```python
import json
from pathlib import Path

# 读取数据
data_path = "data/base_inferences/synthetic/inference_0.jsonl"
output_path = "data/anonymized/inference_0_anon.jsonl"

with open(data_path, 'r') as f_in, open(output_path, 'w') as f_out:
    for line in f_in:
        record = json.loads(line)

        # 脱敏处理
        if 'text' in record:
            record['text'] = anonymizer.anonymize(record['text'])
        if 'metadata' in record:
            record['metadata'] = anonymizer.anonymize_dict(record['metadata'])

        # 保存
        f_out.write(json.dumps(record, ensure_ascii=False) + '\n')
```

### 3. 自定义识别规则

```python
from src.anonymization import PatternRecognizer

# 自定义识别器
class CustomRecognizer(PatternRecognizer):
    def __init__(self):
        super().__init__(["CUSTOM_ID"])

        # 定义模式
        self.patterns = [
            r"[A-Z]{2}\d{10}"  # 例如: AB1234567890
        ]

        # 定义上下文关键词
        self.context_keywords = ["会员号", "卡号", "编号"]

    # 自定义验证逻辑
    def validate(self, match_text, context):
        # 验证校验位等
        return len(match_text) == 12

# 注册识别器
anonymizer.register_recognizer(CustomRecognizer())
```

### 4. 质量验证

```python
from src.anonymization import QualityValidator

validator = QualityValidator()

# 验证脱敏质量
results = validator.validate(
    original_data,
    anonymized_data
)

# 查看报告
print(f"敏感信息覆盖率: {results.coverage}%")
print(f"脱敏准确率: {results.accuracy}%")
print(f"数据可用性: {results.usability}%")
print(f"问题数量: {results.issues}")

# 详细问题
for issue in results.issues_list:
    print(f"- {issue.type}: {issue.description}")
```

### 5. 差分隐私

```python
from src.anonymization import DifferentialPrivacy

# 配置差分隐私
dp = DifferentialPrivacy(
    epsilon=1.0,  # 隐私预算
    delta=1e-5,   # 失败概率
    mechanism="laplacian"  # 机制
)

# 添加噪声到数值数据
noisy_counts = dp.add_noise(counts)

# 查询隐私保护
answer = dp.query(private_data, query_function)
```

## 高级功能

### 1. 格式保持脱敏

```python
from src.anonymization import FormatPreservingAnonymizer

# 保持格式的脱敏
fp_anon = FormatPreservingAnonymizer()

# 邮箱脱敏（保持格式）
email = "user@example.com"
anon_email = fp_anon.anonymize_email(email)
# 输出: u***@e******.com

# 日期脱敏
date = "1990-01-15"
anon_date = fp_anon.anonymize_date(date, preserve_format=True)
# 输出: 1985-05-20 (格式保持但值改变)
```

### 2. 实体识别增强

```python
from src.anonymization import EntityEnhancedAnonymizer

# 使用NER模型增强识别
enhanced_anon = EntityEnhancedAnonymizer(
    ner_model="bert-base-chinese-ner",
    custom_rules=True
)

# 更精确的识别
text = "张三和李四讨论了项目X的预算"
result = enhanced_anon.anonymize_with_entities(text)
# 输出: [人名]和[人名]讨论了[项目]的预算
```

### 3. 上下文感知脱敏

```python
from src.anonymization import ContextAwareAnonymizer

# 考虑上下文的脱敏
context_anon = ContextAwareAnonymizer()

# 同一实体在不同上下文
text1 = "张三的年龄是25岁"
text2 = "张三的工资是10000元"

result1 = context_anon.anonymize(text1, context_id="doc1")
result2 = context_anon.anonymize(text2, context_id="doc1")

# 同一文档内同一实体使用相同替换
# result1: [PERSON_1]的年龄是25岁
# result2: [PERSON_1]的工资是10000元
```

## 配置选项

### AnonymizerConfig

```python
config = AnonymizerConfig(
    # 基础设置
    language="zh-CN",              # 语言
    default_strategy="replace",    # 默认策略

    # 识别设置
    detect_pii=True,               # 检测PII
    detect_medical=True,           # 检测医疗信息
    detect_financial=True,         # 检测财务信息

    # 脱敏设置
    hash_salt="secret_salt",       # 哈希盐值
    mask_char="*",                 # 掩码字符
    mask_ratio=0.5,                # 掩码比例

    # 质量设置
    preserve_format=True,          # 保持格式
    preserve_length=False,         # 保持长度
    validate_output=True,          # 验证输出

    # 性能设置
    batch_size=100,                # 批处理大小
    num_workers=4,                 # 并行工作数
    cache_enabled=True             # 启用缓存
)
```

## 数据流程

```
原始数据
    ↓
[1] 数据解析
    ↓
[2] 敏感信息识别
    ├─ 正则匹配
    ├─ NER模型
    └─ 自定义规则
    ↓
[3] 脱敏策略应用
    ├─ 替换
    ├─ 掩码
    ├─ 哈希
    └─ 其他
    ↓
[4] 质量验证
    ├─ 覆盖率检查
    ├─ 准确性检查
    └─ 可用性检查
    ↓
脱敏数据
```

## 最佳实践

### 1. 分层脱敏

```python
# 第一层：基础脱敏
basic_anon = Anonymizer(config_basic)
data = basic_anon.anonymize(raw_data)

# 第二层：增强脱敏
enhanced_anon = Anonymizer(config_enhanced)
data = enhanced_anon.anonymize(data)

# 第三层：严格脱敏
strict_anon = Anonymizer(config_strict)
final_data = strict_anon.anonymize(data)
```

### 2. 验证和审计

```python
# 保留原始数据映射
mapping = anonymizer.get_mapping()

# 审计日志
audit_log = {
    "timestamp": datetime.now(),
    "records_processed": len(data),
    "sensitive_found": anonymizer.stats.sensitive_count,
    "strategies_used": anonymizer.stats.strategies,
    "quality_score": validator.score
}
```

### 3. 性能优化

```python
# 使用缓存
anonymizer.enable_cache()

# 批处理
results = anonymizer.anonymize_batch(texts, batch_size=100)

# 并行处理
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(anonymizer.anonymize, texts))
```

## 合规性检查

### GDPR 合规

```python
from src.anonymization.compliance import GDPRChecker

checker = GDPRChecker()

# 检查合规性
report = checker.check(anonymized_data)

print(f"合规性: {report.compliant}")
print(f"风险等级: {report.risk_level}")
print(f"建议: {report.recommendations}")
```

### 风险评估

```python
from src.anonymization import RiskAssessor

assessor = RiskAssessor()

# 评估重识别风险
risk = assessor.assess_reidentification_risk(
    anonymized_data,
    original_data
)

print(f"重识别风险: {risk.score}")
print(f"攻击向量: {risk.attack_vectors}")
print(f"缓解措施: {risk.mitigations}")
```

## 故障排查

### 问题1: 识别不准确

```python
# 调试模式
anonymizer.debug_mode = True

# 查看识别结果
details = anonymizer.anonymize_debug(text)
print(details.matches)
```

### 问题2: 格式破坏

```python
# 启用格式保持
config = AnonymizerConfig(
    preserve_format=True,
    preserve_length=True
)
```

### 问题3: 性能问题

```python
# 禁用不必要的检查
config = AnonymizerConfig(
    validate_output=False,
    cache_enabled=True,
    batch_size=200
)
```

## 参考资源

- 脱敏代码: `src/anonymization/`
- 配置示例: `configs/anonymization_config.yaml`
- 测试数据: `data/test/sample_pii.jsonl`
- 规范文档: `docs/gdpr_compliance.md`
- 版本: v1.0.0
