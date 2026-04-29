---
name: heterogeneous-training
description: 异构模型对抗训练技能，支持多模型联合训练和隐私保护
author: Claude & Human Collaboration
version: 1.0.0
category: training
tags: [training, heterogeneous-models, adversarial, privacy, federated]
capabilities:
  - 多模型异构训练
  - 对抗性训练策略
  - 隐私保护机制
  - 分布式训练协调
  - 实验报告生成
---

# 异构模型对抗训练技能

支持多种LLM模型的异构对抗训练，实现隐私保护下的模型性能提升。

## 核心概念

### 异构模型训练
使用不同架构、不同参数规模的模型进行联合训练，通过对抗学习提升整体性能。

### 训练流程
1. **数据准备**: 加载和预处理训练数据
2. **模型初始化**: 初始化异构模型集合
3. **对抗训练**: 模型间进行对抗学习
4. **性能评估**: 评估各模型性能
5. **结果保存**: 保存训练结果和模型

## 使用指南

### 1. 基础训练配置

```python
import sys
sys.path.append('/home/rooter/llm-anonymization')

from src.training.heterogeneous_trainer import HeterogeneousTrainer
from src.configs.config import Config

# 配置
config = Config(
    data_path="data/base_inferences/synthetic/inference_0.jsonl",
    output_dir="outputs/heterogeneous_training",
    models=["qwen-plus", "deepseek-chat", "glm-4"],
    epochs=3,
    batch_size=32
)

# 创建训练器
trainer = HeterogeneousTrainer(config)
```

### 2. 运行训练

```python
# 远程服务器训练
import subprocess

# 登录服务器
ssh_cmd = "ssh rooter@8.147.70.110"

# 部署代码
deploy_cmd = f"""
{ssh_cmd} "cd /root && \\
rm -rf llm-anonymization && \\
git clone https://github.com/your-repo/llm-anonymization.git && \\
cd llm-anonymization && \\
pip install -r requirements.txt"
"""

# 启动训练
train_cmd = f"""
{ssh_cmd} "cd /root/llm-anonymization && \\
nohup python -m src.training.run_heterogeneous \\
--data data/base_inferences/synthetic/inference_0.jsonl \\
--models qwen-plus deepseek-chat glm-4 \\
--epochs 3 \\
--output outputs/exp_$(date +%Y%m%d_%H%M%S) > train.log 2>&1 &"
"""

# 执行
sub.run(deploy_cmd, shell=True)
sub.run(train_cmd, shell=True)
```

### 3. 监控训练进度

```python
# SSH 监控脚本
monitor_script = """#!/bin/bash
cd /root/llm-anonymization

while true; do
    clear
    echo "=== 训练进度监控 ==="
    echo "时间: $(date)"
    echo ""

    # 检查进程
    if pgrep -f "run_heterogeneous" > /dev/null; then
        echo "✓ 训练进程运行中"
    else
        echo "✗ 训练进程未运行"
    fi

    echo ""
    echo "=== 最新日志 ==="
    tail -20 train.log

    echo ""
    echo "=== GPU 使用 ==="
    nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv

    sleep 10
done
"""

# 保存并执行
with open("monitor_training.sh", "w") as f:
    f.write(monitor_script)

subprocess.run(f"scp monitor_training.sh rooter@8.147.70.110:/root/", shell=True)
subprocess.run(f"{ssh_cmd} 'bash /root/monitor_training.sh'", shell=True)
```

### 4. 525样本完整训练

```python
# 完整训练脚本
train_525_script = """
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from src.training import HeterogeneousTrainer, TrainingConfig
from src.models.providers.registry import get_registry

async def train_525_samples():
    # 配置
    config = TrainingConfig(
        data_path="data/base_inferences/synthetic/inference_0.jsonl",
        sample_count=525,
        models=["qwen-plus", "deepseek-chat", "glm-4"],
        epochs=3,
        batch_size=32,
        output_dir="outputs/train_525_full"
    )

    # 初始化
    registry = get_registry(region="china")
    models = [registry.create_model_instance(m) for m in config.models]

    trainer = HeterogeneousTrainer(config, models)

    # 训练
    results = await trainer.train()

    # 保存结果
    trainer.save_results(results)

    return results

if __name__ == "__main__":
    asyncio.run(train_525_samples())
"""

# 保存并运行
with open("train_525_full.py", "w") as f:
    f.write(train_525_script)

subprocess.run("python train_525_full.py", shell=True)
```

