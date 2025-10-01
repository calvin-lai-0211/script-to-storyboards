# Script-to-Storyboards API

FastAPI service for automated storyboard generation from text scripts.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
# Development mode with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python api/main.py
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Health Check
- `GET /` - API root
- `GET /health` - Health check

### Storyboard Generation
- `POST /storyboard/generate` - Generate storyboard for an episode
  ```json
  {
    "script_title": "剧本名称",
    "episode_number": 1,
    "force_regen": false
  }
  ```

### Character Management
- `POST /characters/generate` - Generate character definitions
- `GET /characters/{drama_name}/{episode_number}` - Get all characters

### Scene Management
- `POST /scenes/generate` - Generate scene definitions
- `GET /scenes/{drama_name}/{episode_number}` - Get all scenes

### Props Management
- `POST /props/generate` - Generate key prop definitions

### Episode Management
- `GET /scripts/{script_title}/episodes` - List all episodes

## Example Usage

```bash
# Generate storyboard
curl -X POST "http://localhost:8000/storyboard/generate" \
  -H "Content-Type: application/json" \
  -d '{"script_title": "天归", "episode_number": 1}'

# List episodes
curl "http://localhost:8000/scripts/天归/episodes"

# Get characters
curl "http://localhost:8000/characters/天归/1"
```