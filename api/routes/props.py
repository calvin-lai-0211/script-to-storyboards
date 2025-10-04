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
from models.jimeng_t2i_RH import JimengT2IRH
from utils.upload import R2Uploader
from utils.config import R2_CONFIG
from api.middleware.auth import require_auth, UserPrincipal

def to_cdn_url(image_url: str) -> str:
    """Convert image_url (R2 key or full URL) to CDN URL."""
    if not image_url:
        return None
    # If already a full URL, return as is
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url
    # Otherwise treat as R2 key and prepend CDN base URL
    return f"{R2_CONFIG['cdn_base_url']}/{image_url}"
from api.schemas import (
    GenerateDefinitionsRequest,
    GenerateImageRequest,
    StatusResponse,
    ApiResponse,
    PropListResponse,
    PropDetailResponse,
    GeneratePropImageResponse
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

@router.get("/prop/{prop_id}", response_model=PropDetailResponse)
async def get_prop(prop_id: int, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Get prop details by ID.
    """
    try:
        query = """
            SELECT id, drama_name, episode_number, prop_name,
                   image_prompt, reflection, version, image_url,
                   shots_appeared, is_key_prop, prop_brief, created_at
            FROM key_prop_definitions
            WHERE id = %s
        """
        results = db.fetch_query(query, (prop_id,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该道具")

        prop = results[0]
        return ApiResponse.success(data={
            "id": prop["id"],
            "drama_name": prop["drama_name"],
            "episode_number": prop["episode_number"],
            "prop_name": prop["prop_name"],
            "image_prompt": prop["image_prompt"],
            "reflection": prop["reflection"],
            "version": prop["version"],
            "image_url": to_cdn_url(prop["image_url"]),
            "shots_appeared": prop["shots_appeared"],
            "is_key_prop": prop["is_key_prop"],
            "prop_brief": prop["prop_brief"],
            "created_at": prop["created_at"].isoformat() if prop["created_at"] else None
        })
    except Exception as e:
        logger.error(f"Error getting prop {prop_id}: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.get("/props/all", response_model=PropListResponse)
async def get_all_props(db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
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

        # Convert image_url (R2 keys) to CDN URLs
        for prop in response_data['props']:
            prop['image_url'] = to_cdn_url(prop.get('image_url'))

        logger.info(f"Found {response_data['count']} props across all scripts")
        return ApiResponse.success(data=response_data)

    except Exception as e:
        logger.error(f"Error getting all props: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.post("/props/generate")
async def generate_props(request: GenerateDefinitionsRequest, response: Response, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
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

@router.put("/prop/{prop_id}/prompt")
async def update_prop_prompt(prop_id: int, request: dict, response: Response, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Update prop image prompt.
    """
    try:
        image_prompt = request.get("image_prompt")
        if not image_prompt:
            response.status_code = 400
            return ApiResponse.error(code=400, message="image_prompt is required")

        # First verify the prop exists
        query_check = "SELECT id FROM key_prop_definitions WHERE id = %s"
        results = db.fetch_query(query_check, (prop_id,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该道具")

        # Update the prompt
        conn = db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE key_prop_definitions SET image_prompt = %s WHERE id = %s",
                    (image_prompt, prop_id)
                )
                conn.commit()
        finally:
            conn.close()

        return ApiResponse.success(
            data={"prop_id": prop_id},
            message="Prompt updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating prop prompt: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.post("/prop/{prop_id}/generate-image", response_model=GeneratePropImageResponse)
async def generate_prop_image(prop_id: int, request: GenerateImageRequest, response: Response, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Generate prop image using Jimeng text-to-image.
    Accepts prompt in request body, queries other data from database.
    """
    try:
        # Get image prompt from request
        image_prompt = request.image_prompt

        if not image_prompt or not image_prompt.strip():
            response.status_code = 400
            return ApiResponse.error(code=400, message="image_prompt is required")

        # Query prop info from database
        query = """
            SELECT prop_name, drama_name, episode_number
            FROM key_prop_definitions
            WHERE id = %s
        """
        results = db.fetch_query(query, (prop_id,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该道具")

        prop = results[0]
        prop_name = prop["prop_name"]
        drama_name = prop["drama_name"]
        episode_number = prop["episode_number"]

        # Generate image using Jimeng
        logger.info(f"Generating image for prop {prop_id} ({prop_name})")
        logger.info(f"  Prompt: {image_prompt[:100]}...")

        jimeng = JimengT2IRH()

        # Step 1: Generate image and get URL
        result = jimeng.generate_image(prompt=image_prompt, use_concurrency_control=True)

        if not result or result.get('code') != 0:
            logger.error(f"Failed to generate image: {result}")
            response.status_code = 500
            return ApiResponse.error(code=500, message="Image generation failed")

        # Extract image URL from result
        images = result.get('data', {}).get('images', [])
        if not images:
            response.status_code = 500
            return ApiResponse.error(code=500, message="No images returned from generation")

        image_url = images[0].get('imageUrl')
        if not image_url:
            response.status_code = 500
            return ApiResponse.error(code=500, message="Empty image URL")

        # Step 2: Upload to R2
        r2_uploader = R2Uploader()
        r2_key = f"tiangui/{episode_number}/props/{prop_name}.jpg"

        logger.info(f"Uploading image to R2: {r2_key}...")
        cdn_url = r2_uploader.upload_from_url(image_url, r2_key)

        if not cdn_url:
            logger.error("Failed to upload image to R2")
            response.status_code = 500
            return ApiResponse.error(code=500, message="Failed to upload image to R2")

        logger.info(f"Successfully uploaded to R2: {cdn_url}")

        # Step 3: Download to local storage (optional, for backup)
        output_dir = Path(f"images/{drama_name}/{episode_number}/props")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{prop_name}.jpg")

        logger.info(f"Downloading image to local: {output_path}...")
        saved_path = jimeng._download_image(image_url, output_path)

        if not saved_path:
            logger.warning("Failed to download image locally, but R2 upload succeeded")

        # Update database with R2 key (not full URL) and prompt
        conn = db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE key_prop_definitions SET image_url = %s, image_prompt = %s WHERE id = %s",
                    (r2_key, image_prompt, prop_id)
                )
                conn.commit()
        finally:
            conn.close()

        logger.info(f"Successfully generated image for prop {prop_id}")
        logger.info(f"  R2 Key: {r2_key}")
        logger.info(f"  CDN URL: {cdn_url}")
        if saved_path:
            logger.info(f"  Local: {saved_path}")

        return ApiResponse.success(
            data={
                "prop_id": prop_id,
                "image_url": cdn_url,  # Return full CDN URL to frontend
                "r2_key": r2_key,
                "local_path": saved_path
            },
            message="Image generated and uploaded successfully"
        )

    except Exception as e:
        logger.error(f"Error generating prop image: {e}", exc_info=True)
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
