#!/usr/bin/env python3
"""
Test async jimeng task submission and polling
"""
import time
from models.jimeng_t2i_RH import JimengT2IRH

def test_async_generation():
    """Test async image generation with polling"""
    generator = JimengT2IRH()

    test_prompt = "一位年轻的中国女性，长发披肩，穿着白色衬衫，微笑着看向镜头"

    print(f"=== 测试异步生成流程 ===")
    print(f"提示词: {test_prompt}\n")

    # Step 1: Submit task
    print("Step 1: 提交任务...")
    task_info = generator.submit_task(prompt=test_prompt, use_concurrency_control=True)

    if not task_info:
        print("❌ 任务提交失败")
        return

    task_id = task_info["task_id"]
    print(f"✅ 任务提交成功!")
    print(f"  Task ID: {task_id}")
    print(f"  初始状态: {task_info['status']}\n")

    # Step 2: Poll status manually
    print("Step 2: 开始轮询任务状态...")
    max_polls = 60  # Max 3 minutes (60 * 3s)
    poll_count = 0

    while poll_count < max_polls:
        poll_count += 1

        status_info = generator.check_task_status(task_id)

        if not status_info:
            print(f"❌ 第 {poll_count} 次轮询失败")
            time.sleep(3)
            continue

        status = status_info["status"]
        print(f"  [{poll_count}] 状态: {status}")

        if status == "SUCCESS":
            print(f"\n✅ 任务完成!")
            result = status_info.get("result")
            if result:
                images = result.get('data', {}).get('images', [])
                if images:
                    image_url = images[0].get('imageUrl')
                    print(f"  图片URL: {image_url}")
            break
        elif status in ["FAIL", "CANCEL"]:
            error = status_info.get("error", "未知错误")
            print(f"\n❌ 任务失败: {error}")
            break

        time.sleep(3)

    if poll_count >= max_polls:
        print("\n❌ 轮询超时")

if __name__ == "__main__":
    test_async_generation()
