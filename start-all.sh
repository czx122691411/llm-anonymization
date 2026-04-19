#!/bin/bash

PROJECT_DIR="/home/rooter/llm-anonymization"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

echo "🚀 启动 LLM Anonymization 可视化系统..."

# 检查并启动后端
if ! pgrep -f "uvicorn backend.api.main" > /dev/null; then
    echo "📡 启动后端 API (端口 8000)..."
    cd "$PROJECT_DIR"
    conda run -n py310 nohup uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload > "$PROJECT_DIR/logs/backend.log" 2>&1 &
    sleep 2
    echo "✅ 后端已启动"
else
    echo "✅ 后端已在运行"
fi

# 检查并启动前端
if ! pgrep -f "vite.*3001" > /dev/null; then
    echo "🎨 启动前端界面 (端口 3001)..."
    cd "$PROJECT_DIR/frontend"
    nohup npm run dev > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
    sleep 3
    echo "✅ 前端已启动"
else
    echo "✅ 前端已在运行"
fi

echo ""
echo "🌐 访问地址："
echo "  前端: http://localhost:3001"
echo "  后端: http://localhost:8000"
echo ""
echo "📝 查看日志："
echo "  后端: tail -f $PROJECT_DIR/logs/backend.log"
echo "  前端: tail -f $PROJECT_DIR/logs/frontend.log"
