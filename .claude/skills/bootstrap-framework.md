---
name: bootstrap-framework
description: 人机协作自举框架技能，支持五阶段自举循环开发AI技能库
author: Claude & Human Collaboration
version: 0.3.0
category: framework
tags: [bootstrap, skills, ai, human-ai-collaboration]
capabilities:
  - 技能定义和管理
  - AI驱动的技能生成
  - 自动化测试和质量评估
  - 人类审核和知识注入
  - 迭代改进
---

# 人机协作自举框架技能

基于SkillX理念的五阶段自举循环，用于构建和进化AI技能库。

## 核心概念

### 五阶段自举循环
1. **初始化 (Initiate)** - 人类定义原子技能（种子）
2. **探索与生成 (Explore & Generate)** - AI组合生成新技能
3. **测试与评估 (Test & Evaluate)** - AI自动测试评估质量
4. **反馈与迭代 (Feedback & Iterate)** - AI根据反馈自我改进
5. **注入与验证 (Inject & Validate)** - 人类审核注入专业知识

### 技能层次结构
- **原子技能 (Atomic Skills)**: 基础操作单元，人类定义
- **功能技能 (Functional Skills)**: 组合原子技能，形成复杂功能
- **策略技能 (Planning Skills)**: 高层决策和优化策略

## 使用指南

### 1. 初始化自举引擎

```python
from src.bootstrap import BootstrapEngine, BootstrapConfig
from src.models.providers.registry import get_registry

# 配置
config = BootstrapConfig(
    storage_path="./skill_repository",
    target_quality=0.85,
    max_iterations=5,
    enable_auto_testing=True,
    enable_human_interaction=False  # 演示时禁用
)

# LLM客户端
registry = get_registry(region="china")
llm_client = registry.create_model_instance("qwen-plus", temperature=0.7)

# 创建引擎
engine = BootstrapEngine(config, llm_client)
```

### 2. 运行自举循环

```python
# 定义目标
objective = """
构建数据处理相关的技能库，包括：
- 文件读写能力
- 数据验证能力
- 数据转换能力
- 批处理能力
- 错误处理能力
"""

# 运行自举
result = await engine.run_bootstrap_cycle(
    objective=objective,
    max_iterations=5
)

# 查看结果
print(f"生成技能: {result.total_new_skills}")
print(f"平均质量: {result.final_avg_quality:.2f}")
print(f"成功率: {result.final_avg_success_rate:.2%}")
```

### 3. 技能定义

创建原子技能：

```python
from src.bootstrap import create_atomic_skill, SkillCategory

skill = create_atomic_skill(
    name="read_text_file",
    description="读取文本文件内容",
    inputs={
        "file_path": {
            "type": "str",
            "description": "文件路径",
            "required": True
        }
    },
    outputs={
        "content": {
            "type": "str",
            "description": "文件内容"
        },
        "success": {
            "type": "bool",
            "description": "是否成功"
        }
    },
    implementation='''
try:
    with open(inputs["file_path"], "r", encoding="utf-8") as f:
        content = f.read()
    success = True
except Exception as e:
    content = str(e)
    success = False
'''
)
```

### 4. 人类审核

```python
from src.bootstrap import HumanInterface

interface = HumanInterface(repository)

# 审核待处理技能
reviews = await interface.review_pending_skills(max_skills=10)

# 注入新知识
proposals = await interface.inject_knowledge()

# 提供反馈
feedback = await interface.get_feedback_on_cycle(cycle_result)
```

### 5. 智能测试

```python
from src.bootstrap import AISkillExecutor

executor = AISkillExecutor(repository)

# 生成测试用例
test_cases = await executor.generate_test_cases(skill, count=5)

# 执行测试
results, quality = await executor.execute_tests(skill, test_cases)

# 诊断错误
diagnosis = await executor.diagnose_errors(skill, results)
print(f"错误类型: {diagnosis['error_types']}")
print(f"改进建议: {diagnosis['suggestions']}")
```

## 质量评估

技能质量从四个维度评估：

1. **正确性 (Correctness)**: 基于测试成功率
2. **效率 (Efficiency)**: 基于执行时间
3. **健壮性 (Robustness)**: 基于错误处理能力
4. **可维护性 (Maintainability)**: 基于代码复杂度

```python
quality = SkillQuality(
    score=0.85,        # 综合质量分数 (0-1)
    success_rate=0.90,  # 成功率
    correctness=0.90,   # 正确性
    efficiency=0.80,    # 效率
    robustness=0.85,    # 健壮性
    maintainability=0.85 # 可维护性
)
```

## 配置选项

### BootstrapConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| storage_path | str | "./skill_repository" | 技能仓库路径 |
| target_quality | float | 0.85 | 目标质量分数 |
| improvement_threshold | float | 0.7 | 改进阈值 |
| validation_threshold | float | 0.9 | 验证阈值 |
| max_iterations | int | 5 | 最大迭代次数 |
| max_skills_per_iteration | int | 10 | 每轮最多生成技能数 |
| enable_auto_testing | bool | True | 启用自动测试 |
| enable_human_interaction | bool | True | 启用人类交互 |
| test_timeout | int | 30 | 测试超时时间(秒) |

## 文件结构

```
skill_repository/
├── atomic/          # 原子技能
├── functional/      # 功能技能
├── planning/        # 策略技能
├── _archive/        # 版本归档
├── _history/        # 执行历史
├── _review/         # 人类审核记录
└── _tests/          # 测试用例
```

## 最佳实践

1. **从少量种子技能开始**: 定义3-5个高质量原子技能作为基础
2. **明确自举目标**: 清晰定义要构建的技能领域和目标
3. **逐步增加迭代**: 开始时使用较少迭代次数，逐步增加
4. **启用人类审核**: 在生产环境务必启用人类审核
5. **监控质量指标**: 关注质量分数和成功率变化
6. **定期注入知识**: 人类专家定期注入新知识以引导方向

## 故障排查

### 技能生成失败
- 检查 LLM API 配置
- 确认网络连接
- 查看错误日志

### 质量分数为0
- 检查技能实现代码
- 验证输入输出定义
- 查看测试错误信息

### 改进无效
- 增加迭代次数
- 调整质量阈值
- 注入人类知识

## 参考资源

- 框架代码: `src/bootstrap/`
- 演示脚本: `scripts/demo_bootstrap_engine.py`
- 文档: `CLAUDE.md`
- 版本: v0.3.0
