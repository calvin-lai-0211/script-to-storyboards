# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Script-to-Storyboards** is an automated content creation pipeline that converts text scripts into visual storyboards with character portraits and scene keyframes. It combines LLMs (Gemini 2.5 Pro) and text-to-image models (Qwen Image, Jimeng) to generate structured storyboard scripts and visual assets, inspired by director Alejandro González Iñárritu's cinematic style.

## Core Architecture

### Database-Driven Workflow
The project uses PostgreSQL as the central data store with four main tables:
- `scripts`: Stores raw script content, episodes, characters, and scenes
- `flat_storyboards`: Denormalized storyboard data with scene/shot/sub-shot hierarchy
- `character_portraits`: Character image prompts and generated portrait URLs
- `scene_definitions`: Scene image prompts and keyframe URLs

### Three-Layer Structure
1. **Models Layer** (`models/`): AI model wrappers
   - `yizhan_llm.py`: LLM client (Gemini, DeepSeek) with streaming support and image input
   - `jimeng_t2i_RH.py`: Jimeng text-to-image via RunningHub API with concurrency control (max 3 concurrent)
   - `qwen_image_t2i_RH.py`: Qwen text-to-image via RunningHub API
   - `flux_kontext_img2img_RH.py`: Image-to-image transformations
   - `wan_vace_img2video_RH.py`: Video generation (future feature)

2. **Procedure Layer** (`procedure/`): Core workflow scripts
   - `make_storyboards.py`: Converts scripts to JSON storyboards using Gemini 2.5 Pro with Iñárritu-style prompts
   - `generate_character_portraits.py`: Extracts characters and generates portrait prompts
   - `generate_scene_definitions.py`: Extracts scenes and generates scene keyframe prompts
   - `make_portraits_from_t2i.py`: Generates actual portrait images using threading with concurrency control
   - `generate_scene_images.py`: Generates scene keyframe images

3. **Utils Layer** (`utils/`):
   - `database.py`: PostgreSQL operations wrapper with auto-initialization on instantiation
   - `config.py`: Contains DB credentials, API keys, and model configurations

### Storyboard JSON Structure
The LLM generates hierarchical storyboards:
```
Scene (场景) → Shot (镜头) → Sub-shot (子镜头)
```
Each sub-shot includes: camera angle (景别/机位), characters (涉及人物), scenes (涉及场景), image prompt (布景/人物/动作), video prompt, dialogue/sound effects, duration, and director notes.

## Common Development Commands

### Database Initialization
```bash
python utils/database.py
```
Creates all required tables automatically. The `Database` class auto-initializes schema on instantiation.

### Complete Pipeline Workflow

1. **Import Script to Database**
```bash
python from_script_to_database.py
```
Modify script to set the correct script file path and episode metadata.

2. **Generate Storyboard Script**
```bash
python demo_make_storyboards_from_scripts.py
```
Modify `script_title` variable to match your script name. Uses Gemini 2.5 Pro with streaming output.

3. **Generate Character Portrait Prompts**
```bash
python demo_create_character_portraits.py
```
Modify `drama_name` and `episode_number` variables.

4. **Generate Scene Definition Prompts**
```bash
python demo_create_scene_definitions.py
```
Modify `drama_name` and `episode_number` variables.

5. **Generate Character Portrait Images**
```bash
python procedure/make_portraits_from_t2i.py "剧本名" 集数 -m [jimeng|qwen]
# Example:
python procedure/make_portraits_from_t2i.py "天归(「西语版」)" 1 -m jimeng
```
Uses threading with concurrency control (max 3 concurrent tasks).

6. **Generate Scene Keyframe Images**
```bash
python procedure/generate_scene_images.py "剧本名" 集数 -m [jimeng|qwen]
# Example:
python procedure/generate_scene_images.py "天归(「西语版」)" 1 -m qwen
```

### Output Structure
Generated images are saved to:
```
images/
  └── {剧本名}/
      └── {集数}/
          ├── {角色名}.jpg          # Character portraits
          └── scenes/
              └── scene_{场景名}.jpg # Scene keyframes
```

## Key Implementation Details

### LLM Response Handling
- `make_storyboards.py` uses regex (`re.search(r"\{[\s\S]*\}", response)`) to extract JSON from LLM responses that may contain markdown code blocks or explanatory text
- Retry logic (max 3 attempts) with 5-second delays on failures
- Streaming support with `(content_chunk, reasoning_chunk)` tuple yields

### Image Generation Concurrency
- `jimeng_t2i_RH.py` implements `RunningHubConcurrencyManager` to prevent TASK_QUEUE_MAXED errors
- Max 3 concurrent tasks with conservative threshold
- Uses `try_submit_task()` atomic lock to prevent race conditions
- Task submission retries with exponential backoff and jitter on queue errors

### Database Connection Pattern
All database operations follow:
```python
conn = self._get_connection()
try:
    # operations
    conn.commit()
except Exception as e:
    if conn: conn.rollback()
finally:
    if conn: conn.close()
```

### Character and Scene Name Normalization
The storyboard generation prompt explicitly requires:
- Character names: Global name consistency across all shots (no duplicate names for same character)
- Scene names: Global name consistency with location/character association inference

## Configuration Notes

- Database credentials and API keys are in `utils/config.py` (not version controlled)
- `YIZHAN_API_CONFIG`: Contains API keys for different LLMs (DeepSeek, Gemini, default)
- `RUNNINGHUB_API_CONFIG`: RunningHub API settings with node IDs, timeouts, and model parameters
- Model selection in `YiZhanLLM._get_api_key()` chooses appropriate key based on model name

## Testing and Debugging

- Use `console.debug` for debug logging (per user's global instructions)
- No formal test files exist; testing via demo scripts
- LLM responses can be monitored via streaming output: `print(content_chunk, end='', flush=True)`

## Future Features

- Video generation using `wan_vace_img2video` with `video_prompt` from storyboards
- Audio integration (TTS and sound effects)
- Web UI for non-technical users