#!/bin/bash

echo "========================================"
echo "📊 525条数据训练监控面板"
echo "========================================"
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查进程状态
echo "=== 🖥️ 进程状态 ==="
if ps aux | grep -q "[t]rain_525_full.py"; then
    echo "✓ 训练进程正在运行"
    ps aux | grep "[t]rain_525_full.py" | awk '{printf "  PID: %s | CPU: %s%% | MEM: %s%% | 运行时间: %s\n", $2, $3, $4, $10}'
else
    echo "✗ 训练进程未运行"
fi
echo ""

# 检查日志文件
LOG_FILE="/root/llm-anonymization/training.log"
if [ -f "$LOG_FILE" ]; then
    echo "=== 📝 最新训练日志 ==="
    tail -30 "$LOG_FILE"
    echo ""
    
    # 统计进度
    echo "=== 📈 训练进度统计 ==="
    PROCESSED=$(grep -o "处理样本 \[[0-9]*/525\]" "$LOG_FILE" | tail -1 | grep -o "[0-9]*" | tail -1)
    if [ -n "$PROCESSED" ]; then
        echo "已处理: $PROCESSED / 525"
        PERCENTAGE=$(awk "BEGIN {printf \"%.1f\", ($PROCESSED/525)*100}")
        echo "完成度: $PERCENTAGE%"
    else
        echo "等待训练开始..."
    fi
else
    echo "⚠ 日志文件不存在"
fi
echo ""

# 检查结果文件
echo "=== 💾 结果文件 ==="
RESULT_DIR="/root/llm-anonymization/training_results"
if [ -d "$RESULT_DIR" ]; then
    ls -lh "$RESULT_DIR" 2>/dev/null || echo "结果目录为空"
else
    echo "结果目录尚未创建"
fi
echo ""

# 估算剩余时间（基于已处理样本）
if [ -n "$PROCESSED" ] && [ "$PROCESSED" -gt 0 ]; then
    START_TIME=$(grep "开始时间:" "$LOG_FILE" | head -1 | awk '{print $2" "$3}')
    if [ -n "$START_TIME" ]; then
        echo "=== ⏱️ 时间估算 ==="
        echo "开始时间: $START_TIME"
        echo "（基于当前速度的剩余时间估算需要更多数据点）"
    fi
fi

echo "========================================"
echo "💡 提示:"
echo "  - 实时日志: tail -f $LOG_FILE"
echo "  - Screen会话: screen -r training"
echo "========================================"
