"""
Scene-related endpoints.
"""
import sys
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException, Depends, Response

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.database import Database
from procedure.generate_scene_definitions import SceneDefinitionGenerator
from api.middleware.auth import require_auth, UserPrincipal
from api.schemas import (
    GenerateDefinitionsRequest,
    StatusResponse,
    ApiResponse,
    SceneListResponse,
    ScenesByKeyResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Database dependency
def get_db():
    """Create a new database instance for each request."""
    from utils.config import DB_CONFIG
    db = Database(DB_CONFIG)
    try:
        yield db
    finally:
        pass

@router.post("/scenes/generate")
async def generate_scenes(request: GenerateDefinitionsRequest, response: Response, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Generate scene definitions for a specific episode.
    """
    try:
        generator = SceneDefinitionGenerator(db)
        generator.generate(
            drama_name=request.drama_name,
            episode_number=request.episode_number,
            force_regen=request.force_regen
        )

        return ApiResponse.success(
            data={
                "drama_name": request.drama_name,
                "episode_number": request.episode_number
            },
            message=f"Scene definitions generated for '{request.drama_name}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating scenes: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.get("/scenes/all", response_model=SceneListResponse)
async def get_all_scenes(db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Get all scenes from all scripts.
    """
    try:
        query = """
            SELECT
                id,
                drama_name,
                episode_number,
                scene_name,
                image_prompt,
                reflection,
                image_url
            FROM scene_definitions
            ORDER BY drama_name, episode_number, scene_name
        """
        logger.info("Query all scenes across all scripts")
        results = db.fetch_query(query)

        response_data = {
            "scenes": results,
            "count": len(results)
        }

        logger.info(f"Found {response_data['count']} scenes across all scripts")
        return ApiResponse.success(data=response_data)

    except Exception as e:
        logger.error(f"Error getting all scenes: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.get("/scene/{scene_id}")
async def get_scene(scene_id: int, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Get scene details by ID.
    """
    try:
        query = """
            SELECT id, drama_name, episode_number, scene_name,
                   image_prompt, reflection, version, image_url,
                   shots_appeared, is_key_scene, scene_brief, created_at
            FROM scene_definitions
            WHERE id = %s
        """
        results = db.fetch_query(query, (scene_id,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该场景")

        scene = results[0]
        return ApiResponse.success(data={
            "id": scene["id"],
            "drama_name": scene["drama_name"],
            "episode_number": scene["episode_number"],
            "scene_name": scene["scene_name"],
            "image_prompt": scene["image_prompt"],
            "reflection": scene["reflection"],
            "version": scene["version"],
            "image_url": scene["image_url"],
            "shots_appeared": scene["shots_appeared"],
            "is_key_scene": scene["is_key_scene"],
            "scene_brief": scene["scene_brief"],
            "created_at": scene["created_at"].isoformat() if scene["created_at"] else None
        })
    except Exception as e:
        logger.error(f"Error getting scene: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.get("/scenes/{key}", response_model=ScenesByKeyResponse)
async def get_scenes(key: str, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Get all scenes by script key using JOIN query.
    """
    try:
        # Join query: scripts -> scene_definitions by episode_number
        query = """
            SELECT
                s.key,
                s.title as drama_name,
                s.episode_num as episode_number,
                sc.id,
                sc.scene_name,
                sc.image_prompt,
                sc.reflection,
                sc.image_url
            FROM scripts s
            LEFT JOIN scene_definitions sc ON s.episode_num = sc.episode_number
            WHERE s.key = %s
            ORDER BY sc.scene_name
        """
        logger.info(f"Query scenes by key: {key}")
        results = db.fetch_query(query, (key,))

        if not results:
            logger.warning(f"Script not found for key: {key}")
            return ApiResponse.error(code=404, message="未找到该剧本")

        # Extract metadata from first row
        first_row = results[0]
        response_data = {
            "key": first_row['key'],
            "drama_name": first_row['drama_name'],
            "episode_number": first_row['episode_number'],
            "scenes": [],
            "count": 0
        }

        # Filter out rows where scene id is None
        scenes = [r for r in results if r.get('id') is not None]
        if scenes:
            response_data["scenes"] = scenes
            response_data["count"] = len(scenes)

        logger.info(f"Found {response_data['count']} scenes for episode {response_data['episode_number']}")
        return ApiResponse.success(data=response_data)

    except Exception as e:
        logger.error(f"Error getting scenes: {e}")
        return ApiResponse.error(code=500, message=str(e))
