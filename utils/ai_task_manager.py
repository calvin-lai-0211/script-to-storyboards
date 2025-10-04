#!/usr/bin/env python3
"""
AI Task Manager: 管理异步图片生成任务
注意：仅用于 API 调用的任务管理，脚本使用方式的话直接调用 generate_image() 不使用此模块
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from utils.database import Database

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "PENDING"       # 待提交到 RunningHub
    SUBMITTED = "SUBMITTED"   # 已提交到 RunningHub，待确认状态
    QUEUED = "QUEUED"         # RunningHub 队列中
    RUNNING = "RUNNING"       # RunningHub 生成中
    SUCCESS = "SUCCESS"       # 成功完成
    FAILED = "FAILED"         # 失败
    TIMEOUT = "TIMEOUT"       # 超时


class TaskType(str, Enum):
    """任务类型枚举"""
    CHARACTER_IMAGE = "character_image"
    SCENE_IMAGE = "scene_image"
    PROP_IMAGE = "prop_image"


class EntityType(str, Enum):
    """实体类型枚举"""
    CHARACTER = "character"
    SCENE = "scene"
    PROP = "prop"


class AITaskManager:
    """AI 任务管理器"""

    def __init__(self, db: Database):
        self.db = db

    def create_task(
        self,
        task_type: TaskType,
        entity_type: EntityType,
        entity_id: int,
        prompt: str,
        drama_name: str = None,
        episode_number: int = None,
        entity_name: str = None,
        max_retries: int = 3
    ) -> int:
        """
        创建新任务

        Args:
            task_type: 任务类型
            entity_type: 实体类型
            entity_id: 实体 ID
            prompt: 生成提示词
            drama_name: 剧名
            episode_number: 集数
            entity_name: 实体名称
            max_retries: 最大重试次数

        Returns:
            任务数据库 ID
        """
        conn = self.db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_tasks (
                        task_type, entity_type, entity_id, prompt,
                        drama_name, episode_number, entity_name, max_retries
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        task_type.value,
                        entity_type.value,
                        entity_id,
                        prompt,
                        drama_name,
                        episode_number,
                        entity_name,
                        max_retries,
                    ),
                )
                task_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"✅ 创建任务 #{task_id}: {task_type.value} for {entity_type.value} {entity_id}")
                return task_id
        finally:
            conn.close()

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        查询任务

        Args:
            task_id: 任务数据库 ID

        Returns:
            任务信息字典，不存在返回 None
        """
        query = "SELECT * FROM ai_tasks WHERE id = %s"
        results = self.db.fetch_query(query, (task_id,))
        return results[0] if results else None

    def get_task_by_runninghub_id(self, runninghub_task_id: str) -> Optional[Dict[str, Any]]:
        """通过 RunningHub task_id 查询任务"""
        query = "SELECT * FROM ai_tasks WHERE task_id = %s"
        results = self.db.fetch_query(query, (runninghub_task_id,))
        return results[0] if results else None

    def update_task(
        self,
        task_id: int,
        status: Optional[TaskStatus] = None,
        runninghub_task_id: Optional[str] = None,
        result_url: Optional[str] = None,
        r2_key: Optional[str] = None,
        error_message: Optional[str] = None,
        increment_retry: bool = False
    ) -> bool:
        """
        更新任务

        Args:
            task_id: 任务数据库 ID
            status: 新状态
            runninghub_task_id: RunningHub 任务 ID
            result_url: 结果图片 URL
            r2_key: R2 存储 key
            error_message: 错误信息
            increment_retry: 是否增加重试计数

        Returns:
            更新是否成功
        """
        updates = []
        params = []

        if status:
            updates.append("status = %s")
            params.append(status.value)

            # 根据状态更新时间戳
            if status == TaskStatus.SUBMITTED:
                updates.append("submitted_at = NOW()")
            elif status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.TIMEOUT]:
                updates.append("completed_at = NOW()")

        if runninghub_task_id:
            updates.append("task_id = %s")
            params.append(runninghub_task_id)

        if result_url is not None:
            updates.append("result_url = %s")
            params.append(result_url)

        if r2_key is not None:
            updates.append("r2_key = %s")
            params.append(r2_key)

        if error_message is not None:
            updates.append("error_message = %s")
            params.append(error_message)

        if increment_retry:
            updates.append("retry_count = retry_count + 1")

        # 更新轮询时间
        if status in [TaskStatus.QUEUED, TaskStatus.RUNNING]:
            updates.append("last_poll_at = NOW()")

        if not updates:
            return False

        params.append(task_id)
        query = f"UPDATE ai_tasks SET {', '.join(updates)} WHERE id = %s"

        conn = self.db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                logger.info(f"✅ 更新任务 #{task_id}: {updates}")
                return True
        except Exception as e:
            logger.error(f"❌ 更新任务 #{task_id} 失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_pending_tasks(self, limit: int = 10, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        获取待提交的任务

        Args:
            limit: 最大返回数量
            max_age_days: 最大任务年龄（天），默认30天

        Returns:
            任务列表
        """
        query = """
            SELECT * FROM ai_tasks
            WHERE status = %s
            AND created_at > NOW() - INTERVAL '%s days'
            ORDER BY created_at ASC
            LIMIT %s
        """
        return self.db.fetch_query(query, (TaskStatus.PENDING.value, max_age_days, limit))

    def get_active_tasks(self, limit: int = 50, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        获取进行中的任务（SUBMITTED, QUEUED, RUNNING）

        Args:
            limit: 最大返回数量
            max_age_days: 最大任务年龄（天），默认30天

        Returns:
            任务列表
        """
        query = """
            SELECT * FROM ai_tasks
            WHERE status IN (%s, %s, %s)
            AND created_at > NOW() - INTERVAL '%s days'
            ORDER BY submitted_at ASC
            LIMIT %s
        """
        return self.db.fetch_query(
            query,
            (TaskStatus.SUBMITTED.value, TaskStatus.QUEUED.value, TaskStatus.RUNNING.value, max_age_days, limit),
        )

    def get_timeout_tasks(self, timeout_minutes: int = 10, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        获取超时的任务

        Args:
            timeout_minutes: 超时时间（分钟）
            max_age_days: 最大任务年龄（天），默认30天

        Returns:
            超时任务列表
        """
        query = """
            SELECT * FROM ai_tasks
            WHERE status IN (%s, %s, %s)
            AND submitted_at < NOW() - INTERVAL '%s minutes'
            AND created_at > NOW() - INTERVAL '%s days'
        """
        return self.db.fetch_query(
            query,
            (
                TaskStatus.SUBMITTED.value,
                TaskStatus.QUEUED.value,
                TaskStatus.RUNNING.value,
                timeout_minutes,
                max_age_days,
            ),
        )

    def get_failed_tasks_for_retry(self, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        获取可重试的失败任务

        Args:
            max_age_days: 最大任务年龄（天），默认30天

        Returns:
            可重试任务列表
        """
        query = """
            SELECT * FROM ai_tasks
            WHERE status = %s
            AND retry_count < max_retries
            AND created_at > NOW() - INTERVAL '%s days'
            ORDER BY created_at ASC
        """
        return self.db.fetch_query(query, (TaskStatus.FAILED.value, max_age_days))

    def reset_task_for_retry(self, task_id: int) -> bool:
        """
        重置任务状态以便重试

        Args:
            task_id: 任务数据库 ID

        Returns:
            是否成功
        """
        return self.update_task(
            task_id,
            status=TaskStatus.PENDING,
            runninghub_task_id=None,
            error_message=None,
            increment_retry=True,
        )

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """
        清理旧任务

        Args:
            days: 保留天数

        Returns:
            删除数量
        """
        query = """
            DELETE FROM ai_tasks
            WHERE created_at < NOW() - INTERVAL '%s days'
            AND status IN (%s, %s)
        """

        conn = self.db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (days, TaskStatus.SUCCESS.value, TaskStatus.FAILED.value))
                deleted_count = cur.rowcount
                conn.commit()
                logger.info(f"🗑️ 清理了 {deleted_count} 个旧任务（{days} 天前）")
                return deleted_count
        finally:
            conn.close()

    def get_task_stats(self) -> Dict[str, int]:
        """
        获取任务统计

        Returns:
            各状态任务数量
        """
        query = """
            SELECT status, COUNT(*) as count
            FROM ai_tasks
            GROUP BY status
        """
        results = self.db.fetch_query(query)
        return {row["status"]: row["count"] for row in results}
