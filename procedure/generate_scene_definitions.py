import time
import argparse
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class SceneDefinitionGenerator:
    def __init__(self):
        self.db = Database(DB_CONFIG)
        self.llm = YiZhanLLM()

    def generate(self, drama_name: str, episode_number: int):
        """
        Generates scene definition prompts for all scenes in a specific episode.
        """
        print(f"--- Starting scene definition generation for '{drama_name}' Episode {episode_number} ---")
        
        # 1. Get all unique scene names for the episode
        scenes = self.db.get_scenes_for_episode(drama_name, episode_number)
        if not scenes:
            print("No scenes found for this episode. Aborting.")
            return

        # 2. Get the script content for the episode
        all_episodes_content = self.db.get_episodes_by_base_title(drama_name)
        if not all_episodes_content or episode_number > len(all_episodes_content):
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return
        script_content = all_episodes_content[episode_number - 1]

        # 3. Loop through each scene to generate and store its definition prompt
        for scene_name in scenes:
            print(f"\n--- Processing scene: {scene_name} ---")
            
            # 4. Get all shots where the scene appears
            shots_appeared = self.db.get_shots_for_scene_in_episode(drama_name, episode_number, scene_name)
            print(f"Scene '{scene_name}' appears in shots: {shots_appeared}")

            # 5. Build the prompt for the LLM
            prompt = self._build_prompt(script_content, scene_name)

            # 6. Call LLM to generate the image prompt
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Generating image prompt for '{scene_name}' (Attempt {attempt + 1})...")
                    image_prompt = self.llm.chat(
                        user_message=prompt,
                        model="gemini-2.5-pro",
                        stream=False
                    )
                    print(f"Successfully generated image prompt for '{scene_name}'.")
                    
                    # 7. Insert the result into the database
                    self.db.insert_scene_definition(
                        drama_name=drama_name,
                        episode_number=episode_number,
                        scene_name=scene_name,
                        image_prompt=image_prompt,
                        shots_appeared=shots_appeared
                    )
                    break # Success, exit retry loop
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for '{scene_name}': {e}")
                    if attempt + 1 < max_retries:
                        time.sleep(5)
                    else:
                        print(f"All retries failed for '{scene_name}'. Skipping.")

        print(f"\n--- Scene definition generation completed for '{drama_name}' Episode {episode_number} ---")

    def _build_prompt(self, script_content: str, scene_name: str) -> str:
        """
        Builds the prompt to generate a scene's image prompt.
        """
        return f"""
# CONTEXT
You are a visionary film director and production designer. Your task is to create a detailed image generation prompt for a specific scene based on a script. The goal is to create a definitive, high-quality keyframe that captures the atmosphere, lighting, and core emotion of the scene.

# SCRIPT CONTENT
Here is the script content for the episode:
---
{script_content}
---

# TASK
Based on the provided script, create a single, detailed, and vivid image generation prompt for the scene: "{scene_name}".

# INSTRUCTIONS
1.  **Analyze the Scene**: Read the script carefully to understand the scene's location, mood, time of day, key actions, and emotional tone.
2.  **Define Scene Nature**: You MUST clearly identify and specify the exact nature and type of the scene location (e.g., "traditional Chinese pharmacy with wooden medicine cabinets", "modern middle-class family living room", "ancient palace courtyard", "bustling street market", "hospital emergency room"). This is crucial for accurate image generation.
3.  **Be Specific and Vivid**: The prompt must be highly detailed. Mention specific visual elements, lighting (e.g., 'soft morning light filtering through a window', 'harsh neon glow'), color palette, and camera composition (e.g., 'wide shot', 'low-angle shot').
4.  **Output Format**: The output must be a single text block, ready to be used directly in an advanced AI image generator (like Qwen Image or Midjourney). Do not include any extra text, explanations, or labels.
5.  **Artistic Style**: The prompt should aim for a photorealistic, cinematic style. You can reference specific film styles or directors if it helps capture the mood.
6.  **Key Focus**: The image should represent the entire scene, not just a single character. It should establish the environment and atmosphere.
7.  **No People and scene only！！**: The scene must not include any people, characters, or human figures. Focus purely on the environment, architecture, objects, and atmosphere.

# EXAMPLE PROMPT (for a different scene)
"cinematic wide shot of a traditional Chinese herbal medicine shop interior, with rows of dark wooden medicine cabinets lining the walls, filled with labeled drawers containing various herbs. A wooden counter displays brass scales and ceramic jars. Warm amber lighting from hanging lanterns creates a cozy, authentic atmosphere. The color palette features rich browns, deep golds, and muted reds. Empty and devoid of people. Photorealistic, 8K, sharp focus, traditional and atmospheric."

Now, generate the prompt for the scene: "{scene_name}".
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate scene definitions and store them in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    args = parser.parse_args()

    generator = SceneDefinitionGenerator()
    generator.generate(args.drama_name, args.episode_number)
