#!/bin/bash

# LLM Anonymization 可视化系统停止脚本

echo "🛑 停止 LLM Anonymization 可视化系统..."

# 停止后端
if pgrep -f "uvicorn backend.api.main" > /dev/null; then
    echo "停止后端..."
    pkill -f "uvicorn backend.api.main"
    echo "✅ 后端已停止"
else
    echo "✅ 后端未运行"
fi

# 停止前端
if pgrep -f "vite.*3001" > /dev/null; then
    echo "停止前端..."
    pkill -f "vite"
    echo "✅ 前端已停止"
else
    echo "✅ 前端未运行"
fi

echo ""
echo "✅ 所有服务已停止"
