"""
Script-related endpoints.
"""
import sys
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException, Depends, Response

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.database import Database
from api.models import ApiResponse

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

@router.get("/scripts/{script_title}/episodes")
async def list_episodes(script_title: str, response: Response, db: Database = Depends(get_db)):
    """
    List all episodes for a specific script.
    """
    try:
        query = "SELECT DISTINCT episode_number FROM scripts WHERE drama_name = %s ORDER BY episode_number"
        results = db.fetch_query(query, (script_title,))

        episodes = [row["episode_number"] for row in results]

        return ApiResponse.success(data={
            "script_title": script_title,
            "episodes": episodes,
            "count": len(episodes)
        })
    except Exception as e:
        logger.error(f"Error listing episodes: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
