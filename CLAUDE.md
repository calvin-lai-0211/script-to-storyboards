# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Script-to-Storyboards** is an automated content creation pipeline that converts text scripts into visual storyboards with character portraits and scene keyframes. It combines LLMs (Gemini 2.5 Pro) and text-to-image models (Qwen Image, Jimeng) to generate structured storyboard scripts and visual assets, inspired by director Alejandro González Iñárritu's cinematic style.

## Core Architecture

### Database-Driven Workflow
The project uses PostgreSQL as the central data store with five main tables:
- `scripts`: Stores raw script content, episodes, characters, and scenes
- `flat_storyboards`: Denormalized storyboard data with scene/shot/sub-shot hierarchy
- `character_portraits`: Character image prompts and generated portrait URLs
- `scene_definitions`: Scene image prompts and keyframe URLs
- `users`: User authentication data for Google OAuth login

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
   - `database.py`: PostgreSQL operations wrapper
     - `Database(db_config, auto_init=False)`: Initialize database connection
     - `auto_init=True`: Creates all tables on initialization (only for setup scripts)
     - `auto_init=False` (default): Skip table creation for better performance in production/API
   - `config.py`: Contains DB credentials (with timeouts), API keys, and model configurations

### Storyboard JSON Structure
The LLM generates hierarchical storyboards:
```
Scene (场景) → Shot (镜头) → Sub-shot (子镜头)
```
Each sub-shot includes: camera angle (景别/机位), characters (涉及人物), scenes (涉及场景), image prompt (布景/人物/动作), video prompt, dialogue/sound effects, duration, and director notes.

## Deployment

### Local Development (Docker Compose)

Quick start for local development:
```bash
cd docker/compose
docker-compose up -d
```

Access at:
- Frontend: http://localhost:5173
- API: http://localhost:8001

See [Docker Compose README](docker/compose/README.md) for details.

### Kubernetes Deployment

Deploy to local K8s cluster (k3d/k3s):
```bash
cd docker/k8s
./local-deploy.sh
```

The script will:
1. Build Docker images
2. Import images to K8s
3. Deploy Redis, API, Frontend
4. Optionally deploy Ingress (port 80)

**Access via Ingress**: http://localhost:8080 (k3d maps 80→8080)

**Important K8s Resources**:
- `redis-deployment.yaml`: Session storage (Redis)
- `api-deployment.yaml`: Backend API service
- `frontend-deployment.yaml`: Frontend web service
- `nginx-configmap.yaml`: Nginx configuration
- `ingress.yaml`: Unified entry point (optional)

**Quick Commands**:
```bash
# View status
kubectl get pods

# View logs
kubectl logs -f deployment/storyboard-api

# Restart service
kubectl rollout restart deployment/storyboard-api

# Update API only
./update-api.sh

# Clean up
./undeploy.sh
```

See [docs/k8s/README.md](docs/k8s/README.md) for complete K8s deployment guide.

**Quick Links**:
- [开发入门指南](docs/dev/getting-started.md) - 所有开发模式的完整教程
- [Git Hooks 和 CI/CD](docs/dev/git-hooks-and-ci.md) - 代码提交规范和自动化
- [前端文档](docs/frontend/README.md) - React 前端完整技术文档
- [Kubernetes 部署](docs/k8s/README.md) - K8s 部署指南（含故障排查）

## Common Development Commands

### Database Initialization
```bash
python utils/database.py
```
Creates all required tables. Use `Database(DB_CONFIG, auto_init=True)` when setting up the database for the first time.

**Performance Note**: In production/API code, use `Database(DB_CONFIG)` (without `auto_init`) to skip table creation checks and improve performance.

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

## Authentication and Authorization

### Google OAuth Login
The API now requires authentication for most endpoints. Authentication flow:

1. **User Check**: `/api/user/check-login` returns Google auth URL if not logged in
2. **Google Login**: User authorizes via Google OAuth 2.0
3. **Callback**: `/api/user/google/callback` receives auth code, exchanges for tokens
4. **Session Creation**: User data stored in Redis with 30-day TTL
5. **Cookie**: Session ID stored in `st_sess_id` cookie (HttpOnly, SameSite=Lax)

### Protected Routes
Most API routes require authentication using `Depends(require_auth)`:
- `/api/storyboards/*` - Storyboard data access
- `/api/characters/*` - Character data
- `/api/scenes/*` - Scene data
- `/api/scripts/*` - Script management
- `/api/props/*` - Props management
- `/api/upload` - File uploads

### Session Management
- **Storage**: Redis (falls back to in-memory if unavailable)
- **Key Format**: `st_session:{session_id}`
- **Timeout**: 2592000 seconds (30 days)
- **Auto-extend**: TTL renewed on each access

### Configuration
Update `utils/config.py`:
```python
GOOGLE_OAUTH_CONFIG = {
    "client_id": "YOUR_GOOGLE_CLIENT_ID",
    "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8001/api/user/google/callback"
}
```

See [docs/dev/google-oauth-authentication.md](docs/dev/google-oauth-authentication.md) for detailed setup instructions.

## Testing and Debugging

- Use `console.debug` for debug logging (per user's global instructions)
- No formal test files exist; testing via demo scripts
- LLM responses can be monitored via streaming output: `print(content_chunk, end='', flush=True)`

## Future Features

- Video generation using `wan_vace_img2video` with `video_prompt` from storyboards
- Audio integration (TTS and sound effects)
- Web UI for non-technical users
- Additional OAuth providers (Discord, GitHub)
- Refresh token auto-renewal
- User permissions and roles