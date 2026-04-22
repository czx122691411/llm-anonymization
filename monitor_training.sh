#!/bin/bash
echo "🚀 增强版训练实时监控"
echo "=================="
while true; do
    clear
    echo "📊 最新训练日志 (最后30行):"
    echo "=================="
    tail -30 /root/llm-anonymization/training_full.log 2>/dev/null || echo "等待日志..."
    echo ""
    echo "📈 当前进度:"
    echo "=================="
    grep "处理样本" /root/llm-anonymization/training_full.log 2>/dev/null | tail -1
    echo ""
    echo "按 Ctrl+C 退出监控"
    sleep 5
done
