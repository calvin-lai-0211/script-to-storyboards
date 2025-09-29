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
基于提供的剧本，为角色"{character_name}"创建一个详细生动的图像生成提示词。

# INSTRUCTIONS
1.  **分析角色**: 仔细阅读剧本，理解角色的性格、社会地位、年龄、性别、典型服装和情感状态。
2.  **具体描述**: 提示词必须高度详细。提及具体的视觉元素。
3.  **格式要求**: 输出应该是单一文本块，可直接用作高级AI图像生成器（如Qwen Image或Midjourney）的提示词。不要包含任何额外文字、解释或标签。
4.  **风格要求**: 提示词应追求写实、电影感的风格。提及摄影角度、光照和构图。
5.  **重要限制**: 画面中只能出现一个人物，即角色本身。必须是上半身肖像（upper body portrait），表情自然正常。

# EXAMPLE PROMPT (for a different character)
"cinematic upper body portrait of a sophisticated middle-aged businesswoman in a modern office setting. She has confident eyes, well-groomed appearance, and is wearing a tailored navy blue blazer over a crisp white blouse. Her hair is styled professionally, and she has subtle makeup. The background shows a blurred modern office environment with soft natural lighting from a window. Professional, clean aesthetic, photorealistic, 8K, sharp focus, neutral expression."

现在，为角色"{character_name}"生成提示词。
"""
