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
from api.models import GenerateDefinitionsRequest, StatusResponse, ApiResponse

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
async def generate_scenes(request: GenerateDefinitionsRequest, response: Response, db: Database = Depends(get_db)):
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

@router.get("/scenes/{drama_name}/{episode_number}")
async def get_scenes(drama_name: str, episode_number: int, response: Response, db: Database = Depends(get_db)):
    """
    Get all scenes for a specific episode.
    """
    try:
        scenes = db.get_scenes_for_episode(drama_name, episode_number)
        return ApiResponse.success(data={
            "drama_name": drama_name,
            "episode_number": episode_number,
            "scenes": scenes,
            "count": len(scenes)
        })
    except Exception as e:
        logger.error(f"Error getting scenes: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
