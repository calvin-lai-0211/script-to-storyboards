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
