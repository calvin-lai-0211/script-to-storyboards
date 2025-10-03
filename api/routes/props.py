"""
Props (key props) generation endpoints.
"""
import sys
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException, Depends, Response

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.database import Database
from procedure.generate_key_prop_definitions import KeyPropDefinitionGenerator
from api.schemas import (
    GenerateDefinitionsRequest,
    StatusResponse,
    ApiResponse,
    PropListResponse
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

@router.get("/props/all", response_model=PropListResponse)
async def get_all_props(db: Database = Depends(get_db)):
    """
    Get all props from all scripts.
    """
    try:
        query = """
            SELECT
                id,
                drama_name,
                episode_number,
                prop_name,
                image_prompt,
                reflection,
                version,
                image_url,
                shots_appeared,
                is_key_prop,
                prop_brief,
                created_at
            FROM key_prop_definitions
            ORDER BY drama_name, episode_number, prop_name
        """
        logger.info("Query all props across all scripts")
        results = db.fetch_query(query)

        response_data = {
            "props": results,
            "count": len(results)
        }

        logger.info(f"Found {response_data['count']} props across all scripts")
        return ApiResponse.success(data=response_data)

    except Exception as e:
        logger.error(f"Error getting all props: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.post("/props/generate")
async def generate_props(request: GenerateDefinitionsRequest, response: Response, db: Database = Depends(get_db)):
    """
    Generate key prop definitions for a specific episode.
    """
    try:
        generator = KeyPropDefinitionGenerator(db)
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
            message=f"Key prop definitions generated for '{request.drama_name}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating props: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
