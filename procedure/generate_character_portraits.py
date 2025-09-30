import time
import json
import re
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class CharacterPortraitGenerator:
    def __init__(self):
        self.db = Database(DB_CONFIG)
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
            
            # 4. Get all sub-shot details where the character appears
            sub_shots_details = self.db.get_sub_shots_for_character(drama_name, episode_number, char_name)
            if not sub_shots_details:
                print(f"Could not find any shots for character '{char_name}'. Skipping.")
                continue

            shots_appeared = [shot['sub_shot_number'] for shot in sub_shots_details]
            print(f"Character '{char_name}' appears in shots: {shots_appeared}")

            # 5. Build the prompt for the LLM
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
                        reflection=reflection
                    )
                    break # Success, exit retry loop
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for '{char_name}': {e}")
                    if attempt + 1 < max_retries:
                        time.sleep(5)
                    else:
                        print(f"All retries failed for '{char_name}'. Skipping.")

        print(f"\n--- Character portrait generation completed for '{drama_name}' Episode {episode_number} ---")

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
# 背景
你是一位资深的电影导演和角色设计师。你的任务是根据剧本和角色在不同场景中的具体行为，为特定角色创建一个详细的图像生成提示词。目标是创造一个能够捕捉角色精髓的、高质量的、权威性的肖像。

# 剧本内容
这是本集的剧本内容：
---
{script_content}
---

# 角色出场场景
为了清晰和准确的视觉效果，以下是角色“{character_name}”出现的所有子镜头摘要：
---
{shots_context}
---

# 任务
根据所提供的剧本和角色的场景，为角色“{character_name}”创建一个详细生动的图像生成提示词。最终输出必须是一个JSON对象。

# 指令
1.  **深度分析角色**: 仔细阅读剧本和场景摘要，理解角色的性格、社会地位、年龄、性别和情绪状态。至关重要的是，要分析角色的**背景与当前处境**的对比。例如，一个出身富裕家庭但目前陷入贫困的角色，可能穿着陈旧的衣服，但这些衣服会保持干净且质地优良，显示出其残留的品味和自尊。
2.  **输出JSON格式**: 你的全部输出必须是一个格式良好的单一JSON对象。不要在JSON结构之外包含任何文字。JSON必须包含两个键："reflection" 和 "prompt"。
3.  **'reflection'字段**: 在此字段中，写下你的分析和推理。解释你关于角色背景、当前状态的结论，以及这些因素如何影响他们的外貌、衣着和所处环境（例如，“家虽老旧但有一定品味且整洁”）。
4.  **'prompt'字段**: 在此字段中，写入最终的、详细的图像生成提示词（for 即梦4.0 模型, 用中文提示词）。这个提示词应该是你反思的直接成果。它必须是一个单一的字符串，高度详细，并可直接用于AI图像生成器。
5.  **提示词内容**: 提示词应追求照片般逼真、电影化的风格。提及摄像机角度、光线、构图和具体的视觉元素。图像必须只包含一个人（角色本人），为上半身肖像，表情自然。
6.  **关键要求：仅限单人**: 生成的图像必须只包含目标角色“{character_name}”。不要在图像中包含任何其他人物、角色或形象。肖像应为专注于这一个角色的单人照。

# 示例 (针对不同角色)
```json
{{
  "reflection": "该角色是一位失势的前高级官员。他住在一间简朴的老旧公寓里，但自尊心仍在。尽管装饰过时，但布置得很有品味且一尘不染。他的衣服虽然陈旧，但剪裁精良且保养得很好，这表明他很珍视自己过去的地位。他的表情应该疲惫但有尊严，而不是被打败的样子。",
  "prompt": "电影感的上半身肖像，一位有尊严的中年男子身处一间光线昏暗、整洁但老旧的公寓里。他眼神疲惫但充满自豪，尽管环境简陋，外表依旧整洁。他穿着一件略显磨损但质地优良的粗花呢夹克。背景中可瞥见一个干净有序的房间和复古家具。柔和而忧郁的窗光照亮了他的一侧脸庞。照片般逼真，8K，焦点清晰，情感复杂。"
}}
```

现在，为角色“{character_name}”生成JSON。
"""