### 5. 实验结果分析

```python
from src.analysis import ExperimentAnalyzer

# 分析结果
analyzer = ExperimentAnalyzer("outputs/train_525_full")

# 生成报告
report = analyzer.generate_report()

# 可视化
analyzer.plot_metrics(save_path="outputs/train_525_full/metrics.png")
analyzer.plot_confusion_matrix(save_path="outputs/train_525_full/confusion.png")

print(report)
```

## 训练策略

### 对抗训练模式

1. **并行对抗**: 多个模型同时处理相同数据，比较结果
2. **顺序对抗**: 模型依次处理，后续模型学习前序模型经验
3. **集成对抗**: 模型组成集成系统，集体决策

### 隐私保护机制

- **数据脱敏**: 自动识别和脱敏敏感信息
- **差分隐私**: 添加噪声保护个体隐私
- **联邦学习**: 分布式训练，数据不出本地
- **安全聚合**: 加密聚合模型更新

## 配置参数

### TrainingConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| data_path | str | - | 训练数据路径 |
| sample_count | int | 525 | 训练样本数量 |
| models | list | ["qwen-plus"] | 模型列表 |
| epochs | int | 3 | 训练轮数 |
| batch_size | int | 32 | 批次大小 |
| learning_rate | float | 0.001 | 学习率 |
| output_dir | str | "outputs" | 输出目录 |
| save_frequency | int | 100 | 保存频率(步) |

## 服务器部署

### 准备工作

```bash
# 1. SSH 登录
ssh rooter@8.147.70.110

# 2. 安装依赖
sudo apt update
sudo apt install python3.8 python3-pip git -y
pip3 install torch transformers accelerate

# 3. 克隆项目
cd /root
git clone <your-repo-url> llm-anonymization
cd llm-anonymization
pip install -r requirements.txt
```

### 启动训练

```bash
# 前台运行（测试）
python -m src.training.run_heterogeneous \\
    --data data/base_inferences/synthetic/inference_0.jsonl \\
    --models qwen-plus deepseek-chat \\
    --epochs 1 \\
    --output outputs/test

# 后台运行（正式）
nohup python -m src.training.run_heterogeneous \\
    --data data/base_inferences/synthetic/inference_0.jsonl \\
    --models qwen-plus deepseek-chat glm-4 \\
    --epochs 3 \\
    --output outputs/exp_$(date +%Y%m%d_%H%M%S) \\
    > train.log 2>&1 &

# 查看日志
tail -f train.log

# 检查进程
ps aux | grep run_heterogeneous
```

## 监控和调试

### GPU 监控

```bash
# 实时监控
watch -n 1 nvidia-smi

# 详细信息
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv
```

### 日志分析

```bash
# 训练进度
grep "Epoch" train.log

# 损失值
grep "Loss" train.log

# 错误信息
grep "ERROR" train.log
```

### 性能优化

- 使用混合精度训练 (FP16)
- 梯度累积减少显存
- 数据预加载
- 多GPU并行

## 结果评估

### 评估指标

1. **准确率 (Accuracy)**: 预测正确的比例
2. **精确率 (Precision)**: 正类预测的准确性
3. **召回率 (Recall)**: 正类的识别能力
4. **F1分数**: 精确率和召回率的调和平均
5. **混淆矩阵**: 分类详情

### 可视化

```python
# 训练曲线
plot_training_curve(losses, accuracies, save_path="training_curve.png")

# 模型比较
plot_model_comparison(results, save_path="model_comparison.png")

# 注意力可视化
plot_attention_heatmap(attention_weights, save_path="attention.png")
```

## 故障排查

### 常见问题

1. **OOM (显存不足)**
   - 减小 batch_size
   - 使用梯度累积
   - 启用混合精度

2. **训练缓慢**
   - 检查数据加载
   - 增加 workers
   - 使用分布式训练

3. **不收敛**
   - 调整学习率
   - 检查数据质量
   - 增加训练轮数

4. **SSH 断线**
   - 使用 nohup
   - 使用 screen/tmux
   - 定期保存检查点

## 参考资源

- 训练代码: `src/training/`
- 配置文件: `src/configs/config.py`
- 数据路径: `data/base_inferences/synthetic/`
- 服务器: 8.147.70.110
- 演示脚本: `scripts/train_525_full.py`
