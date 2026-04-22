#!/bin/bash
CHECK_INTERVAL=180  # 3分钟检查一次
CHECK_COUNT=0

echo "🔍 训练监控已启动" | tee -a /root/llm-anonymization/monitor.log
echo "⏰ 检查间隔: ${CHECK_INTERVAL}秒" | tee -a /root/llm-anonymization/monitor.log
echo "" | tee -a /root/llm-anonymization/monitor.log

while true; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    NOW=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 检查进程
    PROCESS=$(ps aux | grep 'python3.*train_enhanced' | grep -v grep | wc -l)
    
    # 获取进度
    LATEST_SAMPLE=$(grep '处理样本' /root/llm-anonymization/training_full.log 2>/dev/null | tail -1)
    
    # 生成报告
    echo "========================================" | tee -a /root/llm-anonymization/monitor.log
    echo "📊 检查 #${CHECK_COUNT} @ ${NOW}" | tee -a /root/llm-anonymization/monitor.log
    echo "进程状态: $(if [ $PROCESS -gt 0 ]; then echo '运行中 ✅'; else echo '已停止 ⚠️'; fi)" | tee -a /root/llm-anonymization/monitor.log
    echo "${LATEST_SAMPLE}" | tee -a /root/llm-anonymization/monitor.log
    
    # 如果进程已停止，检查是否完成
    if [ $PROCESS -eq 0 ]; then
        if grep -q "训练完成" /root/llm-anonymization/training_full.log 2>/dev/null; then
            echo "✅ 训练已完成！" | tee -a /root/llm-anonymization/monitor.log
            break
        else
            echo "⚠️  训练进程异常停止" | tee -a /root/llm-anonymization/monitor.log
            break
        fi
    fi
    
    echo "下次检查: $(date -d '+${CHECK_INTERVAL} seconds' '+%H:%M:%S')" | tee -a /root/llm-anonymization/monitor.log
    echo "" | tee -a /root/llm-anonymization/monitor.log
    
    sleep $CHECK_INTERVAL
done

echo "监控结束" | tee -a /root/llm-anonymization/monitor.log
