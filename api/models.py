"""
Pydantic models for API requests and responses.
"""
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

# Generic type for response data
T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """
    Unified API response format.
    - code=0: success
    - code!=0: error (e.g., 400=bad request, 404=not found, 500=server error)
    """
    code: int
    data: Optional[T] = None
    message: str = "success"

    @classmethod
    def success(cls, data: Any = None, message: str = "success"):
        """Create a successful response"""
        return cls(code=0, data=data, message=message)

    @classmethod
    def error(cls, code: int, message: str, data: Any = None):
        """Create an error response"""
        return cls(code=code, data=data, message=message)

class GenerateStoryboardRequest(BaseModel):
    script_title: str
    episode_number: int
    force_regen: bool = False

class GenerateDefinitionsRequest(BaseModel):
    drama_name: str
    episode_number: int
    force_regen: bool = False

class GenerateImageRequest(BaseModel):
    image_prompt: str

class StatusResponse(BaseModel):
    status: str
    message: str
