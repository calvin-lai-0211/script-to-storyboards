import time
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class CharacterPortraitGenerator:
    def __init__(self):
        self.db = Database(DB_CONFIG)
        self.llm = YiZhanLLM()

    def generate(self, drama_name: str, episode_number: int):
        """
        Generates character portrait prompts for all characters in a specific episode.
        """
        print(f"--- Starting character portrait generation for '{drama_name}' Episode {episode_number} ---")
        
        # 1. Get all unique character names for the episode
        characters = self.db.get_characters_for_episode(drama_name, episode_number)
        if not characters:
            print("No characters found for this episode. Aborting.")
            return

        # 2. Get the script content for the episode
        # get_episodes_by_base_title returns a list of contents, ordered by episode_num
        all_episodes_content = self.db.get_episodes_by_base_title(drama_name)
        if not all_episodes_content or episode_number > len(all_episodes_content):
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return
        script_content = all_episodes_content[episode_number - 1]

        # 3. Loop through each character to generate and store their portrait prompt
        for char_name in characters:
            print(f"\n--- Processing character: {char_name} ---")
            
            # 4. Get all shots where the character appears
            shots_appeared = self.db.get_shots_for_character_in_episode(drama_name, episode_number, char_name)
            print(f"Character '{char_name}' appears in shots: {shots_appeared}")

            # 5. Build the prompt for the LLM
            prompt = self._build_prompt(script_content, char_name)

            # 6. Call LLM to generate the image prompt
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Generating image prompt for '{char_name}' (Attempt {attempt + 1})...")
                    image_prompt = self.llm.chat(
                        user_message=prompt,
                        model="gemini-2.5-pro",
                        stream=False  # We need the full response
                    )
                    print(f"Successfully generated image prompt for '{char_name}'.")
                    
                    # 7. Insert the result into the database
                    self.db.insert_character_portrait(
                        drama_name=drama_name,
                        episode_number=episode_number,
                        character_name=char_name,
                        image_prompt=image_prompt,
                        shots_appeared=shots_appeared
                    )
                    break # Success, exit retry loop
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for '{char_name}': {e}")
                    if attempt + 1 < max_retries:
                        time.sleep(5)
                    else:
                        print(f"All retries failed for '{char_name}'. Skipping.")

        print(f"\n--- Character portrait generation completed for '{drama_name}' Episode {episode_number} ---")

    def _build_prompt(self, script_content: str, character_name: str) -> str:
        """
        Builds the prompt to generate a character's image prompt.
        """
        return f"""
# CONTEXT
You are a creative director and character designer. Your task is to create a detailed image generation prompt for a specific character based on a script. The goal is to create a definitive, high-quality portrait that captures the essence of the character.

# SCRIPT CONTENT
Here is the script content for the episode:
---
{script_content}
---

# TASK
Based on the script provided, create a detailed and vivid image generation prompt for the character: "{character_name}".

# INSTRUCTIONS
1.  **Analyze the Character**: Read the script carefully to understand the character's personality, social status, age, gender, typical clothing, and emotional state.
2.  **Be Specific**: The prompt must be highly detailed. Mention specific visual elements.
3.  **Format**: The output should be a single block of text, ready to be used as a prompt for an advanced AI image generator like Qwen Image or Midjourney. Do not include any extra text, explanations, or labels.
4.  **Style**: The prompt should aim for a photorealistic, cinematic style. Mention camera angles, lighting, and composition.

# EXAMPLE PROMPT (for a different character)
"cinematic full-body portrait of a gritty, middle-aged male detective in his cluttered, dimly lit office at night. He has tired eyes, a wrinkled brow, and a five-o'clock shadow. He's wearing a rumpled trench coat over a stained white shirt and loosened tie. The office is filled with stacks of case files, an overflowing ashtray, and a bottle of whiskey on the desk. The only light source is a single desk lamp, casting long, dramatic shadows. Moody, film noir aesthetic, photorealistic, 8K, sharp focus."

Now, generate the prompt for the character "{character_name}".
"""
