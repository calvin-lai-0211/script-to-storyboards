import time
import argparse
import json
import re
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class KeyPropDefinitionGenerator:
    def __init__(self):
        self.db = Database(DB_CONFIG)
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

        # 2. Get the script content for the episode
        all_episodes_content = self.db.get_episodes_by_base_title(drama_name)
        if not all_episodes_content or episode_number > len(all_episodes_content):
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return
        script_content = all_episodes_content[episode_number - 1]

        # 3. Loop through each prop to generate and store its definition prompt
        for prop_name in props:
            print(f"\n--- Processing key prop: {prop_name} ---")
            
            # 4. Get all sub-shot details where the prop appears
            sub_shots_details = self.db.get_sub_shots_for_key_prop(drama_name, episode_number, prop_name)
            if not sub_shots_details:
                print(f"Could not find any shots for prop '{prop_name}'. Skipping.")
                continue
            
            shots_appeared = [shot['sub_shot_number'] for shot in sub_shots_details]
            print(f"Key prop '{prop_name}' appears in shots: {shots_appeared}")

            # 5. Build the prompt for the LLM
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
                        version='0.1'
                    )
                    break # Success, exit retry loop
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for '{prop_name}': {e}")
                    if attempt + 1 < max_retries:
                        time.sleep(5)
                    else:
                        print(f"All retries failed for '{prop_name}'. Skipping.")

        print(f"\n--- Key prop definition generation completed for '{drama_name}' Episode {episode_number} ---")

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
# 背景
你是一名专业的电影道具师和概念艺术家。你的任务是为特定的关键道具创建一个详细的图像生成提示词。目标是生成一个权威性的、高质量的、且在不同场景中保持一致的道具视觉呈现。

# 剧本内容
为了提供完整背景，这里是全部的剧本内容：
---
{script_content}
---

# 道具出场记录
为确保道具设计与其在故事中的用途保持一致，以下是关键道具“{prop_name}”出现的所有场景摘要：
---
{shots_context}
---

# 任务
根据完整的剧本和道具的具体出场记录，为关键道具“{prop_name}”创建一个单一、详细且生动的图像生成提示词。最终输出必须是一个JSON对象。

# 指令
1.  **分析道具**: 仔细阅读剧本和场景摘要，理解道具的功能、材质、年代、状况（如：全新、磨损、古老）及其对故事和角色的重要性。
2.  **输出JSON格式**: 你的全部输出必须是一个格式正确的单一JSON对象，不包含任何外部文本。JSON必须包含“reflection”和“prompt”两个键。
3.  **'reflection'字段**: 在此字段中，记录你的分析与思考。解释你对道具材质、设计细节、历史感和功能的结论。例如：“这个怀表是角色父亲的遗物，因此尽管年代久远，但应保养良好，表面有细微划痕，材质为黄铜，带有复古的雕花。”
4.  **'prompt'字段**: 在此字段中，根据你的思考编写最终的、详细的图像生成提示词 (for 即梦4.0 模型)。它应是一个可直接使用的单一字符串。
5.  **提示词内容**: 提示词应生成一个干净、独立的道具棚拍图，背景为中性色（如白色或灰色），类似于产品目录或游戏资产。这至关重要。力求照片般的真实感和高分辨率风格。提及能清晰展示道具细节的光线（如“柔和的影棚灯光”）。
6.  **视觉一致性**: 提示词必须能产生一致的视觉效果。如果道具在不同场景中的描述不同（例如，先是干净的，后来变脏了），请为其最中性或最主要的状态创建一个提示词。

# 示例 (针对不同道具)
```json
{{
  "reflection": "这是一个古老的黄铜星盘，是主角家族代代相传的宝物。它应该看起来既精密又饱经风霜，上面的铭文是关键的视觉元素，需要清晰可见。整体感觉是神秘而珍贵。",
  "prompt": "一张照片般逼真的高分辨率棚拍图，一个古董黄铜星盘置于中性灰色背景上。星盘上错综复杂地雕刻着天体图和拉丁铭文。它有使用的痕迹，缝隙中有轻微的铜锈。光线柔和而均匀，凸显了物体的精细细节和金属质感。8K，电影级产品摄影。"
}}
```

现在，为关键道具“{prop_name}”生成JSON。
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate key prop definitions and store them in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("--force-regen", action="store_true", help="Force regeneration of key prop definitions even if they already exist.")
    args = parser.parse_args()

    generator = KeyPropDefinitionGenerator()
    generator.generate(args.drama_name, args.episode_number, args.force_regen)
