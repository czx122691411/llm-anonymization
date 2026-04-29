# Claude Custom Skills

本项目为 LLM匿名化项目定义的自定义 Claude skills，用于增强 Claude 对项目特定功能的理解。

## 技能列表

### 1. bootstrap-framework.md
**人机协作自举框架技能**

- **版本**: 0.3.0
- **类别**: framework
- **功能**:
  - 技能定义和管理
  - AI驱动的技能生成
  - 自动化测试和质量评估
  - 人类审核和知识注入
  - 迭代改进

**核心特性**:
- 五阶段自举循环（初始化→探索→测试→反馈→注入）
- 技能层次结构（原子技能→功能技能→策略技能）
- 多维度质量评估（正确性、效率、健壮性、可维护性）

**相关文件**:
- `src/bootstrap/` - 框架实现
- `scripts/demo_bootstrap_engine.py` - 演示脚本
- `CLAUDE.md` - 完整文档

### 2. heterogeneous-training.md
**异构模型对抗训练技能**

- **版本**: 1.0.0
- **类别**: training
- **功能**:
  - 多模型异构训练
  - 对抗性训练策略
  - 隐私保护机制
  - 分布式训练协调
  - 实验报告生成

**核心特性**:
- 支持525样本完整训练
- 远程服务器部署（8.147.70.110）
- 实时监控和日志分析
- GPU性能优化

**相关文件**:
- `src/training/` - 训练代码
- `data/base_inferences/synthetic/` - 训练数据

### 3. data-anonymization.md
**LLM数据匿名化技能**

- **版本**: 1.0.0
- **类别**: privacy
- **功能**:
  - 敏感信息识别
  - 多种脱敏策略
  - 数据格式保持
  - 批量处理
  - 质量验证

**核心特性**:
- 支持PII、医疗、财务等多种敏感信息
- 6种脱敏策略（替换、掩码、哈希、噪声、删除、伪造）
- GDPR合规性检查
- 差分隐私支持

## 使用方式

这些 skills 会被 Claude Code 自动识别和使用。当你在项目中工作时，Claude 会：

1. **理解项目架构**: 通过技能文件了解项目核心功能
2. **提供精准帮助**: 基于技能定义提供相关建议
3. **生成正确代码**: 参考技能中的代码示例
4. **遵循最佳实践**: 按照技能中的最佳实践指导

## 技能文件格式

每个技能文件包含：

```yaml
---
name: skill-name
description: 技能描述
author: 作者
version: 版本号
category: 类别
tags: [标签列表]
capabilities:
  - 能力1
  - 能力2
---
```

## 更新记录

- **2026-04-20**: 创建初始技能定义
  - bootstrap-framework v0.3.0
  - heterogeneous-training v1.0.0
  - data-anonymization v1.0.0

## 维护指南

### 添加新技能

1. 在 `.claude/skills/` 创建新的 `.md` 文件
2. 按照格式定义 metadata
3. 详细描述技能功能和使用方式
4. 包含代码示例和最佳实践
5. 更新本 README

### 更新现有技能

1. 修改对应的 `.md` 文件
2. 更新版本号
3. 在文档底部添加更新记录

## 项目集成

这些技能与项目的主要模块集成：

```
.claude/skills/
├── bootstrap-framework.md    ← src/bootstrap/
├── heterogeneous-training.md  ← src/training/
├── data-anonymization.md      ← src/anonymization/
└── README.md                  ← 本文件
```

## 相关资源

- 项目文档: `CLAUDE.md`
- 代码仓库: `/home/rooter/llm-anonymization/`
- 服务器: 8.147.70.110
- 训练数据: `data/base_inferences/synthetic/`
