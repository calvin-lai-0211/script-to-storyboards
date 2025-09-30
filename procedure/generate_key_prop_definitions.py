import time
import argparse
import json
import re
import concurrent.futures
from utils.database import Database
from utils.config import DB_CONFIG, MAX_CONCURRENT_THREADS
from models.yizhan_llm import YiZhanLLM

class KeyPropDefinitionGenerator:
    def __init__(self, db_connection: Database):
        self.db = db_connection
        self.llm = YiZhanLLM()

    def generate(self, drama_name: str, episode_number: int, force_regen: bool = False):
        """
        Generates key prop definition prompts for all props in a specific episode.
        """
        table_name = "key_prop_definitions"
        if not force_regen and self.db.check_records_exist(table_name, drama_name, episode_number):
            print(f"Key prop definitions for '{drama_name}' Episode {episode_number} already exist. Skipping.")
            return

        if force_regen:
            print(f"Force regeneration enabled. Clearing existing key prop definitions for '{drama_name}' Episode {episode_number}...")
            self.db.clear_records(table_name, drama_name, episode_number)
            
        print(f"--- Starting key prop definition generation for '{drama_name}' Episode {episode_number} ---")
        
        # 1. Get all unique key prop names for the episode
        props = self.db.get_key_props_for_episode(drama_name, episode_number)
        if not props:
            print("No key props found for this episode. Aborting.")
            return

        # 2. Fetch previous prop definitions if not the first episode
        previous_prop_briefs = {}
        if episode_number > 1:
            print(f"Fetching key prop definitions from previous episodes...")
            previous_episode_numbers = list(range(1, episode_number))
            previous_prop_defs = self.db.get_key_prop_definitions(drama_name, previous_episode_numbers)
            previous_prop_briefs = {
                item['prop_name']: item.get('prop_brief', '')
                for item in previous_prop_defs if item.get('prop_brief')
            }
            print(f"Found previous briefs for: {list(previous_prop_briefs.keys())}")

        # 3. Get the script content for the episode
        all_episodes_content = self.db.get_episodes_by_base_title(drama_name)
        if not all_episodes_content or episode_number > len(all_episodes_content):
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return
        script_content = all_episodes_content[episode_number - 1]

        # 4. Concurrently generate prompts for each prop
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_THREADS) as executor:
            futures = {
                executor.submit(
                    self._generate_for_single_prop,
                    drama_name,
                    episode_number,
                    script_content,
                    prop_name,
                    previous_prop_briefs.get(prop_name) # Pass previous brief if exists
                ): prop_name for prop_name in props
            }
            
            for future in concurrent.futures.as_completed(futures):
                prop_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"An error occurred while processing prop '{prop_name}': {e}")
        
        print(f"\n--- Key prop definition generation completed for '{drama_name}' Episode {episode_number} ---")

    def _generate_for_single_prop(self, drama_name: str, episode_number: int, script_content: str, prop_name: str, previous_brief: str = None):
        """
        Generates and stores the image prompt for a single key prop.
        This method is designed to be called concurrently.
        """
        print(f"\n--- Processing key prop: {prop_name} ---")
        
        # 4. Get all sub-shot details where the prop appears
        sub_shots_details = self.db.get_sub_shots_for_key_prop(drama_name, episode_number, prop_name)
        if not sub_shots_details:
            print(f"Could not find any shots for prop '{prop_name}'. Skipping.")
            return
        
        shots_appeared = [shot['sub_shot_number'] for shot in sub_shots_details]
        print(f"Key prop '{prop_name}' appears in shots: {shots_appeared}")

        # 5. Build the prompt for the LLM
        prompt = ""
        if previous_brief:
            print(f"Found previous brief for '{prop_name}'. Using memory-enhanced prompt.")
            prompt = self._build_prompt_with_memory(script_content, prop_name, sub_shots_details, previous_brief)
        else:
            prompt = self._build_prompt(script_content, prop_name, sub_shots_details)

        # 6. Call LLM to generate the image prompt
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating image prompt for '{prop_name}' (Attempt {attempt + 1})...")
                response_tuple = self.llm.chat(
                    user_message=prompt,
                    model="gemini-2.5-pro",
                    stream=False
                )
                response_str = response_tuple[0]

                json_match = re.search(r"\{[\s\S]*\}", response_str)
                if not json_match:
                    raise ValueError("No valid JSON object found in the LLM response.")
                
                json_string = json_match.group(0)
                response_json = json.loads(json_string)
                image_prompt = response_json.get("prompt")
                reflection = response_json.get("reflection")
                is_key_prop = response_json.get("is_key_prop")
                prop_brief = response_json.get("prop_brief")

                if not image_prompt:
                    raise ValueError("JSON response does not contain a 'prompt' field.")

                print(f"Successfully generated image prompt for '{prop_name}'.")
                
                # 7. Insert the result into the database
                self.db.insert_key_prop_definition(
                    drama_name=drama_name,
                    episode_number=episode_number,
                    prop_name=prop_name,
                    image_prompt=image_prompt,
                    shots_appeared=shots_appeared,
                    reflection=reflection,
                    version='0.1',
                    is_key_prop=is_key_prop,
                    prop_brief=prop_brief
                )
                return # Success, exit function
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{prop_name}': {e}")
                if attempt + 1 < max_retries:
                    time.sleep(5)
                else:
                    print(f"All retries failed for '{prop_name}'. Skipping.")
                    raise

    def _build_prompt_with_memory(self, script_content: str, prop_name: str, sub_shots_details: list, previous_brief: str) -> str:
        shots_context = "\n".join([
            f"  - Shot {shot['sub_shot_number']}: "
            f"Scene Context: {shot.get('scene_description', 'N/A')}, "
            f"Action/Description: {shot.get('image_prompt', 'N/A')}"
            for shot in sub_shots_details
        ])

        return f"""
# CONTEXT
You are a professional prop master and concept artist. Your task is to **update** a key prop's definition and image prompt based on its usage in a new episode.

# PROP'S PREVIOUS BRIEF
This is the existing summary of the prop "{prop_name}" based on previous episodes:
---
{previous_brief}
---

# SCRIPT CONTENT FOR THE NEW EPISODE
Here is the script content for the new episode:
---
{script_content}
---

# PROP'S NEW APPEARANCES IN THIS EPISODE
Here is a summary of all scenes where "{prop_name}" appears in the **new episode**:
---
{shots_context}
---

# TASK
Your goal is to **update and enrich** the prop's definition. Based on its new appearances, you will create an updated `prop_brief` and a corresponding image `prompt`. The final output must be a single JSON object.

# INSTRUCTIONS
1.  **Analyze New Context**: Read the new script and scene summaries. Does the prop's function, meaning, or physical state change in this episode? For example, is a pristine item now damaged? Does a simple object reveal a hidden feature?
2.  **Update Prop Brief**: **Rewrite** the `prop_brief`. It must be a new, single sentence that integrates the old brief with the new information. This should be a cumulative summary of the prop's identity and significance.
3.  **Determine if Key Prop**: This status is unlikely to change, but confirm if it remains a central, recurring item.
4.  **Visual Consistency**: The updated prompt should reflect the prop's **most current, neutral state**, unless a permanent change has occurred (e.g., it is broken and will remain so). The goal is a consistent visual that can be used for this and future episodes.
5.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object with keys: "reflection", "prompt", "is_key_prop", and "prop_brief".
6.  **'reflection' Field**: Explain how the new scenes informed your updated description. Example: "The locket was previously just a keepsake. In this episode, it's used to hide a key. I've updated the brief to include this new function, and the prompt now mentions a subtle hinge on its side."
7.  **'prompt' Field**: Write the new, updated, detailed image generation prompt. It must still be an isolated studio shot against a neutral background.
8.  **'is_key_prop' Field**: A boolean (`true` or `false`).
9.  **'prop_brief' Field**: The new, updated, cumulative one-sentence summary.

# EXAMPLE (for updating a prop)
```json
{{
  "reflection": "This astrolabe was known to be a family heirloom. The new episode reveals it's also a key to a hidden door. Its function is now more significant. The brief is updated to reflect its dual nature. The prompt remains visually consistent but I will add a note about a specific symbol on its surface that was mentioned in this episode.",
  "prompt": "A photorealistic, high-resolution studio shot of an antique brass astrolabe... It shows signs of wear, with a slight patina in the crevices. A small, unique symbol of a serpent eating its tail is subtly engraved on the outer ring. The lighting is soft and even...",
  "is_key_prop": true,
  "prop_brief": "An ancient, weathered brass astrolabe with celestial engravings, a family heirloom that also serves as the key to a hidden passage."
}}
```

Now, generate the updated JSON for the key prop: "{prop_name}".
"""

    def _build_prompt(self, script_content: str, prop_name: str, sub_shots_details: list) -> str:
        """
        Builds the prompt to generate a key prop's image prompt.
        """
        # Format the sub-shot details for inclusion in the prompt
        shots_context = "\n".join([
            f"  - Shot {shot['sub_shot_number']}: "
            f"Scene Context: {shot.get('scene_description', 'N/A')}, "
            f"Action/Description: {shot.get('image_prompt', 'N/A')}"
            for shot in sub_shots_details
        ])

        return f"""
# CONTEXT
You are a professional prop master and concept artist for a film production. Your task is to create a detailed image generation prompt for a specific key prop. The goal is to generate a definitive, high-quality, and consistent visual representation of the prop that can be used across different scenes.

# SCRIPT CONTENT
For full context, here is the entire script content:
---
{script_content}
---

# PROP'S APPEARANCES
To ensure the prop's design is consistent with its usage in the story, here is a summary of all scenes where the prop "{prop_name}" appears:
---
{shots_context}
---

# TASK
Based on the full script and the prop's specific appearances, create a single, detailed, and vivid image generation prompt for the key prop: "{prop_name}". The final output must be a JSON object.

# INSTRUCTIONS
    1.  **Analyze the Prop**: Carefully read the script and scene summaries to understand the prop's function, material, age, condition (e.g., new, worn, ancient), and its significance to the story and characters.
    2.  **Determine if Key Prop**: A prop is considered "key" if it meets **all** the following criteria:
        a. It is frequently used by key characters and is significant to the plot.
        b. Based on the narrative, it is clear this prop will reappear in future episodes.
    3.  **Prop Brief**: Write a concise one-sentence summary of the prop's appearance and significance.
    4.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object with no external text. It must contain four keys: "reflection", "prompt", "is_key_prop", and "prop_brief".
    5.  **'reflection' Field**: Write down your analysis and reasoning here. Explain your conclusions about the prop's material, design details, history, and function. For example: "This pocket watch is a family heirloom, so while old, it should be well-maintained. The material is brass, with vintage engravings, and minor scratches on the surface."
    6.  **'prompt' Field**: Write the final, detailed image generation prompt here (for the Jimeng 4.0 model, in English). It should be a single, ready-to-use string.
    7.  **'is_key_prop' Field**: A boolean value (`true` or `false`) based on your analysis in step 2.
    8.  **'prop_brief' Field**: A string containing the one-sentence summary.
    9.  **Prompt Content**: The prompt must describe a clean, isolated studio shot of the prop against a neutral background (like white or grey). This is crucial. Aim for a photorealistic, high-resolution style. Mention lighting that clearly showcases the prop's details (e.g., "soft studio lighting").
    10. **Visual Consistency**: The prompt must produce a consistent visual. If the prop is described differently in different scenes (e.g., clean then later dirty), create a prompt for its most neutral or primary state.

# EXAMPLE (for a different prop)
```json
{{
  "reflection": "This is an ancient brass astrolabe, a treasure passed down through the protagonist's family. It should look both intricate and weathered. The inscriptions are a key visual element and need to be clear. The overall feeling is mysterious and precious.",
  "prompt": "A photorealistic, high-resolution studio shot of an antique brass astrolabe against a neutral grey background. The astrolabe is intricately engraved with celestial maps and Latin inscriptions. It shows signs of wear, with a slight patina in the crevices. The lighting is soft and even, highlighting the fine details and metallic texture of the object. 8K, cinematic product shot.",
  "is_key_prop": true,
  "prop_brief": "An ancient, weathered brass astrolabe with intricate celestial engravings, serving as a family heirloom."
}}
```

Now, generate the JSON for the key prop: "{prop_name}".
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate key prop definitions and store them in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("--force-regen", action="store_true", help="Force regeneration of key prop definitions even if they already exist.")
    args = parser.parse_args()

    db = Database(DB_CONFIG)
    generator = KeyPropDefinitionGenerator(db)
    generator.generate(args.drama_name, args.episode_number, args.force_regen)
