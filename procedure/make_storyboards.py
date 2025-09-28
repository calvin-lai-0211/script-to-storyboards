import json
import time
import re
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class MakeStoryboardsText:
    def __init__(self):
        self.db = Database(DB_CONFIG)
        # Initialize YiZhanLLM without a specific API key.
        # The class will now select the correct key based on the model name.
        self.llm = YiZhanLLM()

    def generate(self, base_script_title):
        """
        Generates a storyboard in JSON format from a script in the database.
        """
        print(f"Fetching episodes for script: '{base_script_title}'")
        episodes_content = self.db.get_episodes_by_base_title(base_script_title)

        if not episodes_content:
            print("Could not retrieve script content. Aborting.")
            return None

        all_storyboards = []
        for i, episode_script in enumerate(episodes_content):
            episode_num = i + 1
            print(f"\n--- Generating storyboard for Episode {episode_num} ---")
            
            prompt = self._build_prompt(episode_script)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Generating storyboard for Episode {episode_num} via LLM (streaming)...")
                    
                    stream_generator = self.llm.chat(
                        user_message=prompt,
                        model="gemini-2.5-pro",
                        stream=True
                    )
                    
                    full_response_content = ""
                    print("AI Response: ", end="", flush=True)
                    for content_chunk, reasoning_chunk in stream_generator:
                        if content_chunk:
                            print(content_chunk, end="", flush=True)
                            full_response_content += content_chunk
                    
                    print("\n--- Stream completed ---")

                    # Use regex to extract the JSON object from the potentially messy LLM response
                    json_match = re.search(r"\{[\s\S]*\}", full_response_content)
                    
                    if not json_match:
                        raise ValueError("No valid JSON object found in the LLM response.")

                    json_string = json_match.group(0)
                    storyboard_json = json.loads(json_string)
                    print("Successfully generated and parsed storyboard JSON.")

                    # Insert the storyboard into the database
                    director_style = "Alejango González Iñárritu"
                    self.db.insert_flat_storyboard(
                        drama_name=base_script_title,
                        director_style=director_style,
                        storyboard_data=storyboard_json,
                        episode_number=episode_num
                    )
                    
                    all_storyboards.append(storyboard_json)
                    break  # Break the retry loop on success

                except Exception as e:
                    print(f"\nAttempt {attempt + 1} of {max_retries} for Episode {episode_num} failed: {e}")
                    if attempt + 1 < max_retries:
                        print("Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        print(f"All retries for Episode {episode_num} failed. Skipping to next episode.")
            
        return all_storyboards
        
    def _build_prompt(self, script_content):
        return f"""
你是一位专业的导演（亚利桑德罗·冈萨雷斯·伊纳里图 (Alejandro González Iñárritu)） 你要学习他的分镜方式和表现力，
且擅长为快节奏的戏剧创作详细的分镜脚本。

先介绍 亚利桑德罗·冈萨雷斯·伊纳里图  的镜头的风格，然后在做如下任务。

# 任务
你的任务是仔细分析下面提供的剧本，并生成一个结构清晰、内容详细的分镜脚本。

# 核心指令
1.  **严格的JSON格式**：最终输出必须是一个格式正确的JSON对象。不要在JSON代码块之外添加任何解释性文字。
2.  **层级结构**：分镜需要有清晰的层级：`场景 (Scene)` -> `镜头 (Shot)` -> `子镜头 (Sub-shot)`。
3.  **镜头切换**：每当人物、机位、或核心动作发生变化时，都应切换到新的`镜头 (Shot)`。
4.  **子镜头定义**：每个`子镜头 (Sub-shot)`代表一个持续3到5秒的、连贯的单一动作。
5.  **节奏控制**：牢记这是一部短剧，节奏至关重要。请保持镜头的快速和简洁，迅速带入情节。

# JSON输出规范
请严格遵循以下JSON结构。字段名和层级关系必须完全一致。

```json
{{
  "storyboard": [
    {{
      "scene_number": "场景一",
      "scene_description": "【文字描述】对该场景的环境、氛围和核心事件的整体描述。",
      "shots": [
        {{
          "shot_number": "1.1",
          "shot_description": "【文字描述】对这个一级镜头的简要描述，例如：主角A进入房间。",
          "sub_shots": [
            {{
              "sub_shot_number": "1.1.1",
              "景别/机位": "【例如：中景，过肩镜头，特写】",
              "涉及人物": ["【人物A】", "【人物B】"],
              "涉及场景": "【例如：夜晚的书房】",
              "布景/人物/动作（生成首帧的prompt）": "【一段详细的文字，用于AI绘画生成该分镜的首帧图像。需要包含景别、人物外貌、表情、动作、布景、光线和整体风格。例如：'中景，一位40多岁的疲惫侦探坐在黑暗办公室凌乱的办公桌前，只有一盏台灯照亮着他，他表情关切地看着一份案件档案，黑色电影风格。'】",
              “wan2.5 生成视频的prompt”：【包括视频动作，音频，镜头，以及音频等等】
              "对白/音效": "【人物对白或关键音效。例如：'主角A：“我找到线索了。” 音效：远处传来警笛声。'】",
              "时长(秒)": 4,
              "备注": "【导演的额外备注。例如：'镜头缓慢推向主角面部' 或 '快速剪辑'】"
            }}
          ]
        }}
      ]
    }}
  ]
}}
```

# 剧本内容
---
{script_content}
---
"""
