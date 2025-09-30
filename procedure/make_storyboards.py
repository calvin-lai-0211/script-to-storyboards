import json
import time
import re
from utils.database import Database
from utils.config import DB_CONFIG
from models.yizhan_llm import YiZhanLLM

class MakeStoryboardsText:
    def __init__(self, db_connection: Database):
        self.db = db_connection
        # Initialize YiZhanLLM without a specific API key.
        # The class will now select the correct key based on the model name.
        self.llm = YiZhanLLM()

    def generate(self, base_script_title: str, episode_number: int, force_regen: bool = False):
        """
        Generates a storyboard in JSON format for a specific episode from a script in the database.
        """
        # Check if storyboard data already exists for this episode
        table_name = "flat_storyboards"
        if not force_regen and self.db.check_records_exist(table_name, base_script_title, episode_number):
            print(f"Storyboard data for '{base_script_title}' Episode {episode_number} already exists. Skipping generation.")
            return

        if force_regen:
            print(f"Force regeneration enabled. Clearing existing storyboard data for '{base_script_title}' Episode {episode_number}...")
            self.db.clear_records(table_name, base_script_title, episode_number)

        print(f"Fetching script for: '{base_script_title}' Episode {episode_number}")
        episode_script = self.db.get_episode_script(base_script_title, episode_number)

        if not episode_script:
            print(f"Could not retrieve script content for Episode {episode_number}. Aborting.")
            return None

        print(f"\n--- Generating storyboard for Episode {episode_number} ---")
        
        prompt = ""
        if episode_number == 1:
            prompt = self._build_prompt(episode_script)
        else:
            print(f"--- Fetching memory from previous episodes (1 to {episode_number - 1}) ---")
            previous_episode_numbers = list(range(1, episode_number))
            
            episode_summaries = self.db.get_episode_memories(base_script_title, previous_episode_numbers)
            characters = self.db.get_character_definitions(base_script_title, previous_episode_numbers)
            scenes = self.db.get_scene_definitions(base_script_title, previous_episode_numbers)
            props = self.db.get_key_prop_definitions(base_script_title, previous_episode_numbers)

            prompt = self._build_prompt_with_memory(
                script_content=episode_script,
                episode_summaries=episode_summaries,
                characters=characters,
                scenes=scenes,
                props=props
            )
        
        storyboard_json = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Generating storyboard for Episode {episode_number} via LLM (streaming)...")
                
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
                    episode_number=episode_number
                )
                
                break  # Break the retry loop on success

            except Exception as e:
                print(f"\nAttempt {attempt + 1} of {max_retries} for Episode {episode_number} failed: {e}")
                if attempt + 1 < max_retries:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"All retries for Episode {episode_number} failed.")
        
        return storyboard_json
        
    def _format_memory_for_prompt(self, memory_data, title):
        if not memory_data:
            return ""
        
        formatted_string = f"# {title}\n"
        for item in memory_data:
            if 'plot_summary' in item:
                formatted_string += f"## 第 {item['episode_number']} 集摘要\n- {item['plot_summary']}\n\n"
            elif 'character_name' in item:
                formatted_string += f"## 角色: {item['character_name']}\n- 简介: {item.get('character_brief', 'N/A')}\n- 形象参考: {item.get('image_prompt', 'N/A')}\n\n"
            elif 'scene_name' in item:
                formatted_string += f"## 场景: {item['scene_name']}\n- 简介: {item.get('scene_brief', 'N/A')}\n- 气氛参考: {item.get('image_prompt', 'N/A')}\n\n"
            elif 'prop_name' in item:
                formatted_string += f"## 道具: {item['prop_name']}\n- 简介: {item.get('prop_brief', 'N/A')}\n- 形象参考: {item.get('image_prompt', 'N/A')}\n\n"
        return formatted_string

    def _build_prompt_with_memory(self, script_content, episode_summaries, characters, scenes, props):
        episode_memory_str = self._format_memory_for_prompt(episode_summaries, "前情提要")
        character_memory_str = self._format_memory_for_prompt(characters, "已确立的角色")
        scene_memory_str = self._format_memory_for_prompt(scenes, "已确立的场景")
        prop_memory_str = self._format_memory_for_prompt(props, "已确立的关键道具")

        return f"""
你是一位专业的导演（亚利桑德罗·冈萨雷斯·伊纳里图 (Alejandro González Iñárritu)） 你要学习他的分镜方式和表现力，
且擅长为快节奏的戏剧创作详细的分镜脚本。

# 任务
你的任务是仔细分析下面提供的**新一集**剧本，并生成一个结构清晰、内容详细的分镜脚本。

# 关键记忆和连续性指令 (非常重要!)
为了保持剧集的连续性，你**必须**严格遵循以下已经建立的角色、场景和道具设定。
在生成新的分镜时，如果提到以下任何内容，**必须使用完全相同的名称**。

---
{episode_memory_str}
---
{character_memory_str}
---
{scene_memory_str}
---
{prop_memory_str}
---

# 核心指令
1.  **严格的JSON格式**：最终输出必须是一个格式正确的JSON对象。不要在JSON代码块之外添加任何解释性文字。
2.  **完整性第一**：你必须确保分镜脚本覆盖了剧本中的**所有**场景和关键情节。**不要忽略剧本中出现的任何角色、明确指明的场景地点或关键道具**。
3.  **层级结构**：分镜需要有清晰的层级：`场景 (Scene)` -> `镜头 (Shot)` -> `子镜头 (Sub-shot)`。
4.  **镜头切换**：每当人物、机位、或核心动作发生变化时，都应切换到新的`镜头 (Shot)`。
5.  **子镜头定义**：每个`子镜头 (Sub-shot)`代表一个持续3到5秒的、连贯的单一动作，因为是短剧，尽可能少人（不多于2人参与）。
6.  **节奏控制**：牢记这是一部短剧，节奏至关重要。请保持镜头的快速和简洁，迅速带入情节。
7.  **场景定义**：场景定义需要给出场景的全局名称，场景的描述需要给出场景的位置，场景的氛围，场景的时间，场景的关键动作，场景的情感基调。
              特别注意： **同一个场景不允许有多个名称，保证场景的一致性**。必须参考上面的 "已确立的场景" 列表。
8.  **道具定义**：特别注意： **同一个道具不允许有多个名称，保证道具的一致性**。必须参考上面的 "已确立的关键道具" 列表。
9.  **人物定义**：特别注意： **同一个人不允许有多个名称，保证人物的一致性**。必须参考上面的 "已确立的角色" 列表。

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
          "shot_description": "【文字描述】对这个一级镜头的简要描述，例如：主角A进入房间。该描述出现的人物描述，需要和涉及人物字段一致，不允许用简称代词造成歧义，同样在场景描述和道具描述也是。",
          "sub_shots": [
            {{
              "sub_shot_number": "1.1.1",
              "景别/机位": "【例如：中景，过肩镜头，特写】",
              "涉及人物": ["【人物A】", "【人物B】", 注意人物A，人物B全局名称的归一化，不能一个人物出现两个名字，人物没有给出姓名，尽可能给出全面的角色和身份推断],
              "涉及场景": ["【例如：夜晚的书房】", "【人物A家的厨房】","注意场景全局名称的归一化，不能同一个场景出现两个名字，场景没有给出名称，尽可能给出全面的场景的位置和角色关联的地理位置推断，地理位置名称必须给人物，时间限定语给全，例如 catherine20年前的家"],
              "涉及关键道具": ["【例如：神秘的信件】", "【主角的怀表】", "注意关键道具全局名称的归一化，特别是跨场景出现的道具"],
              "布景/人物/动作（生成首帧的prompt）": "【一段详细的文字，用于AI绘画生成该分镜的首帧图像。需要包含景别、人物外貌、表情、动作、布景、光线和整体风格。例如：'中景，一位40多岁的疲惫侦探坐在黑暗办公室凌乱的办公桌前，只有一盏台灯照亮着他，他表情关切地看着一份案件档案，黑色电影风格。'】",
              "wan2.5 生成视频的prompt”：【包括视频动作，音频，镜头，以及音频等等】
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

# 新一集的剧本内容
---
{script_content}
---
"""

    def _build_prompt(self, script_content):
        return f"""
你是一位专业的导演（亚利桑德罗·冈萨雷斯·伊纳里图 (Alejandro González Iñárritu)） 你要学习他的分镜方式和表现力，
且擅长为快节奏的戏剧创作详细的分镜脚本。

# 任务
你的任务是仔细分析下面提供的剧本，并生成一个结构清晰、内容详细的分镜脚本。

# 核心指令
1.  **严格的JSON格式**：最终输出必须是一个格式正确的JSON对象。不要在JSON代码块之外添加任何解释性文字。
2.  **完整性第一**：你必须确保分镜脚本覆盖了剧本中的**所有**场景和关键情节。**不要忽略剧本中出现的任何角色、明确指明的场景地点或关键道具**。
3.  **层级结构**：分镜需要有清晰的层级：`场景 (Scene)` -> `镜头 (Shot)` -> `子镜头 (Sub-shot)`。
4.  **镜头切换**：每当人物、机位、或核心动作发生变化时，都应切换到新的`镜头 (Shot)`。
5.  **子镜头定义**：每个`子镜头 (Sub-shot)`代表一个持续3到5秒的、连贯的单一动作，因为是短剧，尽可能少人（不多于2人参与）。
6.  **节奏控制**：牢记这是一部短剧，节奏至关重要。请保持镜头的快速和简洁，迅速带入情节。
7.  **场景定义**：场景定义需要给出场景的全局名称，场景的描述需要给出场景的位置，场景的氛围，场景的时间，场景的关键动作，场景的情感基调。
              特别注意： **同一个场景不允许有多个名称，保证场景的一致性**。
8.  **道具定义**：特别注意： **同一个场景不允许有多个名称，保证场景的一致性**。

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
          "shot_description": "【文字描述】对这个一级镜头的简要描述，例如：主角A进入房间。该描述出现的人物描述，需要和涉及人物字段一致，不允许用简称代词造成歧义，同样在场景描述和道具描述也是。",
          "sub_shots": [
            {{
              "sub_shot_number": "1.1.1",
              "景别/机位": "【例如：中景，过肩镜头，特写】",
              "涉及人物": ["【人物A】", "【人物B】", 注意人物A，人物B全局名称的归一化，不能一个人物出现两个名字，人物没有给出姓名，尽可能给出全面的角色和身份推断],
              "涉及场景": ["【例如：夜晚的书房】", "【人物A家的厨房】","注意场景全局名称的归一化，不能同一个场景出现两个名字，场景没有给出名称，尽可能给出全面的场景的位置和角色关联的地理位置推断，地理位置名称必须给人物，时间限定语给全，例如 catherine20年前的家"],
              "涉及关键道具": ["【例如：神秘的信件】", "【主角的怀表】", "注意关键道具全局名称的归一化，特别是跨场景出现的道具"],
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
