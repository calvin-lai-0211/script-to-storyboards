import time
import argparse
import json
import re
import concurrent.futures
from utils.database import Database
from utils.config import DB_CONFIG, MAX_CONCURRENT_THREADS
from models.yizhan_llm import YiZhanLLM

class SceneDefinitionGenerator:
    def __init__(self, db_connection: Database):
        self.db = db_connection
        self.llm = YiZhanLLM()

    def generate(self, drama_name: str, episode_number: int, force_regen: bool = False):
        """
        Generates scene definition prompts for all scenes in a specific episode.
        """
        table_name = "scene_definitions"
        if not force_regen and self.db.check_records_exist(table_name, drama_name, episode_number):
            print(f"Scene definitions for '{drama_name}' Episode {episode_number} already exist. Skipping.")
            return

        if force_regen:
            print(f"Force regeneration enabled. Clearing existing scene definitions for '{drama_name}' Episode {episode_number}...")
            self.db.clear_records(table_name, drama_name, episode_number)

        print(f"--- Starting scene definition generation for '{drama_name}' Episode {episode_number} ---")
        
        # 1. Get all unique scene names for the episode
        scenes = self.db.get_scenes_for_episode(drama_name, episode_number)
        if not scenes:
            print("No scenes found for this episode. Aborting.")
            return

        # 2. Fetch previous scene definitions if not the first episode
        previous_scene_briefs = {}
        if episode_number > 1:
            print(f"Fetching scene definitions from previous episodes...")
            previous_episode_numbers = list(range(1, episode_number))
            previous_scene_defs = self.db.get_scene_definitions(drama_name, previous_episode_numbers)
            previous_scene_briefs = {
                item['scene_name']: item.get('scene_brief', '')
                for item in previous_scene_defs if item.get('scene_brief')
            }
            print(f"Found previous briefs for: {list(previous_scene_briefs.keys())}")

        # 3. Get the script content for the episode
        all_episodes_content = self.db.get_episodes_by_base_title(drama_name)
        if not all_episodes_content or episode_number > len(all_episodes_content):
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return
        script_content = all_episodes_content[episode_number - 1]

        # 4. Concurrently generate prompts for each scene
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_THREADS) as executor:
            futures = {
                executor.submit(
                    self._generate_for_single_scene,
                    drama_name,
                    episode_number,
                    script_content,
                    scene_name,
                    previous_scene_briefs.get(scene_name) # Pass previous brief if exists
                ): scene_name for scene_name in scenes
            }
            
            for future in concurrent.futures.as_completed(futures):
                scene_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"An error occurred while processing scene '{scene_name}': {e}")

        print(f"\n--- Scene definition generation completed for '{drama_name}' Episode {episode_number} ---")

    def _generate_for_single_scene(self, drama_name: str, episode_number: int, script_content: str, scene_name: str, previous_brief: str = None):
        """
        Generates and stores the image prompt for a single scene.
        This method is designed to be called concurrently.
        """
        print(f"\n--- Processing scene: {scene_name} ---")
        
        # 4. Get all shots where the scene appears
        shots_appeared = self.db.get_shots_for_scene_in_episode(drama_name, episode_number, scene_name)
        print(f"Scene '{scene_name}' appears in shots: {shots_appeared}")

        # 5. Build the prompt for the LLM
        prompt = ""
        if previous_brief:
            print(f"Found previous brief for '{scene_name}'. Using memory-enhanced prompt.")
            prompt = self._build_prompt_with_memory(script_content, scene_name, previous_brief)
        else:
            prompt = self._build_prompt(script_content, scene_name)

        # 6. Call LLM to generate the image prompt
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating image prompt for '{scene_name}' (Attempt {attempt + 1})...")
                response_tuple = self.llm.chat(
                    user_message=prompt,
                    model="gemini-2.5-pro",
                    stream=False
                )
                response_str = response_tuple[0] # Get the content part of the response

                # Extract JSON from the response
                json_match = re.search(r"\{[\s\S]*\}", response_str)
                if not json_match:
                    raise ValueError("No valid JSON object found in the LLM response.")
                
                json_string = json_match.group(0)
                response_json = json.loads(json_string)
                image_prompt = response_json.get("prompt")
                reflection = response_json.get("reflection")
                is_key_scene = response_json.get("is_key_scene")
                scene_brief = response_json.get("scene_brief")

                if not image_prompt:
                    raise ValueError("JSON response does not contain a 'prompt' field.")

                print(f"Successfully generated and extracted image prompt for '{scene_name}'.")
                
                # 7. Insert the result into the database
                self.db.insert_scene_definition(
                    drama_name=drama_name,
                    episode_number=episode_number,
                    scene_name=scene_name,
                    image_prompt=image_prompt,
                    shots_appeared=shots_appeared,
                    reflection=reflection,
                    version='0.1',
                    is_key_scene=is_key_scene,
                    scene_brief=scene_brief
                )
                return # Success, exit function
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{scene_name}': {e}")
                if attempt + 1 < max_retries:
                    time.sleep(5)
                else:
                    print(f"All retries failed for '{scene_name}'. Skipping.")
                    raise

    def _build_prompt_with_memory(self, script_content: str, scene_name: str, previous_brief: str) -> str:
        return f"""
# CONTEXT
You are a visionary film director and production designer. Your task is to **update** a scene's definition and image prompt based on the events of a new episode.

# SCENE'S PREVIOUS BRIEF
This is the existing summary of the scene "{scene_name}" based on previous episodes:
---
{previous_brief}
---

# SCRIPT CONTENT FOR THE NEW EPISODE
Here is the script content for the new episode where this scene might be mentioned or featured:
---
{script_content}
---

# TASK
Your goal is to **update and enrich** the scene's definition. Based on the new script content, you will create an updated `scene_brief` and a corresponding image `prompt`. The final output must be a single JSON object.

# INSTRUCTIONS
1.  **Analyze New Events**: Read the new script. Do any events in this episode change the atmosphere, appearance, or significance of the scene "{scene_name}"? For example, has a clean room become messy, has a calm place become a site of conflict, or has its emotional tone shifted?
2.  **Update Scene Brief**: **Rewrite** the `scene_brief`. It must be a new, single sentence that integrates the old brief with any new context from this episode. This should be a cumulative summary of the scene's role and feeling.
3.  **Determine if Key Scene**: This status is unlikely to change, but confirm if it's still a critical, recurring location.
4.  **Visual Consistency and Evolution**: The updated prompt should reflect the scene's **new state**, if it has changed. However, adhere to the core theme of "Noble Poverty" and its architectural basis. The change should feel like an evolution, not a replacement. For example, if a fight occurred, the prompt might now describe "a faint scratch on the otherwise pristine mahogany table."
5.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object with keys: "reflection", "prompt", "is_key_scene", and "scene_brief".
6.  **'reflection' Field**: Explain how the new episode's events informed your updated description. Example: "The tense argument in this scene leaves a lingering feeling of conflict. I've updated the brief to reflect this and added 'a tense, heavy atmosphere' to the prompt."
7.  **'prompt' Field**: Write the new, updated, detailed image generation prompt. It must still be a cinematic shot focused on the environment and atmosphere.
8.  **'is_key_scene' Field**: A boolean (`true` or `false`).
9.  **'scene_brief' Field**: The new, updated, cumulative one-sentence summary.
10. **No People**: The generated keyframe image should still not contain any people.

# EXAMPLE (for updating a scene)
```json
{{
  "reflection": "This study was previously a place of quiet dignity. After the protagonist's desperate search for a hidden document in this episode, the room, while still fundamentally tidy, now has a subtle undercurrent of disquiet. The prompt is updated to reflect this by mentioning a few slightly displaced books and a more dramatic lighting scheme, hinting at the recent turmoil.",
  "prompt": "cinematic wide shot of a dimly lit, old study... sunlight streams through a large window, casting long, dramatic shadows. Most books are orderly, but a small stack on the central desk is slightly askew... conveying a sense of recent, frantic searching within the quiet dignity. Photorealistic, 8K...",
  "is_key_scene": true,
  "scene_brief": "A quiet, dignified study, now holding a subtle tension after a desperate search for secrets within its walls."
}}
```

Now, generate the updated JSON for the scene "{scene_name}".
"""

    def _build_prompt(self, script_content: str, scene_name: str) -> str:
        """
        Builds the prompt to generate a scene's image prompt.
        """
        return f"""
# CONTEXT
You are a visionary film director and production designer. Your task is to create a detailed image generation prompt for a specific scene based on the script. The goal is to generate a definitive, high-quality keyframe that captures the scene's atmosphere, lighting, and core emotion.

# SCRIPT CONTENT
Here is the script content for the episode:
---
{script_content}
---

# TASK
Based on the provided script, create a single, detailed, and vivid image generation prompt for the scene "{scene_name}". The final output must be a JSON object.

# INSTRUCTIONS
1.  **Deep Scene Analysis**: Read the script to understand the scene's location, mood, time of day, and emotional tone.
2.  **Determine if Key Scene**: A scene is considered "key" if it meets **all** the following criteria:
    a. It is a critical location where major plot events unfold.
    b. It is a location frequently visited by key characters.
    c. Based on the narrative, it is clear this location will reappear in future episodes.
3.  **Scene Brief**: Write a concise one-sentence summary of the scene's purpose and atmosphere.
4.  **CRITICAL THEME - Noble Poverty**: Analyze the scene's history versus its current state. For example, a living room in the home of an impoverished noble family should show signs of past grandeur. The setting can be old or worn, but the taste, quality of the items (even if aged), and overall cleanliness must convey a sense of elegance and dignity. The space should feel curated and respected, not neglected.
5.  **Visual Consistency**: The generated image should represent the scene's fundamental state, not a temporary condition. **Critically, you must ignore transient details** resulting from specific actions, such as battle damage, bloodstains, temporary messes, or scattered objects, unless the script specifies these as a permanent feature of the scene. Focus on the enduring atmosphere and architecture.
6.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object with no external text. It must contain four keys: "reflection", "prompt", "is_key_scene", and "scene_brief".
7.  **'reflection' Field**: Write down your analysis here. Explain your conclusions about the scene's atmosphere, lighting, key objects, and how you will visually represent the theme of "noble poverty." For example: "The furniture is antique and of high quality, but shows signs of age like faded upholstery. The room is spotless, indicating the owner's pride."
8.  **'prompt' Field**: Write the final, detailed image generation prompt here (for the Jimeng 4.0 model, in English). This prompt should be a direct result of your reflection and ready for an AI image generator.
9.  **'is_key_scene' Field**: A boolean value (`true` or `false`).
10. **'scene_brief' Field**: A string containing the one-sentence summary.
11. **Prompt Content**: The prompt should aim for a photorealistic, cinematic style. Detail the composition, lighting, color palette, and key elements of the environment.
12. **No People, Pure Scene**: Unless specifically instructed by the script, the scene should not contain any people. Focus on the environment, architecture, objects, and atmosphere.

# EXAMPLE (for a different scene)
```json
{{
  "reflection": "This is the study of a retired professor from a once-wealthy family. The room is filled with old books and antique furniture. Though the rug is worn and the wallpaper is peeling slightly, the room is exceptionally clean and organized. The lingering quality of the items and the tidiness show the owner's intellectual and dignified nature despite their financial decline.",
  "prompt": "cinematic wide shot of a dimly lit, old study filled with books. Sunlight streams through a large, aged window, illuminating dust motes in the air. Antique, high-quality wooden bookshelves line the walls, filled with leather-bound volumes. A worn but elegant Persian rug covers the floor. The room is impeccably clean and orderly, conveying a sense of quiet dignity. Photorealistic, 8K, rich textures, melancholic but dignified atmosphere.",
  "is_key_scene": true,
  "scene_brief": "A quiet, dignified study reflecting the owner's scholarly past and current state of noble poverty."
}}
```

Now, generate the JSON for the scene "{scene_name}".
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate scene definitions and store them in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("--force-regen", action="store_true", help="Force regeneration of scene definitions even if they already exist.")
    args = parser.parse_args()

    # In a real scenario, you'd initialize the Database here or pass it to the generator
    db_connection = Database(DB_CONFIG)
    generator = SceneDefinitionGenerator(db_connection)
    generator.generate(args.drama_name, args.episode_number, args.force_regen)
