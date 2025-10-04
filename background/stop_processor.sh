#!/bin/bash
# 停止后台任务处理器

cd "$(dirname "$0")/.."

PID_FILE="logs/task_processor.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID file not found: $PID_FILE"
    echo "   Task processor may not be running"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "🛑 Stopping Task Processor (PID: $PID)..."
    kill $PID
    sleep 2

    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Process still running, force killing..."
        kill -9 $PID
    fi

    echo "✅ Task Processor stopped"
    rm -f "$PID_FILE"
else
    echo "ℹ️  Process with PID $PID is not running"
    rm -f "$PID_FILE"
fi
