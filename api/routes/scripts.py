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
from api.schemas import (
    ApiResponse,
    ScriptListResponse,
    ScriptDetailResponse
)
from api.middleware.auth import require_auth, UserPrincipal

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

@router.get("/scripts", response_model=ScriptListResponse)
async def get_all_scripts(
    response: Response,
    db: Database = Depends(get_db),
    user: UserPrincipal = Depends(require_auth)
):
    """
    Get all scripts with metadata (title, episode_num, author, creation_year).
    """
    try:
        query = """
            SELECT script_id, key, title, episode_num, author, creation_year, score
            FROM scripts
            ORDER BY creation_year DESC NULLS LAST, title ASC, episode_num ASC
        """
        results = db.fetch_query(query)

        return ApiResponse.success(data={
            "scripts": results,
            "count": len(results)
        })
    except Exception as e:
        logger.error(f"Error getting scripts: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.get("/scripts/{key}", response_model=ScriptDetailResponse)
async def get_script(
    key: str,
    db: Database = Depends(get_db),
    user: UserPrincipal = Depends(require_auth)
):
    """
    Get script content by key.
    """
    try:
        query = """
            SELECT script_id, key, title, episode_num, content, roles, sceneries,
                   author, creation_year, score
            FROM scripts
            WHERE key = %s
        """
        results = db.fetch_query(query, (key,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该剧本")

        script = results[0]
        return ApiResponse.success(data=script)
    except Exception as e:
        logger.error(f"Error getting script: {e}")
        return ApiResponse.error(code=500, message=str(e))
