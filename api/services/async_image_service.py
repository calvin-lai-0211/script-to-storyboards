#!/usr/bin/env python3
"""
Async Image Generation Service
统一处理所有实体（角色、场景、道具）的异步图片生成
"""
import logging
from typing import Dict, Any, Optional
from utils.database import Database
from utils.ai_task_manager import AITaskManager, TaskType, EntityType, TaskStatus

logger = logging.getLogger(__name__)


# Entity configuration mapping
ENTITY_CONFIG = {
    EntityType.CHARACTER: {
        "table": "character_portraits",
        "name_field": "character_name",
        "r2_path": "characters",
        "task_type": TaskType.CHARACTER_IMAGE
    },
    EntityType.SCENE: {
        "table": "scene_definitions",
        "name_field": "scene_name",
        "r2_path": "scenes",
        "task_type": TaskType.SCENE_IMAGE
    },
    EntityType.PROP: {
        "table": "key_prop_definitions",
        "name_field": "prop_name",
        "r2_path": "props",
        "task_type": TaskType.PROP_IMAGE
    }
}


class AsyncImageService:
    """
    异步图片生成服务

    提供统一的接口来：
    1. 提交异步生成任务
    2. 查询任务状态
    3. 获取实体信息
    """

    def __init__(self, db: Database):
        self.db = db
        self.task_manager = AITaskManager(db)

    def submit_task(
        self,
        entity_type: EntityType,
        entity_id: int,
        image_prompt: str
    ) -> Dict[str, Any]:
        """
        提交异步图片生成任务

        Args:
            entity_type: 实体类型 (CHARACTER/SCENE/PROP)
            entity_id: 实体ID
            image_prompt: 图片生成提示词

        Returns:
            {
                "task_id": str,
                "status": str,
                "message": str
            }

        Raises:
            ValueError: 实体不存在或配置错误
        """
        # Get entity config
        config = ENTITY_CONFIG.get(entity_type)
        if not config:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        # Query entity info
        entity_info = self._get_entity_info(entity_type, entity_id)
        if not entity_info:
            raise ValueError(f"{entity_type.value} with id {entity_id} not found")

        entity_name = entity_info[config["name_field"]]
        drama_name = entity_info["drama_name"]
        episode_number = entity_info["episode_number"]

        logger.info(f"Creating async task for {entity_type.value} {entity_id} ({entity_name})")

        # Create task in database
        task_id = self.task_manager.create_task(
            task_type=config["task_type"],
            entity_type=entity_type,
            entity_id=entity_id,
            prompt=image_prompt,
            drama_name=drama_name,
            episode_number=episode_number,
            entity_name=entity_name
        )

        logger.info(f"Task created: #{task_id}")

        return {
            "task_id": str(task_id),
            "status": TaskStatus.PENDING.value,
            "message": "Task created successfully, will be processed by background worker"
        }

    def get_task_status(
        self,
        entity_type: EntityType,
        entity_id: int,
        task_id: int
    ) -> Dict[str, Any]:
        """
        查询任务状态

        Args:
            entity_type: 实体类型 (用于验证)
            entity_id: 实体ID (用于验证)
            task_id: 任务ID

        Returns:
            {
                "status": str,
                "image_url": str (仅SUCCESS),
                "error": str (仅FAILED/TIMEOUT)
            }

        Raises:
            ValueError: 任务不存在或不属于该实体
        """
        # Query task
        task = self.task_manager.get_task(task_id)

        if not task:
            raise ValueError("Task not found")

        # Verify task belongs to this entity
        if task["entity_id"] != entity_id or task["entity_type"] != entity_type.value:
            raise ValueError("Task does not belong to this entity")

        task_status = task["status"]

        result = {"status": task_status}

        if task_status == TaskStatus.SUCCESS.value:
            result["image_url"] = task["result_url"]
            result["message"] = "图片生成完成"
        elif task_status in [TaskStatus.FAILED.value, TaskStatus.TIMEOUT.value]:
            result["error"] = task["error_message"] or f"任务{task_status.lower()}"
            result["message"] = result["error"]
        else:
            result["message"] = f"任务{task_status.lower()}"

        return result

    def _get_entity_info(
        self,
        entity_type: EntityType,
        entity_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        查询实体信息

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体信息字典，包含 name_field, drama_name, episode_number
        """
        config = ENTITY_CONFIG.get(entity_type)
        if not config:
            return None

        query = f"""
            SELECT {config['name_field']}, drama_name, episode_number
            FROM {config['table']}
            WHERE id = %s
        """

        logger.debug(f"Query: {query}, params: ({entity_id},)")
        results = self.db.fetch_query(query, (entity_id,))
        logger.debug(f"Query results type: {type(results)}, content: {results}")

        if results and len(results) > 0:
            logger.debug(f"First result type: {type(results[0])}, content: {results[0]}")

        return results[0] if results else None

    @staticmethod
    def get_r2_key(
        entity_type: EntityType,
        episode_number: int,
        entity_name: str
    ) -> str:
        """
        生成 R2 存储 key

        Args:
            entity_type: 实体类型
            episode_number: 集数
            entity_name: 实体名称

        Returns:
            R2 key (例如: "tiangui/1/characters/李明.jpg")
        """
        config = ENTITY_CONFIG.get(entity_type)
        if not config:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        return f"tiangui/{episode_number}/{config['r2_path']}/{entity_name}.jpg"
