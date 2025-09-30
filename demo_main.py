import argparse
import sys
import os

# Ensure the project root is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import Database
from utils.config import DB_CONFIG

from procedure.make_storyboards import MakeStoryboardsText
from procedure.generate_character_portraits import CharacterPortraitGenerator
from procedure.generate_scene_definitions import SceneDefinitionGenerator
from procedure.generate_key_prop_definitions import KeyPropDefinitionGenerator
from procedure.generate_character_images import make_portraits_concurrently
from procedure.generate_scene_images import generate_scenes_concurrently
from procedure.generate_key_prop_images import generate_props_concurrently

def run_full_pipeline(drama_name: str, episode_target: int = None, model_name: str = "jimeng", force_regen: bool = False):
    """
    Executes the entire script-to-storyboard pipeline.
    """
    db = Database(DB_CONFIG)

    # --- Step 1: Generate Storyboards from Script ---
    # This step is foundational and processes the entire script to populate the flat_storyboards table.
    print("\n" + "="*50)
    print("🎬 STEP 1: GENERATING STORYBOARDS...")
    print("="*50)
    storyboard_generator = MakeStoryboardsText()
    storyboard_generator.generate(base_script_title=drama_name, force_regen=force_regen)
    print("✅ Storyboard generation complete.")

    # --- Determine which episodes to process ---
    if episode_target:
        episodes_to_process = [episode_target]
        print(f"\nTargeting Episode: {episode_target}")
    else:
        print("\nNo specific episode provided. Processing all available episodes...")
        episodes_to_process = db.get_episode_numbers_for_drama(drama_name)
        if not episodes_to_process:
            print(f"❌ No episodes found for drama '{drama_name}' in the database. Aborting.")
            return
        print(f"Found episodes to process: {episodes_to_process}")

    # --- Loop through each episode and process ---
    for episode_num in episodes_to_process:
        print("\n" + "#"*80)
        print(f" PROCESSING EPISODE {episode_num} ".center(80, '#'))
        print("#"*80)

        # --- Step 2: Generate Prompts for all assets ---
        print("\n" + "="*50)
        print(f"📝 STEP 2: GENERATING PROMPTS FOR EPISODE {episode_num}...")
        print("="*50)
        
        # Characters
        char_prompt_generator = CharacterPortraitGenerator()
        char_prompt_generator.generate(drama_name=drama_name, episode_number=episode_num, force_regen=force_regen)
        
        # Scenes
        scene_prompt_generator = SceneDefinitionGenerator()
        scene_prompt_generator.generate(drama_name=drama_name, episode_number=episode_num, force_regen=force_regen)

        # Key Props
        prop_prompt_generator = KeyPropDefinitionGenerator()
        prop_prompt_generator.generate(drama_name=drama_name, episode_number=episode_num, force_regen=force_regen)
        
        print(f"✅ Prompt generation for Episode {episode_num} complete.")

        # --- Step 3: Generate Images from Prompts ---
        print("\n" + "="*50)
        print(f"🖼️  STEP 3: GENERATING IMAGES FOR EPISODE {episode_num} using '{model_name}' model...")
        print("="*50)

        # Character Portraits
        make_portraits_concurrently(drama_name, episode_num, model_name)

        # Scene Images
        generate_scenes_concurrently(drama_name, episode_num, model_name)
        
        # Key Prop Images
        generate_props_concurrently(drama_name, episode_num, model_name)

        print(f"✅ Image generation for Episode {episode_num} complete.")

    print("\n" + "*"*80)
    print("🎉 FULL PIPELINE COMPLETED SUCCESSFULLY! 🎉".center(80, ' '))
    print("*"*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the full Script-to-Storyboards pipeline.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "drama_name", 
        type=str, 
        nargs='?', 
        default="天归（「西语版」）",
        help="The name of the drama to process (must match the title in the 'scripts' table).\n(default: \"天归（「西语版」）\")"
    )
    
    parser.add_argument(
        "episode_number", 
        type=int, 
        nargs='?', 
        default=None,
        help="Optional: The specific episode number to process.\nIf not provided, all episodes for the drama will be processed."
    )

    parser.add_argument(
        "-m", "--model", 
        type=str, 
        default="jimeng", 
        choices=["jimeng", "qwen"],
        help="The model to use for image generation.\n(default: jimeng)"
    )

    parser.add_argument(
        "-f", "--force-regen",
        action="store_true",
        help="If set, forces regeneration of data by deleting existing records before processing."
    )

    args = parser.parse_args()

    run_full_pipeline(args.drama_name, args.episode_number, args.model, args.force_regen)
