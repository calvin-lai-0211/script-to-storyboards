#!/bin/bash
# 启动后台任务处理器

# 切换到项目根目录
cd "$(dirname "$0")/.."

echo "🚀 Starting Background Task Processor..."

# 使用 nohup 在后台运行
nohup python3 background/task_processor.py > logs/task_processor.log 2>&1 &

PID=$!
echo "✅ Task Processor started with PID: $PID"
echo $PID > logs/task_processor.pid

echo "📋 Log file: logs/task_processor.log"
echo "   Use 'tail -f logs/task_processor.log' to monitor"
