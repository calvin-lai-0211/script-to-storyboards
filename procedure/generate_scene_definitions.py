import time
import argparse
import json
import re
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class SceneDefinitionGenerator:
    def __init__(self):
        self.db = Database(DB_CONFIG)
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
                        version='0.1'
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
# 背景
你是一位富有远见的电影导演和美术指导。你的任务是根据剧本，为特定场景创建一个详细的图像生成提示词。目标是生成一个权威性的、高质量的关键帧，以捕捉场景的氛围、光线和核心情感。

# 剧本内容
以下是该集的剧本内容：
---
{script_content}
---

# 任务
根据提供的剧本，为场景“{scene_name}”创建一个单一、详细且生动的图像生成提示词。最终输出必须是一个JSON对象。

# 指令
1.  **深度分析场景**: 仔细阅读剧本，理解场景的地点、情绪、时间、关键动作和情感基调。思考场景的“历史”与“现状”。例如，一个曾经华丽但现已破败的客厅，应在细节中体现其昔日的辉煌与如今的衰败。
2.  **输出JSON格式**: 你的全部输出必须是一个格式正确的单一JSON对象，不包含任何外部文本。JSON必须包含“reflection”和“prompt”两个键。
3.  **'reflection'字段**: 在此字段中，记录你的分析与思考。解释你对场景氛围、光线、关键物品及整体感觉的结论。例如：“这个场景是角色内心的避风港，尽管物质条件陈旧，但处处透露出温馨和主人的巧思，应使用暖色调和柔和的光线来表现。”
4.  **'prompt'字段**: 在此字段中，根据你的思考编写最终的、详细的图像生成提示词（for 即梦4.0 模型）。这应是一个可直接使用的单一字符串。
5.  **提示词内容**: 提示词应追求逼真的电影风格。详细描述场景的构图、光线、色彩和关键元素。
6.  **关键焦点**: 图像应代表整个场景的氛围和环境。
7.  **无人物，纯场景**: 除非剧本特别指示，否则场景中不应包含任何人物。专注于环境、建筑、物体和氛围。

# 示例 (针对不同场景)
```json
{{
  "reflection": "这是一个侦探在案件陷入僵局时深夜独处的办公室。空间应感觉混乱但有生活气息，反映他内心的挣扎。光线是关键，应是孤独、戏剧性的。混乱中应有秩序，显示出他的专业性。",
  "prompt": "电影级广角镜头，一个1940年代风格的侦探办公室，时间是深夜。整个房间光线昏暗，只有一盏绿色银行家台灯照亮了凌乱的木制办公桌的一角，桌上散落着案件档案、照片和半满的咖啡杯。月光透过百叶窗的缝隙，在地板上投下条纹光影。空气中似乎有尘埃在光束中浮动。整个场景色调偏冷，充满黑色电影的神秘和孤独感。空无一人。逼真写实，8K，细节丰富。"
}}
```

现在，为场景“{scene_name}”生成JSON。
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate scene definitions and store them in the database.")
    parser.add_argument("drama_name", type=str, help="The name of the drama.")
    parser.add_argument("episode_number", type=int, help="The episode number.")
    parser.add_argument("--force-regen", action="store_true", help="Force regeneration of scene definitions even if they already exist.")
    args = parser.parse_args()

    generator = SceneDefinitionGenerator()
    generator.generate(args.drama_name, args.episode_number, args.force_regen)
