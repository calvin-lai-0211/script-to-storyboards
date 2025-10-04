#!/usr/bin/env python3
"""
Background Task Processor: 处理异步图片生成任务
独立进程，持续运行处理 ai_tasks 表中的任务

Usage:
    python background/task_processor.py
"""
import sys
import time
import logging
import signal
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import Database
from utils.config import DB_CONFIG, TASK_PROCESSOR_CONFIG
from utils.ai_task_manager import AITaskManager, TaskStatus, TaskType, EntityType
from models.jimeng_t2i_RH import JimengT2IRH
from utils.upload import R2Uploader
from utils.config import R2_CONFIG

# 设置日志
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "task_processor.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)


class TaskProcessor:
    """后台任务处理器"""

    def __init__(self):
        self.db = None
        self.task_manager = None
        self.jimeng = None
        self.r2_uploader = None
        self.running = True
        self.consecutive_errors = 0

        # 从配置文件加载配置
        self.poll_interval = TASK_PROCESSOR_CONFIG['poll_interval']
        self.task_timeout = TASK_PROCESSOR_CONFIG['task_timeout']
        self.max_pending_batch = TASK_PROCESSOR_CONFIG['max_pending_batch']
        self.max_active_batch = TASK_PROCESSOR_CONFIG['max_active_batch']
        self.max_consecutive_errors = TASK_PROCESSOR_CONFIG['max_consecutive_errors']

        # 初始化连接
        self._initialize_connections()

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _initialize_connections(self):
        """初始化数据库和服务连接（支持重连）"""
        try:
            logger.info("初始化数据库和服务连接...")
            self.db = Database(DB_CONFIG)
            self.task_manager = AITaskManager(self.db)
            self.jimeng = JimengT2IRH()
            self.r2_uploader = R2Uploader()
            self.consecutive_errors = 0  # 重置错误计数
            logger.info("✅ 连接初始化成功")
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}", exc_info=True)
            raise

    def _signal_handler(self, signum, frame):
        """处理终止信号"""
        logger.info(f"收到信号 {signum}，准备退出...")
        self.running = False

    def run(self):
        """主循环"""
        logger.info("=" * 40)
        logger.info("🚀 Background Task Processor 启动")
        logger.info(f"⚙️  配置: 轮询间隔={self.poll_interval}s, 超时={self.task_timeout}min")
        logger.info("=" * 40)

        loop_count = 0
        while self.running:
            try:
                loop_count += 1
                logger.info(f"\n{'='*40}")
                logger.info(f"🔄 第 {loop_count} 轮任务处理开始")
                logger.info(f"{'='*40}")

                # 1. 处理待提交的任务
                self._process_pending_tasks()

                # 2. 轮询进行中的任务
                self._poll_active_tasks()

                # 3. 处理超时任务
                self._handle_timeout_tasks()

                # 4. 重试失败任务
                self._retry_failed_tasks()

                # 成功完成一轮循环，重置错误计数
                self.consecutive_errors = 0

                logger.info(f"✅ 第 {loop_count} 轮处理完成，等待 {self.poll_interval}s 后开始下一轮\n")

                # 等待下一次循环
                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("收到中断信号，退出...")
                break
            except Exception as e:
                self.consecutive_errors += 1
                logger.error(
                    f"处理任务时发生错误 ({self.consecutive_errors}/{self.max_consecutive_errors}): {e}",
                    exc_info=True
                )

                # 如果连续错误过多，尝试重新初始化连接
                if self.consecutive_errors >= self.max_consecutive_errors:
                    logger.warning(
                        f"⚠️  连续错误 {self.consecutive_errors} 次，尝试重新初始化连接..."
                    )
                    try:
                        self._initialize_connections()
                        logger.info("✅ 重新初始化成功")
                    except Exception as init_error:
                        logger.error(f"❌ 重新初始化失败: {init_error}", exc_info=True)
                        logger.error("等待 60 秒后重试...")
                        time.sleep(60)
                else:
                    # 递增等待时间，避免错误风暴
                    wait_time = min(self.poll_interval * self.consecutive_errors, 30)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

        logger.info("🛑 Background Task Processor 已退出")

    def _process_pending_tasks(self):
        """处理待提交的任务"""
        logger.info("🔍 [步骤1] 查询 PENDING 任务...")
        tasks = self.task_manager.get_pending_tasks(limit=self.max_pending_batch)

        if not tasks:
            logger.info("   ℹ️  没有待处理的 PENDING 任务")
            return

        logger.info(f"   📋 查询到 {len(tasks)} 个 PENDING 任务，开始提交到 RunningHub")

        for task in tasks:
            try:
                self._submit_task(task)
            except Exception as e:
                logger.error(f"提交任务 #{task['id']} 失败: {e}", exc_info=True)
                self.task_manager.update_task(
                    task['id'],
                    status=TaskStatus.FAILED,
                    error_message=f"提交失败: {str(e)}"
                )

    def _submit_task(self, task: Dict[str, Any]):
        """提交单个任务到 RunningHub"""
        task_id = task['id']
        entity_name = task.get('entity_name', 'Unknown')
        prompt = task['prompt']

        logger.info(f"   📤 提交任务 #{task_id} ({entity_name}) 到 RunningHub...")

        # 调用 jimeng.submit_task() 提交
        result = self.jimeng.submit_task(
            prompt=prompt,
            use_concurrency_control=True  # 使用并发控制
        )

        if not result:
            raise Exception("jimeng.submit_task() 返回 None")

        runninghub_task_id = result['task_id']
        logger.info(f"   ✅ 任务 #{task_id} 提交成功 → RunningHub ID: {runninghub_task_id}")

        # 更新数据库状态为 SUBMITTED
        self.task_manager.update_task(
            task_id,
            status=TaskStatus.SUBMITTED,
            runninghub_task_id=runninghub_task_id
        )
        logger.info(f"   💾 数据库状态已更新: #{task_id} → SUBMITTED")

    def _poll_active_tasks(self):
        """轮询进行中的任务"""
        logger.info("🔍 [步骤2] 查询 ACTIVE 任务（SUBMITTED/QUEUED/RUNNING）...")
        tasks = self.task_manager.get_active_tasks(limit=self.max_active_batch)

        if not tasks:
            logger.info("   ℹ️  没有进行中的 ACTIVE 任务")
            return

        logger.info(f"   📋 查询到 {len(tasks)} 个 ACTIVE 任务，开始查询远程状态")

        for task in tasks:
            try:
                self._check_task_status(task)
            except Exception as e:
                logger.error(f"查询任务 #{task['id']} 状态失败: {e}", exc_info=True)

    def _check_task_status(self, task: Dict[str, Any]):
        """查询单个任务状态"""
        task_id = task['id']
        entity_name = task.get('entity_name', 'Unknown')
        current_status = task.get('status', 'UNKNOWN')
        runninghub_task_id = task['task_id']

        if not runninghub_task_id:
            logger.warning(f"   ⚠️  任务 #{task_id} 没有 RunningHub ID，跳过")
            return

        # 调用 jimeng.check_task_status() 查询远程状态
        status_info = self.jimeng.check_task_status(runninghub_task_id)

        if not status_info:
            logger.warning(f"   ⚠️  无法查询任务 #{task_id} 的远程状态")
            return

        remote_status = status_info['status']

        if remote_status in ['QUEUED', 'RUNNING']:
            # 更新状态
            new_status = TaskStatus.QUEUED if remote_status == 'QUEUED' else TaskStatus.RUNNING
            if current_status != new_status.value:
                logger.info(f"   🔄 任务 #{task_id} ({entity_name}) 状态变化: {current_status} → {new_status.value}")
                self.task_manager.update_task(task_id, status=new_status)
                logger.info(f"   💾 数据库状态已更新: #{task_id} → {new_status.value}")

        elif remote_status == 'SUCCESS':
            # 处理成功
            logger.info(f"   🎉 任务 #{task_id} ({entity_name}) 完成！开始后处理...")
            self._handle_task_success(task, status_info)

        elif remote_status in ['FAIL', 'CANCEL']:
            # 处理失败
            error_msg = status_info.get('error', f'任务{remote_status.lower()}')
            logger.error(f"   ❌ 任务 #{task_id} ({entity_name}) 失败: {error_msg}")
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error_message=error_msg
            )
            logger.info(f"   💾 数据库状态已更新: #{task_id} → FAILED")

    def _handle_task_success(self, task: Dict[str, Any], status_info: Dict[str, Any]):
        """处理任务成功"""
        task_id = task['id']
        entity_type = task['entity_type']
        entity_id = task['entity_id']
        entity_name = task.get('entity_name', 'Unknown')

        try:
            # 提取图片 URL
            logger.info(f"      📥 提取图片 URL...")
            result = status_info.get('result')
            if not result:
                raise Exception("No result in status_info")

            images = result.get('data', {}).get('images', [])
            if not images:
                raise Exception("No images in result")

            image_url = images[0].get('imageUrl')
            if not image_url:
                raise Exception("Empty image URL")

            logger.info(f"      ✅ 图片 URL: {image_url[:80]}...")

            # 上传到 R2
            r2_key = self._get_r2_key(task)
            logger.info(f"      📤 上传图片到 R2: {r2_key}")

            cdn_url = self.r2_uploader.upload_from_url(image_url, r2_key)
            if not cdn_url:
                raise Exception("Failed to upload to R2")

            logger.info(f"      ✅ R2 上传成功: {cdn_url}")

            # 更新对应实体的图片 URL
            logger.info(f"      💾 更新实体 {entity_type} #{entity_id} 的图片 URL...")
            self._update_entity_image(entity_type, entity_id, r2_key, task['prompt'])

            # 更新任务状态为成功
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.SUCCESS,
                result_url=cdn_url,
                r2_key=r2_key
            )
            logger.info(f"      💾 数据库状态已更新: #{task_id} → SUCCESS")

            logger.info(f"   🎉 任务 #{task_id} ({entity_name}) 完整流程完成！")

        except Exception as e:
            logger.error(f"   ❌ 任务 #{task_id} 后处理失败: {e}", exc_info=True)
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error_message=f"后处理失败: {str(e)}"
            )
            logger.info(f"   💾 数据库状态已更新: #{task_id} → FAILED")

    def _get_r2_key(self, task: Dict[str, Any]) -> str:
        """生成 R2 存储 key"""
        entity_type = task['entity_type']
        entity_name = task['entity_name']
        episode = task['episode_number']

        if entity_type == EntityType.CHARACTER.value:
            return f"tiangui/{episode}/characters/{entity_name}.jpg"
        elif entity_type == EntityType.SCENE.value:
            return f"tiangui/{episode}/scenes/{entity_name}.jpg"
        elif entity_type == EntityType.PROP.value:
            return f"tiangui/{episode}/props/{entity_name}.jpg"
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

    def _update_entity_image(self, entity_type: str, entity_id: int, r2_key: str, prompt: str):
        """更新实体的图片 URL"""
        table_map = {
            EntityType.CHARACTER.value: 'character_portraits',
            EntityType.SCENE.value: 'scene_definitions',
            EntityType.PROP.value: 'props'
        }

        table = table_map.get(entity_type)
        if not table:
            raise ValueError(f"Unknown entity type: {entity_type}")

        conn = self.db._get_connection()
        try:
            with conn.cursor() as cur:
                # Update both image_url and image_prompt
                cur.execute(
                    f"UPDATE {table} SET image_url = %s, image_prompt = %s WHERE id = %s",
                    (r2_key, prompt, entity_id)
                )
                conn.commit()
                logger.info(f"✅ 更新 {table} #{entity_id} 的图片 URL")
        finally:
            conn.close()

    def _handle_timeout_tasks(self):
        """处理超时任务"""
        logger.info("🔍 [步骤3] 查询超时任务...")
        timeout_tasks = self.task_manager.get_timeout_tasks(timeout_minutes=self.task_timeout)

        if not timeout_tasks:
            logger.info(f"   ℹ️  没有超时任务（超时阈值: {self.task_timeout}分钟）")
            return

        logger.warning(f"   ⏰ 发现 {len(timeout_tasks)} 个超时任务")

        for task in timeout_tasks:
            task_id = task['id']
            entity_name = task.get('entity_name', 'Unknown')
            logger.warning(f"   ⏰ 任务 #{task_id} ({entity_name}) 超时，标记为 TIMEOUT")
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.TIMEOUT,
                error_message=f"任务超时（超过 {self.task_timeout} 分钟）"
            )
            logger.info(f"   💾 数据库状态已更新: #{task_id} → TIMEOUT")

    def _retry_failed_tasks(self):
        """重试失败的任务"""
        logger.info("🔍 [步骤4] 查询可重试的失败任务...")
        retry_tasks = self.task_manager.get_failed_tasks_for_retry()

        if not retry_tasks:
            logger.info("   ℹ️  没有可重试的失败任务")
            return

        logger.info(f"   🔄 发现 {len(retry_tasks)} 个可重试的失败任务")

        for task in retry_tasks:
            task_id = task['id']
            entity_name = task.get('entity_name', 'Unknown')
            retry_count = task['retry_count']
            logger.info(f"   🔄 重试任务 #{task_id} ({entity_name}) - 第 {retry_count + 1} 次重试")
            self.task_manager.reset_task_for_retry(task_id)
            logger.info(f"   💾 数据库状态已更新: #{task_id} → PENDING (retry_count={retry_count + 1})")


def main():
    """主入口"""
    processor = TaskProcessor()
    processor.run()


if __name__ == "__main__":
    main()
