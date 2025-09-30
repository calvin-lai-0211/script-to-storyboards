import time
import json
import re
import concurrent.futures
from utils.database import Database
from utils.config import DB_CONFIG, MAX_CONCURRENT_THREADS
from models.yizhan_llm import YiZhanLLM

class CharacterPortraitGenerator:
    def __init__(self, db_connection: Database):
        self.db = db_connection
        self.llm = YiZhanLLM()

    def generate(self, drama_name: str, episode_number: int, force_regen: bool = False):
        """
        Generates character portrait prompts for all characters in a specific episode.
        """
        table_name = "character_portraits"
        if not force_regen and self.db.check_records_exist(table_name, drama_name, episode_number):
            print(f"Character portraits for '{drama_name}' Episode {episode_number} already exist. Skipping.")
            return

        if force_regen:
            print(f"Force regeneration enabled. Clearing existing character portraits for '{drama_name}' Episode {episode_number}...")
            self.db.clear_records(table_name, drama_name, episode_number)

        print(f"--- Starting character portrait generation for '{drama_name}' Episode {episode_number} ---")
        
        # 1. Get all unique character names for the episode
        characters = self.db.get_characters_for_episode(drama_name, episode_number)
        if not characters:
            print("No characters found for this episode. Aborting.")
            return

        # 2. Fetch previous character definitions if not the first episode
        previous_character_briefs = {}
        if episode_number > 1:
            print(f"Fetching character definitions from previous episodes...")
            previous_episode_numbers = list(range(1, episode_number))
            previous_character_defs = self.db.get_character_definitions(drama_name, previous_episode_numbers)
            previous_character_briefs = {
                item['character_name']: item.get('character_brief', '')
                for item in previous_character_defs if item.get('character_brief')
            }
            print(f"Found previous briefs for: {list(previous_character_briefs.keys())}")

        # 3. Get the script content for the episode
        # get_episodes_by_base_title returns a list of contents, ordered by episode_num
        all_episodes_content = self.db.get_episodes_by_base_title(drama_name)
        if not all_episodes_content or episode_number > len(all_episodes_content):
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return
        script_content = all_episodes_content[episode_number - 1]

        # 4. Concurrently generate prompts for each character
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_THREADS) as executor:
            # Create a future for each character
            futures = {
                executor.submit(
                    self._generate_for_single_character,
                    drama_name,
                    episode_number,
                    script_content,
                    char_name,
                    previous_character_briefs.get(char_name) # Pass previous brief if exists
                ): char_name for char_name in characters
            }
            
            for future in concurrent.futures.as_completed(futures):
                char_name = futures[future]
                try:
                    future.result()  # We call result() to raise any exceptions that occurred
                except Exception as e:
                    print(f"An error occurred while processing character '{char_name}': {e}")

        print(f"\n--- Character portrait generation completed for '{drama_name}' Episode {episode_number} ---")

    def _generate_for_single_character(self, drama_name: str, episode_number: int, script_content: str, char_name: str, previous_brief: str = None):
        """
        Generates and stores the image prompt for a single character.
        This method is designed to be called concurrently.
        """
        print(f"\n--- Processing character: {char_name} ---")
        
        # 4. Get all sub-shot details where the character appears
        sub_shots_details = self.db.get_sub_shots_for_character(drama_name, episode_number, char_name)
        if not sub_shots_details:
            print(f"Could not find any shots for character '{char_name}'. Skipping.")
            return

        shots_appeared = [shot['sub_shot_number'] for shot in sub_shots_details]
        print(f"Character '{char_name}' appears in shots: {shots_appeared}")

        # 5. Build the prompt for the LLM
        prompt = ""
        if previous_brief:
            print(f"Found previous brief for '{char_name}'. Using memory-enhanced prompt.")
            prompt = self._build_prompt_with_memory(script_content, char_name, sub_shots_details, previous_brief)
        else:
            prompt = self._build_prompt(script_content, char_name, sub_shots_details)

        # 6. Call LLM to generate the image prompt
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating image prompt for '{char_name}' (Attempt {attempt + 1})...")
                response_tuple = self.llm.chat(
                    user_message=prompt,
                    model="gemini-2.5-pro",
                    stream=False  # We need the full response
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
                is_key_character = response_json.get("is_key_character")
                character_brief = response_json.get("character_brief")

                if not image_prompt:
                    raise ValueError("JSON response does not contain a 'prompt' field.")

                print(f"Successfully generated and extracted image prompt for '{char_name}'.")
                
                # 7. Insert the result into the database
                self.db.insert_character_portrait(
                    drama_name=drama_name,
                    episode_number=episode_number,
                    character_name=char_name,
                    image_prompt=image_prompt,
                    shots_appeared=shots_appeared,
                    reflection=reflection,
                    version='0.1',
                    is_key_character=is_key_character,
                    character_brief=character_brief
                )
                return # Success, exit function
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for '{char_name}': {e}")
                if attempt + 1 < max_retries:
                    time.sleep(5)
                else:
                    print(f"All retries failed for '{char_name}'. Skipping.")
                    raise  # Re-raise the exception to be caught by the future
    
    def _build_prompt_with_memory(self, script_content: str, character_name: str, sub_shots_details: list, previous_brief: str) -> str:
        shots_context = "\n".join([
            f"  - Shot {shot['sub_shot_number']}: "
            f"Scene: {shot.get('scene_description', 'N/A')}, "
            f"Action: {shot.get('image_prompt', 'N/A')}, "
            f"Dialogue/Sound: {shot.get('dialogue_sound', 'N/A')}"
            for shot in sub_shots_details
        ])

        return f"""
# CONTEXT
You are a senior film director and character designer. Your task is to **update** a character's definition and image prompt based on new scenes from a new episode.

# CHARACTER'S PREVIOUS BRIEF
This is the existing summary of the character "{character_name}" based on previous episodes:
---
{previous_brief}
---

# SCRIPT CONTENT FOR THE NEW EPISODE
Here is the script content for the new episode:
---
{script_content}
---

# CHARACTER'S NEW SCENES IN THIS EPISODE
Here is a summary of all sub-shots where "{character_name}" appears in the **new episode**:
---
{shots_context}
---

# TASK
Your goal is to **update and enrich** the character's definition. Based on the new scenes, you will create an updated `character_brief` and a corresponding image `prompt`. The final output must be a single JSON object.

# INSTRUCTIONS
1.  **Analyze New Information**: Read the new script and scenes. How do the character's actions or dialogue in this episode add to or change our understanding of them?
2.  **Update Character Brief**: **Rewrite** the `character_brief`. It must be a new, single sentence that integrates the old brief with the new information from this episode. This should be a cumulative summary.
3.  **Determine if Key Character**: A character is "key" if they have a proper name, are crucial to the plot, and are likely to appear again. This status is unlikely to change episode to episode, but confirm it.
4.  **Aesthetic Enhancement for Key Characters**: For characters identified as **key** and having a **positive or protagonist role**, enhance their appearance. Men should be described as **handsome** and women as **beautiful**. For older female characters, their beauty should be described as timeless and enduring, still evident despite their age.
5.  **Physicality and Appearance**: The image prompt should reflect the **updated understanding** of the character based on the new episode's context. **Crucially, ensure the prompt still specifies the character's inferred age and Hispanic/Latino ethnicity for consistency.**
6.  **Condition and Wear (Noble Poverty Theme)**: When updating the character's appearance, continue to adhere to the "Noble Poverty" theme. For **key and positive or protagonist characters**, the visual representation of their clothing must be subtle.
    - **Wear**: Any aging, fading, or wear from the new episode's context must be described as **'slightly'** or **'subtly'**. The effect should be barely perceptible, not drastic.
    - **Cleanliness**: Their clothes must **always** be described as **impeccably clean** and well-maintained.
7.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object with keys: "reflection", "prompt", "is_key_character", and "character_brief".
8.  **'reflection' Field**: Explain how the new scenes informed your updated description. For example: "In this episode, the character showed a moment of unexpected defiance. I've updated their brief to reflect this inner strength, and the prompt now suggests a more determined gaze."
9.  **'prompt' Field**: Write the new, updated, detailed image generation prompt. It must still be a waist-up, front-facing, photorealistic portrait of only the single character, and **must begin with the character's ethnicity and age**.
10. **'is_key_character' Field**: A boolean (`true` or `false`).
11. **'character_brief' Field**: The new, updated, cumulative one-sentence summary.

# EXAMPLE (for updating a character)
```json
{{
  "reflection": "The character was previously defined by her dignity amidst poverty. In this new episode, she actively sells family heirlooms, showing a more pragmatic and desperate side. My updated brief reflects this struggle between maintaining appearances and surviving. The prompt is updated to show a hint of worry in her otherwise serene expression.",
  "prompt": "cinematic waist-up front-facing portrait of an elegant Hispanic woman in her late 30s... She has a dignified but subtly worried expression... (rest of the detailed prompt)",
  "is_key_character": true,
  "character_brief": "A resilient woman from a fallen noble family, now forced to sell heirlooms, struggling to maintain her dignity amidst increasing desperation."
}}
```

Now, generate the updated JSON for the character "{character_name}".
"""

    def _build_prompt(self, script_content: str, character_name: str, sub_shots_details: list) -> str:
        """
        Builds the prompt to generate a character's image prompt.
        """
        # Format the sub-shot details for inclusion in the prompt
        shots_context = "\n".join([
            f"  - Shot {shot['sub_shot_number']}: "
            f"Scene: {shot.get('scene_description', 'N/A')}, "
            f"Action: {shot.get('image_prompt', 'N/A')}, "
            f"Dialogue/Sound: {shot.get('dialogue_sound', 'N/A')}"
            for shot in sub_shots_details
        ])

        return f"""
# CONTEXT
You are a senior film director and character designer. Your task is to create a detailed image generation prompt for a specific character, based on the provided script and their scenes. The goal is to create a definitive, high-quality portrait that captures the character's essence.

# SCRIPT CONTENT
Here is the script content for the episode:
---
{script_content}
---

# CHARACTER'S SCENES
For clarity and a precise visual, here is a summary of all sub-shots where the character "{character_name}" appears:
---
{shots_context}
---

# TASK
Based on the script and scenes, create a detailed, vivid image generation prompt for the character "{character_name}". The final output must be a single JSON object.

# INSTRUCTIONS
1.  **Deep Character Analysis**: Read the script and summaries to understand the character's personality, social status, and emotions. From this, you **must infer their specific age** (e.g., 'a man in his late 40s') and **ethnicity (assume Hispanic/Latino for this drama)**.
2.  **Determine if Key Character**: A character is considered "key" if they meet **all** the following criteria:
    a. They have a proper, formal name (e.g., "Leonardo", not "Thug A").
    b. They are crucial for advancing the plot.
3.  **Character Brief**: Write a concise one-sentence summary of the character's role in the story.
4.  **Aesthetic Enhancement for Key Characters**: If a character is identified as **key** and has a **positive or protagonist role**, you must enhance their appearance in the prompt. Men should be described as **handsome** and women as **beautiful**. For older female characters, their beauty should be described as timeless and enduring, still clearly visible despite their age. This is a critical instruction.
5.  **Infer Physicality from Personality**: Based on your character analysis, infer their likely physical build, posture, and typical expression. For example, a timid and anxious character might be described as having a 'slender build and a worried expression,' while a confident leader might have a 'strong posture and a determined gaze.' This inference is critical for creating a believable portrait.
6.  **Facial Details**: When describing the character's face, focus on permanent features that define their history and personality, such as long-term scars or birthmarks. **Critically, you must ignore temporary conditions** like dirt, stains, black eyes, or bruises from recent events, as the portrait should represent their fundamental appearance, not a transient state.
7.  **CRITICAL THEME - Noble Poverty**: You must analyze the contrast between the character's potentially noble background and their current state of poverty. This theme is central to the visual representation. When describing clothing, be extremely detailed:
    - **Style**: Specify the cut and type of garment with refined details. The style should reflect a refined taste and noble heritage:
      * **For Noble Women**: Victorian-inspired high-collared blouses with pearl buttons, A-line midi dresses with subtle pleating, tailored wool coats with structured shoulders, silk scarves draped elegantly, vintage brooches or simple pearl earrings
      * **For Noble Men**: Double-breasted wool coats with peaked lapels, crisp white dress shirts with French cuffs, tailored trousers with sharp creases, silk ties in muted colors, pocket watches on chains, leather dress shoes (even if worn)
      * **General Elements**: Classic cuts that never go out of style, attention to proportions and fit, subtle but quality details like mother-of-pearl buttons, fine stitching, or delicate embroidery
    - **Color Palette**: Deeply consider the colors that reflect both nobility and current circumstances. **Please choose randomly to avoid repetition**:
      * **Noble Heritage Colors**: Deep jewel tones (emerald, sapphire, burgundy), classic navy, charcoal grey, ivory, or rich earth tones that suggest quality and refinement，
      * **Faded Elegance**: These noble colors should appear as muted or softened by time - a once-vibrant burgundy now appears as dusty rose, a deep navy has faded to slate blue, emerald has become sage green
      * **Timeless Neutrals**: Cream, beige, soft grey, or muted pastels that maintain dignity while showing the passage of time
      * **Avoid**: Bright, flashy colors or overly saturated hues that would suggest new wealth or poor taste
    - **Condition & Material**: Describe the clothing as 'old', 'worn', or 'faded', but emphasize that the material is of **high quality** (e.g., fine cotton, aged silk, durable tweed).
    - **Condition and Wear**: For **key and positive or protagonist characters**, the depiction of clothing is critical for the "Noble Poverty" theme.
        - **Wear**: Any signs of age, such as being old, worn, or faded, must be described with extreme subtlety. Use modifiers like **'slightly'** or **'subtly'**. The effect should be barely perceptible and not drastic (e.g., 'a subtly faded collar', not 'a heavily faded shirt').
        - **Cleanliness**: Crucially, their clothes must **always** be described as **impeccably clean** and well-maintained, for example, 'neatly pressed despite its age'. This emphasizes their dignity.
    8.  **Output JSON Format**: Your entire output must be a single, well-formed JSON object with no external text. It must contain four keys: "reflection", "prompt", "is_key_character", and "character_brief".
    9.  **'reflection' Field**: Write down your analysis here. Explain your conclusions about the character's background versus their current situation and how this duality should influence their appearance and clothing. 
    For example: "Despite their poverty, their noble origins mean they maintain their clothes meticulously. The fabric is faded but of high quality."
10. **'prompt' Field**: Write the final, detailed image generation prompt here (for the Jimeng 4.0 model, in English). This prompt must be a direct result of your reflection. It must be a single, highly-detailed string.
11. **'is_key_character' Field**: A boolean value (`true` or `false`).
12. **'character_brief' Field**: A string containing the one-sentence summary.
13. **Prompt Content**: The prompt must describe a **waist-up, front-facing portrait**. It **must begin with the character's inferred ethnicity and age** (e.g., "A Hispanic man in his 40s..."). It should aim for a photorealistic, cinematic style. Mention lighting and composition. The character should have a natural expression.
14. **CRITICAL: Single Character Only**: The generated image must contain ONLY the target character "{character_name}". No other people or figures.

# EXAMPLE (for a different character)
```json
{{
  "reflection": "The character is a descendant of a noble family that has fallen on hard times. She lives in a modest home, but her dignity is intact. Her dress is old and faded but was clearly expensive and is impeccably clean. This contrast shows her resilience and refusal to let circumstances define her. Her expression should be thoughtful, not sorrowful.",
  "prompt": "cinematic waist-up front-facing portrait of an elegant Hispanic woman in her late 30s, from a noble but impoverished family. She has a dignified and serene expression, looking directly at the camera. She wears a high-collared dress made of a fine, high-quality cotton; the color is faded from many washes but the fabric is impeccably clean and neatly pressed with minimal wrinkles. The garment's style is classic and timeless, showing signs of being well-cared-for despite its age. The setting is a humble but tidy room, with soft, natural light. Photorealistic, 8K, sharp focus, understated elegance.",
  "is_key_character": true,
  "character_brief": "A resilient woman from a fallen noble family, struggling to maintain her dignity amidst poverty."
}}
```

Now, generate the JSON for the character "{character_name}".
"""
