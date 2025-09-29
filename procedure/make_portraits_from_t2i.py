import os
import argparse
import sys
import threading
import ast

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import Database
from utils.config import DB_CONFIG

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

def generate_single_portrait(character_info: dict, output_dir: str, image_generator):
    """
    Generates a single character portrait and saves it.
    This function is designed to be run in a separate thread.
    """
    character_name = character_info['character_name']
    image_prompt_raw = character_info['image_prompt']

    try:
        if not image_prompt_raw:
            print(f"Skipping '{character_name}' due to missing image prompt.")
            return

        image_prompt = image_prompt_raw
        try:
            prompt_data = ast.literal_eval(image_prompt_raw)
            if isinstance(prompt_data, (list, tuple)) and len(prompt_data) > 0 and isinstance(prompt_data[0], str):
                image_prompt = prompt_data[0]
                print(f"Extracted prompt for '{character_name}'.")
        except (ValueError, SyntaxError):
            pass # Keep raw value if not a tuple/list

        if not image_prompt:
            print(f"Skipping '{character_name}' as extracted prompt is empty.")
            return

        output_path = os.path.join(output_dir, f"{character_name}.jpg")

        if os.path.exists(output_path):
            print(f"Portrait for '{character_name}' already exists. Skipping.")
            return

        # The log "Starting task..." is now triggered by a callback
        # inside the image generator, ensuring it runs after the
        # concurrency lock is acquired.
        on_start = lambda: print(f"🚀 Starting image generation task for '{character_name}'...")
        
        saved_path = image_generator.text_to_image(
            prompt=image_prompt,
            output_path=output_path,
            # width=720, # Removed to allow model defaults
            # height=1280, # Removed to allow model defaults
            on_start_callback=on_start
        )

        if saved_path:
            print(f"Successfully saved portrait for '{character_name}' at {saved_path}")
        else:
            print(f"Failed to generate portrait for '{character_name}'.")
            
    except Exception as e:
        print(f"An error occurred while generating portrait for '{character_name}': {e}")


def make_portraits_concurrently(drama_name: str, episode_number: int, model_name: str):
    """
    Generates character portraits concurrently for a given drama and episode,
    respecting the concurrency limits defined in the image generator.
    """
    print(f"Starting portrait generation for {drama_name}, Episode {episode_number} using {model_name} model...")

    db = Database(DB_CONFIG)
    
    try:
        model_creator = get_model_creator(model_name)
        image_generator = model_creator()
    except ValueError as e:
        print(e)
        return

    query = """
    SELECT character_name, image_prompt 
    FROM public.character_portraits 
    WHERE drama_name = %s AND episode_number = %s;
    """
    params = (drama_name, episode_number)
    characters_to_create = db.fetch_query(query, params)

    if not characters_to_create:
        print("No characters found for the specified drama and episode.")
        return

    print(f"Found {len(characters_to_create)} characters to generate.")

    output_dir = os.path.join("images", drama_name, str(episode_number))
    os.makedirs(output_dir, exist_ok=True)

    threads = []
    for character in characters_to_create:
        # Each thread will call generate_single_portrait.
        # The concurrency manager inside image_generator will block threads
        # if the number of active tasks reaches the limit (3).
        thread = threading.Thread(target=generate_single_portrait, args=(character, output_dir, image_generator))
        threads.append(thread)
        thread.start()
        print(f"Thread for '{character['character_name']}' started.")

    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("Portrait generation process finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate character portraits from text-to-image based on drama and episode.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("-m", "--model", type=str, default="jimeng", choices=["jimeng", "qwen"],
                        help="The model to use for image generation (default: jimeng).")
    
    args = parser.parse_args()
    
    make_portraits_concurrently(args.drama_name, args.episode_number, args.model)
