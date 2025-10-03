"""
FastAPI main application entry point.
Refactored to use modular route files.
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import signal
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Script-to-Storyboards API",
    description="Automated storyboard generation from text scripts",
    version="0.1.0",
    docs_url="/api/docs",       # Swagger UI 移动到 /api/docs
    redoc_url="/api/redoc",     # ReDoc 移动到 /api/redoc
    openapi_url="/api/openapi.json"  # OpenAPI spec URL
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for AuthenticationError
@app.exception_handler(Exception)
async def authentication_error_handler(request: Request, exc: Exception):
    """Handle AuthenticationError and return HTTP 200 with error details in body."""
    from api.middleware.auth import AuthenticationError

    if isinstance(exc, AuthenticationError):
        return JSONResponse(
            status_code=200,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": exc.data
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )

    # Re-raise other exceptions to be handled by FastAPI default handlers
    raise exc

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logger.info("Received shutdown signal, cleaning up...")
    import sys
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Import and register routers
from api.routes import health, characters, storyboards, scenes, scripts, props, upload, user, google_auth

app.include_router(health.router)
app.include_router(user.router)
app.include_router(google_auth.router)
app.include_router(characters.router)
app.include_router(storyboards.router)
app.include_router(scenes.router)
app.include_router(scripts.router)
app.include_router(props.router)
app.include_router(upload.router)

if __name__ == "__main__":
    import uvicorn
    import os

    # Read port from environment variable, default to 8001 for local dev
    port = int(os.getenv("API_PORT", "8001"))

    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
