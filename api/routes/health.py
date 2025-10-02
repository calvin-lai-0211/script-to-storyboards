"""
Health check endpoints.
"""
from fastapi import APIRouter, Response
from api.models import ApiResponse

router = APIRouter()

@router.get("/")
async def root(response: Response):
    """Root endpoint."""
    try:
        return ApiResponse.success(data={
            "message": "Script-to-Storyboards API",
            "version": "0.1.0"
        })
    except Exception as e:
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.get("/health")
async def health(response: Response):
    """Health check endpoint."""
    try:
        return ApiResponse.success(data={"status": "healthy"})
    except Exception as e:
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))

@router.get("/api/health")
async def api_health(response: Response):
    """Health check endpoint under /api prefix."""
    try:
        return ApiResponse.success(data={"status": "healthy"})
    except Exception as e:
        response.status_code = 500
        return ApiResponse.error(code=500, message=str(e))
