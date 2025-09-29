import os
import argparse
import sys
import threading
import ast

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import Database
from utils.config import DB_CONFIG
# Remove LLM imports as we will no longer generate prompts on the fly
# from models.yizhan_llm import YiZhanLLM, extract_content_from_stream

def get_model_creator(model_name: str):
    """Dynamically imports and returns the creator function for the specified model."""
    if model_name == "jimeng":
        from models.jimeng_t2i_RH import create_jimeng_t2i_rh
        return create_jimeng_t2i_rh
    elif model_name == "qwen":
        from models.qwen_image_t2i_RH import create_qwen_t2i_rh
        return create_qwen_t2i_rh
    else:
        raise ValueError(f"Unknown model: {model_name}. Please choose 'jimeng' or 'qwen'.")

def generate_single_scene_image(scene_info: dict, output_dir: str, image_generator):
    """
    Generates a single scene image using a pre-generated prompt from the database.
    """
    scene_name = scene_info['scene_name']
    detailed_prompt = scene_info['image_prompt']
    
    # Scene number can be derived from the scene_name if needed, or passed along.
    # For simplicity, we'll use scene_name for identification.
    
    try:
        print(f"🎨 Using pre-generated prompt for Scene '{scene_name}': {detailed_prompt}")

        # Generate the image using the detailed prompt
        # We need a unique identifier for the file. Let's create one from the scene name.
        safe_scene_name = "".join(x for x in scene_name if x.isalnum())
        output_path = os.path.join(output_dir, f"scene_{safe_scene_name}.jpg")

        if os.path.exists(output_path):
            print(f"Image for Scene '{scene_name}' already exists. Skipping.")
            return

        on_start = lambda: print(f"🚀 Starting image generation task for Scene '{scene_name}'...")
        
        saved_path = image_generator.text_to_image(
            prompt=detailed_prompt,
            output_path=output_path,
            on_start_callback=on_start
        )

        if saved_path:
            print(f"✅ Successfully saved image for Scene '{scene_name}' at {saved_path}")
        else:
            print(f"❌ Failed to generate image for Scene '{scene_name}'.")
            
    except Exception as e:
        print(f"An error occurred while generating image for Scene '{scene_name}': {e}")

def generate_scenes_concurrently(drama_name: str, episode_number: int, model_name: str):
    """
    Generates scene images concurrently for a given drama and episode using prompts from the database.
    """
    print(f"Starting scene generation for {drama_name}, Episode {episode_number} using {model_name} model...")

    db = Database(DB_CONFIG)
    
    try:
        model_creator = get_model_creator(model_name)
        image_generator = model_creator()
    except ValueError as e:
        print(e)
        return

    # 1. Fetch scenes and their pre-generated prompts from the database
    scene_query = """
    SELECT scene_name, image_prompt
    FROM scene_definitions
    WHERE drama_name = %s AND episode_number = %s AND image_prompt IS NOT NULL;
    """
    scene_params = (drama_name, episode_number)
    scenes_to_create = db.fetch_query(scene_query, scene_params)

    if not scenes_to_create:
        print("No scenes with generated prompts found for the specified drama and episode.")
        print("Please run generate_scene_definitions.py first.")
        return

    print(f"Found {len(scenes_to_create)} scenes with prompts to generate.")

    output_dir = os.path.join("images", drama_name, str(episode_number), "scenes")
    os.makedirs(output_dir, exist_ok=True)

    threads = []
    for scene in scenes_to_create:
        thread = threading.Thread(target=generate_single_scene_image, args=(scene, output_dir, image_generator))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    
    print("Scene generation process finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate scene images from pre-generated prompts stored in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("-m", "--model", type=str, default="jimeng", choices=["jimeng", "qwen"],
                        help="The model to use for image generation (default: jimeng).")
    
    args = parser.parse_args()
    
    generate_scenes_concurrently(args.drama_name, args.episode_number, args.model)
