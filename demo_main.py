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
from procedure.generate_memory_for_episodes import EpisodeMemoryGenerator
from procedure.generate_character_images import make_portraits_concurrently
from procedure.generate_scene_images import generate_scenes_concurrently
from procedure.generate_key_prop_images import generate_props_concurrently

def generate_storyboards(drama_name: str, force_regen: bool = False, episode_number: int = None):
    """
    Generates storyboards. If an episode_number is provided, it only generates for that episode.
    Otherwise, it generates for all episodes sequentially.
    """
    db = Database(DB_CONFIG)
    storyboard_generator = MakeStoryboardsText(db)

    if episode_number:
        episodes_to_process = [episode_number]
        print(f"\n🎬 STANDALONE: GENERATING STORYBOARD for '{drama_name}' Episode {episode_number}...")
    else:
        episodes_to_process = db.get_episode_numbers_for_drama(drama_name)
        print(f"\n🎬 STANDALONE: GENERATING STORYBOARDS for all episodes of '{drama_name}'...")

    for ep_num in episodes_to_process:
        storyboard_generator.generate(base_script_title=drama_name, episode_number=ep_num, force_regen=force_regen)
    
    print("✅ Storyboard generation complete.")

def run_full_pipeline(drama_name: str, episode_target: int = None, model_name: str = "jimeng", force_regen: bool = False):
    """
    Executes the entire script-to-storyboard pipeline.
    """
    db = Database(DB_CONFIG)
    storyboard_generator = MakeStoryboardsText(db)

    # --- Pre-flight check for script existence ---
    print(f"🔍 Verifying existence of script: '{drama_name}'...")
    if not db.check_script_exists_by_base_title(drama_name):
        print(f"❌ No scripts found for base title '{drama_name}'. Please check the drama name and ensure scripts are in the database.")
        print("Aborting pipeline.")
        return
    print("✅ Script verified.")

    # --- Determine which episodes to process for image generation ---
    if episode_target:
        # If a specific episode is targeted, we process only that one.
        episodes_to_process = [episode_target]
        print(f"\n🎯 Targeting Episode {episode_target} for processing.")
    else:
        print("\nNo specific episode targeted. Processing all available episodes...")
        episodes_to_process = db.get_episode_numbers_for_drama(drama_name)
        if not episodes_to_process:
            print(f"❌ No episodes found for drama '{drama_name}' in the database to process. Aborting.")
            return
        print(f"Found episodes to process: {episodes_to_process}")

    # --- Loop through each episode and process ---
    for episode_num in episodes_to_process:
        print("\n" + "#"*80)
        print(f" PROCESSING EPISODE {episode_num} ".center(80, '#'))
        print("#"*80)

        # --- Step 1: Generate Storyboard from Script ---
        print("\n" + "="*50)
        print(f"📝 STEP 1: GENERATING STORYBOARD FOR EPISODE {episode_num}...")
        print("="*50)
        storyboard_generator.generate(base_script_title=drama_name, episode_number=episode_num, force_regen=force_regen)
        print(f"✅ Storyboard for Episode {episode_num} complete.")

        # --- Step 2: Generate Prompts for all assets ---
        print("\n" + "="*50)
        print(f"📝 STEP 2: GENERATING PROMPTS FOR EPISODE {episode_num}...")
        print("="*50)
        
        # Characters
        char_prompt_generator = CharacterPortraitGenerator(db)
        char_prompt_generator.generate(drama_name=drama_name, episode_number=episode_num, force_regen=force_regen)
        
        # Scenes
        scene_prompt_generator = SceneDefinitionGenerator(db)
        scene_prompt_generator.generate(drama_name=drama_name, episode_number=episode_num, force_regen=force_regen)

        # Key Props
        prop_prompt_generator = KeyPropDefinitionGenerator(db)
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

        # --- Step 4: Generate Episode Memory ---
        print("\n" + "="*50)
        print(f"🧠 STEP 4: GENERATING EPISODE MEMORY FOR EPISODE {episode_num}...")
        print("="*50)

        memory_generator = EpisodeMemoryGenerator(db)
        memory_generator.generate(drama_name=drama_name, episode_number=episode_num, force_regen=force_regen)

        print(f"✅ Episode memory generation for Episode {episode_num} complete.")

    print("\n" + "*"*80)
    print("🎉 FULL PIPELINE COMPLETED SUCCESSFULLY! 🎉".center(80, ' '))
    print("*"*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the full Script-to-Storyboards pipeline or only generate storyboards.",
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
        help="Optional: The specific episode number to process for images and memory.\nIf not provided, all episodes with existing storyboards will be processed."
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

    parser.add_argument(
        "--storyboard-only",
        action="store_true",
        help="If set, only runs the storyboard text generation step."
    )

    args = parser.parse_args()

    if args.storyboard_only:
        generate_storyboards(args.drama_name, args.force_regen, args.episode_number)
    else:
        run_full_pipeline(args.drama_name, args.episode_number, args.model, args.force_regen)
