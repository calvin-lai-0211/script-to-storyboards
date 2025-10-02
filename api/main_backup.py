"""
FastAPI main application entry point.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path
import signal
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import Database
from utils.config import DB_CONFIG
from procedure.make_storyboards import MakeStoryboardsText
from procedure.generate_character_portraits import CharacterPortraitGenerator
from procedure.generate_scene_definitions import SceneDefinitionGenerator
from procedure.generate_key_prop_definitions import KeyPropDefinitionGenerator
from models.jimeng_t2i_RH import JimengT2IRH

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Script-to-Storyboards API",
    description="Automated storyboard generation from text scripts",
    version="0.1.0"
)

# API Router with /api prefix
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency - create new instance per request
def get_db():
    """Create a new database instance for each request."""
    db = Database(DB_CONFIG)
    try:
        yield db
    finally:
        # Cleanup if needed
        pass

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Request/Response models
class GenerateStoryboardRequest(BaseModel):
    script_title: str
    episode_number: int
    force_regen: bool = False

class GenerateDefinitionsRequest(BaseModel):
    drama_name: str
    episode_number: int
    force_regen: bool = False

class StatusResponse(BaseModel):
    status: str
    message: str

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Script-to-Storyboards API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@api_router.post("/storyboard/generate", response_model=StatusResponse)
async def generate_storyboard(request: GenerateStoryboardRequest, db: Database = Depends(get_db)):
    """
    Generate storyboard for a specific episode.
    """
    try:
        generator = MakeStoryboardsText(db)
        result = generator.generate(
            base_script_title=request.script_title,
            episode_number=request.episode_number,
            force_regen=request.force_regen
        )

        if result is None and not request.force_regen:
            return StatusResponse(
                status="skipped",
                message=f"Storyboard already exists for '{request.script_title}' Episode {request.episode_number}"
            )

        return StatusResponse(
            status="success",
            message=f"Storyboard generated for '{request.script_title}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating storyboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/characters/generate", response_model=StatusResponse)
async def generate_characters(request: GenerateDefinitionsRequest, db: Database = Depends(get_db)):
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

        return StatusResponse(
            status="success",
            message=f"Character portraits generated for '{request.drama_name}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating characters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/scenes/generate", response_model=StatusResponse)
async def generate_scenes(request: GenerateDefinitionsRequest, db: Database = Depends(get_db)):
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

        return StatusResponse(
            status="success",
            message=f"Scene definitions generated for '{request.drama_name}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating scenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/props/generate", response_model=StatusResponse)
async def generate_props(request: GenerateDefinitionsRequest, db: Database = Depends(get_db)):
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

        return StatusResponse(
            status="success",
            message=f"Key prop definitions generated for '{request.drama_name}' Episode {request.episode_number}"
        )
    except Exception as e:
        logger.error(f"Error generating props: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/scripts/{script_title}/episodes")
async def list_episodes(script_title: str, db: Database = Depends(get_db)):
    """
    List all available episodes for a script.
    """
    try:
        episodes = db.get_episode_numbers_for_drama(script_title)
        return {
            "script_title": script_title,
            "episodes": episodes,
            "count": len(episodes)
        }
    except Exception as e:
        logger.error(f"Error listing episodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/characters/{drama_name}/{episode_number}")
async def get_characters(drama_name: str, episode_number: int, db: Database = Depends(get_db)):
    """
    Get all characters for a specific episode.
    """
    try:
        characters = db.get_characters_for_episode(drama_name, episode_number)
        return {
            "drama_name": drama_name,
            "episode_number": episode_number,
            "characters": characters,
            "count": len(characters)
        }
    except Exception as e:
        logger.error(f"Error getting characters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/scenes/{drama_name}/{episode_number}")
async def get_scenes(drama_name: str, episode_number: int, db: Database = Depends(get_db)):
    """
    Get all scenes for a specific episode.
    """
    try:
        scenes = db.get_scenes_for_episode(drama_name, episode_number)
        return {
            "drama_name": drama_name,
            "episode_number": episode_number,
            "scenes": scenes,
            "count": len(scenes)
        }
    except Exception as e:
        logger.error(f"Error getting scenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/character/{character_id}")
async def get_character(character_id: int, db: Database = Depends(get_db)):
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
            raise HTTPException(status_code=404, detail="Character not found")

        character = results[0]
        return {
            "id": character["id"],
            "drama_name": character["drama_name"],
            "episode_number": character["episode_number"],
            "character_name": character["character_name"],
            "image_prompt": character["image_prompt"],
            "reflection": character["reflection"],
            "image_url": character["image_url"],
            "is_key_character": character["is_key_character"],
            "character_brief": character["character_brief"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting character: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/character/{character_id}/prompt")
async def update_character_prompt(character_id: int, request: dict, db: Database = Depends(get_db)):
    """
    Update character image prompt.
    """
    try:
        image_prompt = request.get("image_prompt")
        if not image_prompt:
            raise HTTPException(status_code=400, detail="image_prompt is required")

        # First verify the character exists
        query_check = "SELECT id FROM character_portraits WHERE id = %s"
        results = db.fetch_query(query_check, (character_id,))

        if not results:
            raise HTTPException(status_code=404, detail="Character not found")

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

        return {"status": "success", "message": "Prompt updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating character prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/character/{character_id}/generate-image")
async def generate_character_image(character_id: int, db: Database = Depends(get_db)):
    """
    Generate character portrait image using Jimeng text-to-image,
    download and save to local storage.
    """
    try:
        # Get character data
        query = """
            SELECT cp.character_name, cp.image_prompt, s.drama_name, s.episode_number
            FROM character_portraits cp
            JOIN scripts s ON cp.script_id = s.id
            WHERE cp.id = %s
        """
        results = db.fetch_query(query, (character_id,))

        if not results:
            raise HTTPException(status_code=404, detail="Character not found")

        character = results[0]
        character_name = character["character_name"]
        image_prompt = character["image_prompt"]
        drama_name = character["drama_name"]
        episode_number = character["episode_number"]

        if not image_prompt:
            raise HTTPException(status_code=400, detail="Character has no image prompt")

        # Generate image using Jimeng
        logger.info(f"Generating image for character {character_id} ({character_name})")
        logger.info(f"  Prompt: {image_prompt[:100]}...")

        jimeng = JimengT2IRH()

        # Step 1: Generate image and get URL
        result = jimeng.generate_image(prompt=image_prompt, use_concurrency_control=True)

        if not result or result.get('code') != 0:
            logger.error(f"Failed to generate image: {result}")
            raise HTTPException(status_code=500, detail="Image generation failed")

        # Extract image URL from result
        images = result.get('data', {}).get('images', [])
        if not images:
            raise HTTPException(status_code=500, detail="No images returned from generation")

        image_url = images[0].get('imageUrl')
        if not image_url:
            raise HTTPException(status_code=500, detail="Empty image URL")

        # Step 2: Download image to local storage
        output_dir = Path(f"images/{drama_name}/{episode_number}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{character_name}.jpg")

        logger.info(f"Downloading image to {output_path}...")
        saved_path = jimeng._download_image(image_url, output_path)

        if not saved_path:
            logger.warning("Failed to download image, but URL is available")
            # Continue anyway since we have the URL

        # Update database with new image URL
        conn = db._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE character_portraits SET image_url = %s WHERE id = %s",
                    (image_url, character_id)
                )
                conn.commit()
        finally:
            conn.close()

        logger.info(f"✅ Successfully generated image for character {character_id}")
        if saved_path:
            logger.info(f"  📁 Local: {saved_path}")
        logger.info(f"  🌐 URL: {image_url}")

        return {
            "status": "success",
            "message": "Image generated and saved successfully",
            "image_url": image_url,
            "local_path": saved_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating character image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Register the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=5,
        timeout_graceful_shutdown=10
    )