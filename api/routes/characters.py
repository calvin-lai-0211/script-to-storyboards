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
from api.models import GenerateDefinitionsRequest, GenerateImageRequest, ApiResponse

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
async def generate_characters(request: GenerateDefinitionsRequest, response: Response, db: Database = Depends(get_db)):
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

@router.get("/characters/{drama_name}/{episode_number}")
async def get_characters(drama_name: str, episode_number: int, response: Response, db: Database = Depends(get_db)):
    """
    Get all characters for a specific episode.
    """
    try:
        characters = db.get_characters_for_episode(drama_name, episode_number)
        return ApiResponse.success(data={
            "drama_name": drama_name,
            "episode_number": episode_number,
            "characters": characters,
            "count": len(characters)
        })
    except Exception as e:
        logger.error(f"Error getting characters: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.get("/character/{character_id}")
async def get_character(character_id: int, response: Response, db: Database = Depends(get_db)):
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
            response.status_code = 404
            return ApiResponse.error(code=404, message="Character not found")

        character = results[0]
        return ApiResponse.success(data={
            "id": character["id"],
            "drama_name": character["drama_name"],
            "episode_number": character["episode_number"],
            "character_name": character["character_name"],
            "image_prompt": character["image_prompt"],
            "reflection": character["reflection"],
            "image_url": character["image_url"],
            "is_key_character": character["is_key_character"],
            "character_brief": character["character_brief"]
        })
    except Exception as e:
        logger.error(f"Error getting character: {e}")
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.put("/character/{character_id}/prompt")
async def update_character_prompt(character_id: int, request: dict, response: Response, db: Database = Depends(get_db)):
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
            response.status_code = 404
            return ApiResponse.error(code=404, message="Character not found")

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

@router.post("/character/{character_id}/generate-image")
async def generate_character_image(character_id: int, request: GenerateImageRequest, response: Response, db: Database = Depends(get_db)):
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
            response.status_code = 404
            return ApiResponse.error(code=404, message="Character not found")

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

        # Step 2: Download image to local storage
        output_dir = Path(f"images/{drama_name}/{episode_number}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{character_name}.jpg")

        logger.info(f"Downloading image to {output_path}...")
        saved_path = jimeng._download_image(image_url, output_path)

        if not saved_path:
            logger.warning("Failed to download image, but URL is available")
            # Continue anyway since we have the URL

        # Update database with new image URL and prompt
        conn = db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE character_portraits SET image_url = %s, image_prompt = %s WHERE id = %s",
                    (image_url, image_prompt, character_id)
                )
                conn.commit()
        finally:
            conn.close()

        logger.info(f"Successfully generated image for character {character_id}")
        if saved_path:
            logger.info(f"  Local: {saved_path}")
        logger.info(f"  URL: {image_url}")

        return ApiResponse.success(
            data={
                "character_id": character_id,
                "image_url": image_url,
                "local_path": saved_path
            },
            message="Image generated and saved successfully"
        )

    except Exception as e:
        logger.error(f"Error generating character image: {e}", exc_info=True)
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
