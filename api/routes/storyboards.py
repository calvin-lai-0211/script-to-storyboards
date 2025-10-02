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
from api.models import GenerateStoryboardRequest, ApiResponse

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

@router.post("/storyboard/generate")
async def generate_storyboard(request: GenerateStoryboardRequest, response: Response, db: Database = Depends(get_db)):
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
