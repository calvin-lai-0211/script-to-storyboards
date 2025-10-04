"""
Character-related endpoints.
"""
import sys
from pathlib import Path
import logging

from fastapi import APIRouter, Depends, Response

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.database import Database
from procedure.generate_character_portraits import CharacterPortraitGenerator
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
    ApiResponse,
    CharacterListResponse,
    CharactersByKeyResponse,
    CharacterDetailResponse,
    GenerateImageResponse
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

@router.post("/characters/generate")
async def generate_characters(request: GenerateDefinitionsRequest, response: Response, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Generate character portrait definitions for a specific episode.
    """
    try:
        generator = CharacterPortraitGenerator(db)
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
            message=f"Character portraits generated for '{request.drama_name}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating characters: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.get("/characters/all", response_model=CharacterListResponse)
async def get_all_characters(db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Get all characters from all scripts.
    """
    try:
        query = """
            SELECT
                id,
                drama_name,
                episode_number,
                character_name,
                image_prompt,
                reflection,
                image_url,
                is_key_character,
                character_brief
            FROM character_portraits
            ORDER BY drama_name, episode_number, is_key_character DESC, character_name
        """
        logger.info("Query all characters across all scripts")
        results = db.fetch_query(query)

        response_data = {
            "characters": results,
            "count": len(results)
        }

        # Convert image_url (R2 keys) to CDN URLs
        for char in response_data['characters']:
            char['image_url'] = to_cdn_url(char.get('image_url'))

        logger.info(f"Found {response_data['count']} characters across all scripts")
        return ApiResponse.success(data=response_data)

    except Exception as e:
        logger.error(f"Error getting all characters: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.get("/characters/{key}", response_model=CharactersByKeyResponse)
async def get_characters(key: str, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Get all characters by script key using JOIN query.
    """
    try:
        # Join query: scripts -> character_portraits by episode_number
        query = """
            SELECT
                s.key,
                s.title as drama_name,
                s.episode_num as episode_number,
                c.id,
                c.character_name,
                c.image_prompt,
                c.reflection,
                c.image_url,
                c.is_key_character,
                c.character_brief
            FROM scripts s
            LEFT JOIN character_portraits c ON s.episode_num = c.episode_number
            WHERE s.key = %s
            ORDER BY c.is_key_character DESC, c.character_name
        """
        logger.info(f"Query characters by key: {key}")
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
            "characters": [],
            "count": 0
        }

        # Filter out rows where character id is None
        characters = [r for r in results if r.get('id') is not None]
        if characters:
            response_data["characters"] = characters
            response_data["count"] = len(characters)

        logger.info(f"Found {response_data['count']} characters for episode {response_data['episode_number']}")
        return ApiResponse.success(data=response_data)

    except Exception as e:
        logger.error(f"Error getting characters: {e}")
        return ApiResponse.error(code=500, message=str(e))

@router.get("/character/{character_id}", response_model=CharacterDetailResponse)
async def get_character(character_id: int, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Get character details by ID.
    """
    try:
        query = """
            SELECT id, drama_name, episode_number, character_name,
                   image_prompt, reflection, image_url, is_key_character, character_brief
            FROM character_portraits
            WHERE id = %s
        """
        results = db.fetch_query(query, (character_id,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该角色")

        character = results[0]
        return ApiResponse.success(data={
            "id": character["id"],
            "drama_name": character["drama_name"],
            "episode_number": character["episode_number"],
            "character_name": character["character_name"],
            "image_prompt": character["image_prompt"],
            "reflection": character["reflection"],
            "image_url": to_cdn_url(character["image_url"]),
            "is_key_character": character["is_key_character"],
            "character_brief": character["character_brief"]
        })
    except Exception as e:
        logger.error(f"Error getting character: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.put("/character/{character_id}/prompt")
async def update_character_prompt(character_id: int, request: dict, response: Response, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Update character image prompt.
    """
    try:
        image_prompt = request.get("image_prompt")
        if not image_prompt:
            response.status_code = 400
            return ApiResponse.error(code=400, message="image_prompt is required")

        # First verify the character exists
        query_check = "SELECT id FROM character_portraits WHERE id = %s"
        results = db.fetch_query(query_check, (character_id,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该角色")

        # Update the prompt
        conn = db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE character_portraits SET image_prompt = %s WHERE id = %s",
                    (image_prompt, character_id)
                )
                conn.commit()
        finally:
            conn.close()

        return ApiResponse.success(
            data={"character_id": character_id},
            message="Prompt updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating character prompt: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.post("/character/{character_id}/generate-image", response_model=GenerateImageResponse)
async def generate_character_image(character_id: int, request: GenerateImageRequest, response: Response, db: Database = Depends(get_db), user: UserPrincipal = Depends(require_auth)):
    """
    Generate character portrait image using Jimeng text-to-image.
    Accepts prompt in request body, queries other data from database.
    """
    try:
        # Get image prompt from request
        image_prompt = request.image_prompt

        if not image_prompt or not image_prompt.strip():
            response.status_code = 400
            return ApiResponse.error(code=400, message="image_prompt is required")

        # Query character info from database
        query = """
            SELECT character_name, drama_name, episode_number
            FROM character_portraits
            WHERE id = %s
        """
        results = db.fetch_query(query, (character_id,))

        if not results:
            return ApiResponse.error(code=404, message="未找到该角色")

        character = results[0]
        character_name = character["character_name"]
        drama_name = character["drama_name"]
        episode_number = character["episode_number"]

        # Generate image using Jimeng
        logger.info(f"Generating image for character {character_id} ({character_name})")
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
        r2_key = f"tiangui/{episode_number}/characters/{character_name}.jpg"

        logger.info(f"Uploading image to R2: {r2_key}...")
        cdn_url = r2_uploader.upload_from_url(image_url, r2_key)

        if not cdn_url:
            logger.error("Failed to upload image to R2")
            response.status_code = 500
            return ApiResponse.error(code=500, message="Failed to upload image to R2")

        logger.info(f"Successfully uploaded to R2: {cdn_url}")

        # Step 3: Download to local storage (optional, for backup)
        output_dir = Path(f"images/{drama_name}/{episode_number}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{character_name}.jpg")

        logger.info(f"Downloading image to local: {output_path}...")
        saved_path = jimeng._download_image(image_url, output_path)

        if not saved_path:
            logger.warning("Failed to download image locally, but R2 upload succeeded")

        # Update database with R2 key (not full URL) and prompt
        conn = db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE character_portraits SET image_url = %s, image_prompt = %s WHERE id = %s",
                    (r2_key, image_prompt, character_id)
                )
                conn.commit()
        finally:
            conn.close()

        logger.info(f"Successfully generated image for character {character_id}")
        logger.info(f"  R2 Key: {r2_key}")
        logger.info(f"  CDN URL: {cdn_url}")
        if saved_path:
            logger.info(f"  Local: {saved_path}")

        return ApiResponse.success(
            data={
                "character_id": character_id,
                "image_url": cdn_url,  # Return full CDN URL to frontend
                "r2_key": r2_key,
                "local_path": saved_path
            },
            message="Image generated and uploaded successfully"
        )

    except Exception as e:
        logger.error(f"Error generating character image: {e}", exc_info=True)
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
