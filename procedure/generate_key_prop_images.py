import os
import argparse
import sys
import threading
from typing import Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import Database
from utils.config import DB_CONFIG
from models.jimeng_t2i_RH import create_jimeng_t2i_rh
from models.qwen_image_t2i_RH import create_qwen_t2i_rh

# --- Concurrency Configuration ---
MAX_CONCURRENT_TASKS = 3  # Set the maximum number of concurrent image generation tasks
# ---------------------------------

def get_model_creator(model_name: str):
    """Dynamically imports and returns the creator function for the specified model."""
    if model_name == "jimeng":
        return create_jimeng_t2i_rh
    elif model_name == "qwen":
        return create_qwen_t2i_rh
    else:
        raise ValueError(f"Unknown model: {model_name}. Please choose 'jimeng' or 'qwen'.")

def generate_single_prop_image(prop_info: Dict[str, Any], output_dir: str, image_generator: Any, semaphore: threading.Semaphore):
    """
    Generates a single key prop image using a pre-generated prompt from the database.
    This function is designed to be run in a separate thread.
    """
    with semaphore:
        prop_name = prop_info['prop_name']
        detailed_prompt = prop_info['image_prompt']
        
        try:
            print(f"🎨 Using pre-generated prompt for Prop '{prop_name}': {detailed_prompt}")

            # Sanitize the prop name to create a valid filename
            safe_prop_name = "".join(x for x in prop_name if x.isalnum() or x in "._-").strip()
            if not safe_prop_name:
                safe_prop_name = f"prop_{hash(prop_name)}"

            output_path = os.path.join(output_dir, f"{safe_prop_name}.jpg")

            if os.path.exists(output_path):
                print(f"Image for Prop '{prop_name}' already exists. Skipping.")
                return

            on_start = lambda: print(f"🚀 Starting image generation task for Prop '{prop_name}'...")
            
            saved_path = image_generator.text_to_image(
                prompt=detailed_prompt,
                output_path=output_path,
                on_start_callback=on_start
            )

            if saved_path:
                print(f"✅ Successfully saved image for Prop '{prop_name}' at {saved_path}")
            else:
                print(f"❌ Failed to generate image for Prop '{prop_name}'.")
                
        except Exception as e:
            print(f"An error occurred while generating image for Prop '{prop_name}': {e}")

def generate_props_concurrently(drama_name: str, episode_number: int, model_name: str):
    """
    Generates key prop images concurrently for a given drama and episode using prompts from the database.
    """
    print(f"Starting key prop image generation for {drama_name}, Episode {episode_number} using {model_name} model...")

    db = Database(DB_CONFIG)
    
    try:
        model_creator = get_model_creator(model_name)
        image_generator = model_creator()
    except ValueError as e:
        print(e)
        return

    # 1. Fetch props and their pre-generated prompts from the database
    prop_query = """
    SELECT prop_name, image_prompt
    FROM key_prop_definitions
    WHERE drama_name = %s AND episode_number = %s AND image_prompt IS NOT NULL;
    """
    prop_params = (drama_name, episode_number)
    props_to_create = db.fetch_query(prop_query, prop_params)

    if not props_to_create:
        print("No key props with generated prompts found for the specified drama and episode.")
        print("Please run generate_key_prop_definitions.py first.")
        return

    print(f"Found {len(props_to_create)} key props with prompts to generate.")
    print(f"Concurrency limit set to {MAX_CONCURRENT_TASKS} tasks.")

    output_dir = os.path.join("images", drama_name, str(episode_number), "props")
    os.makedirs(output_dir, exist_ok=True)

    semaphore = threading.Semaphore(MAX_CONCURRENT_TASKS)
    threads = []
    for prop in props_to_create:
        thread = threading.Thread(target=generate_single_prop_image, args=(prop, output_dir, image_generator, semaphore))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    
    print("Key prop image generation process finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate key prop images from pre-generated prompts stored in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("-m", "--model", type=str, default="jimeng", choices=["jimeng", "qwen"],
                        help="The model to use for image generation (default: jimeng).")
    
    args = parser.parse_args()
    
    generate_props_concurrently(args.drama_name, args.episode_number, args.model)
