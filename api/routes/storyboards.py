"""
Storyboard generation endpoints.
"""
import sys
from pathlib import Path
import logging

from fastapi import APIRouter, Depends, Response

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.database import Database
from procedure.make_storyboards import MakeStoryboardsText
from api.middleware.auth import require_auth, UserPrincipal
from api.utils import get_db
from api.schemas import (
    GenerateStoryboardRequest,
    ApiResponse,
    StoryboardResponse,
    MemoryResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

@router.get("/storyboards/{key}", response_model=StoryboardResponse)
async def get_storyboards(
    key: str,
    db: Database = Depends(get_db),
    user: UserPrincipal = Depends(require_auth)
):
    """
    Get all storyboard data for a specific script by key.
    Uses JOIN to query storyboards directly by episode_number.
    """
    try:
        # Join query: scripts -> flat_storyboards by episode_number
        query = """
            SELECT
                s.key,
                s.title as drama_name,
                s.episode_num as episode_number,
                f.id,
                f.scene_number,
                f.scene_description,
                f.shot_number,
                f.shot_description,
                f.sub_shot_number,
                f.camera_angle,
                f.characters,
                f.scene_context,
                f.key_props,
                f.image_prompt,
                f.video_prompt,
                f.dialogue_sound,
                f.duration_seconds,
                f.notes
            FROM scripts s
            LEFT JOIN flat_storyboards f ON s.episode_num = f.episode_number
            WHERE s.key = %s
            ORDER BY f.scene_number, f.shot_number, f.sub_shot_number
        """
        logger.info(f"Query storyboards by key: {key}")
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
            "storyboards": [],
            "count": 0
        }

        # Filter out rows where storyboard id is None (no storyboards yet)
        storyboards = [r for r in results if r.get('id') is not None]
        if storyboards:
            response_data["storyboards"] = storyboards
            response_data["count"] = len(storyboards)

        logger.info(f"Found {response_data['count']} storyboard records for episode {response_data['episode_number']}")
        return ApiResponse.success(data=response_data)

    except Exception as e:
        logger.error(f"Error getting storyboards: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.get("/memory/{key}", response_model=MemoryResponse)
async def get_episode_memory(
    key: str,
    db: Database = Depends(get_db),
    user: UserPrincipal = Depends(require_auth)
):
    """
    Get episode memory/summary by script key.
    Query by episode_number only.
    """
    try:
        # First get episode_number from scripts by key
        script_query = """
            SELECT episode_num FROM scripts WHERE key = %s
        """
        script_results = db.fetch_query(script_query, (key,))

        if not script_results:
            return ApiResponse.error(code=404, message="未找到该剧本")

        episode_number = script_results[0]['episode_num']

        logger.info(f"Searching memory with episode_number={episode_number}")

        # Query memory by episode_number only
        query = """
            SELECT id, script_name, episode_number, plot_summary, options, created_at
            FROM episode_memory
            WHERE episode_number = %s
        """
        results = db.fetch_query(query, (episode_number,))

        if not results:
            return ApiResponse.error(code=404, message="暂无剧集摘要数据")

        memory = results[0]
        return ApiResponse.success(data=memory)
    except Exception as e:
        logger.error(f"Error getting episode memory: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.post("/storyboard/generate")
async def generate_storyboard(
    request: GenerateStoryboardRequest,
    response: Response,
    db: Database = Depends(get_db),
    user: UserPrincipal = Depends(require_auth)
):
    """
    Generate storyboard from script.
    """
    try:
        generator = MakeStoryboardsText()
        generator.generate_storyboard(
            script_title=request.script_title,
            episode_number=request.episode_number,
            force_regen=request.force_regen
        )

        return ApiResponse.success(
            data={
                "script_title": request.script_title,
                "episode_number": request.episode_number
            },
            message=f"Storyboard generated for '{request.script_title}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating storyboard: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
