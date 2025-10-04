#!/usr/bin/env python3
"""
本地开发启动脚本
同时启动 API 服务和 Task Processor
"""
import subprocess
import sys
import signal
import time
from pathlib import Path

# 进程列表
processes = []

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    print("\n\n🛑 收到退出信号，正在关闭所有服务...")
    for process in processes:
        if process.poll() is None:  # 进程还在运行
            print(f"   停止进程 PID={process.pid}")
            process.terminate()

    # 等待进程退出
    time.sleep(2)

    # 强制杀死仍在运行的进程
    for process in processes:
        if process.poll() is None:
            print(f"   强制停止进程 PID={process.pid}")
            process.kill()

    print("✅ 所有服务已关闭")
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 确保 logs 目录存在
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("🚀 Script-to-Storyboards 本地开发环境启动")
    print("=" * 70)
    print()

    # 启动 Task Processor（后台进程）
    print("📋 [1/2] 启动 Background Task Processor...")
    task_processor = subprocess.Popen(
        [sys.executable, "background/task_processor.py"]
    )
    processes.append(task_processor)
    print(f"   ✅ Task Processor 已启动 (PID: {task_processor.pid})")
    print(f"   📄 日志输出到: logs/task_processor.log")
    print(f"   💡 查看日志: tail -f logs/task_processor.log")
    print()

    # 等待 1 秒确保 Task Processor 启动
    time.sleep(1)

    # 启动 API 服务（前台进程，显示日志）
    print("🌐 [2/2] 启动 API 服务...")
    print("   📄 API 日志将在下方显示")
    print("   🌍 API URL: http://localhost:8001")
    print()
    print("=" * 70)
    print("💡 提示:")
    print("   - 按 Ctrl+C 可同时停止 API 和 Task Processor")
    print("   - API 日志会实时显示在下方")
    print("   - Task Processor 日志可通过以下命令查看:")
    print("     tail -f logs/task_processor.log")
    print("=" * 70)
    print()

    # 启动 API（前台运行，输出日志到控制台）
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app",
         "--host", "0.0.0.0", "--port", "8001", "--reload"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(api_process)

    # 等待 API 进程结束（正常情况下会一直运行）
    try:
        api_process.wait()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
