"""
Pydantic models for API requests and responses.
"""
from typing import Any, Optional, Generic, TypeVar, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

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

# ==================== Request Models ====================

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

# ==================== Response Data Models ====================

class CharacterPortrait(BaseModel):
    """Character portrait data structure"""
    id: int
    drama_name: str
    episode_number: int
    character_name: str
    image_prompt: Optional[str] = None
    reflection: Optional[str] = None
    image_url: Optional[str] = None
    is_key_character: bool = False
    character_brief: Optional[str] = None

class CharacterListData(BaseModel):
    """Response data for character list"""
    characters: List[CharacterPortrait]
    count: int

class CharactersByKeyData(BaseModel):
    """Response data for characters by script key"""
    key: str
    drama_name: str
    episode_number: int
    characters: List[CharacterPortrait]
    count: int

class CharacterDetailData(BaseModel):
    """Response data for single character detail"""
    id: int
    drama_name: str
    episode_number: int
    character_name: str
    image_prompt: Optional[str] = None
    reflection: Optional[str] = None
    image_url: Optional[str] = None
    is_key_character: bool
    character_brief: Optional[str] = None

class GenerateImageData(BaseModel):
    """Response data for image generation"""
    character_id: int
    image_url: str
    local_path: Optional[str] = None

class SceneDefinition(BaseModel):
    """Scene definition data structure"""
    id: int
    drama_name: str
    episode_number: int
    scene_name: str
    image_prompt: Optional[str] = None
    reflection: Optional[str] = None
    image_url: Optional[str] = None

class SceneListData(BaseModel):
    """Response data for scene list"""
    scenes: List[SceneDefinition]
    count: int

class ScenesByKeyData(BaseModel):
    """Response data for scenes by script key"""
    key: str
    drama_name: str
    episode_number: int
    scenes: List[SceneDefinition]
    count: int

class PropDefinition(BaseModel):
    """Prop definition data structure"""
    id: int
    drama_name: str
    episode_number: int
    prop_name: str
    image_prompt: Optional[str] = None
    reflection: Optional[str] = None
    image_url: Optional[str] = None

class PropListData(BaseModel):
    """Response data for prop list"""
    props: List[PropDefinition]
    count: int

class PropsByKeyData(BaseModel):
    """Response data for props by script key"""
    key: str
    drama_name: str
    episode_number: int
    props: List[PropDefinition]
    count: int

class FlatStoryboard(BaseModel):
    """Flat storyboard record from database"""
    id: int
    scene_number: str
    scene_description: str
    shot_number: str
    shot_description: str
    sub_shot_number: str
    camera_angle: str
    characters: List[str]
    scene_context: List[str]
    key_props: List[str]
    image_prompt: str
    video_prompt: Optional[str] = None
    dialogue_sound: str
    duration_seconds: int
    notes: str

class StoryboardData(BaseModel):
    """Response data for storyboard (flat structure)"""
    key: str
    drama_name: str
    episode_number: int
    storyboards: List[FlatStoryboard]
    count: int

class ScriptMetadata(BaseModel):
    """Script metadata from database"""
    script_id: Optional[int] = None
    key: str
    title: str
    episode_num: int
    author: Optional[str] = None
    creation_year: Optional[int] = None
    score: Optional[float] = None

class ScriptListData(BaseModel):
    """Response data for script list"""
    scripts: List[ScriptMetadata]
    count: int

class ScriptDetail(BaseModel):
    """Script detail with content from database"""
    script_id: Optional[int] = None
    key: str
    title: str
    episode_num: int
    content: str
    roles: Optional[List[str]] = None
    sceneries: Optional[List[str]] = None
    author: Optional[str] = None
    creation_year: Optional[int] = None
    score: Optional[float] = None

class EpisodeMemory(BaseModel):
    """Episode memory/summary data from database"""
    id: int
    script_name: str
    episode_number: int
    plot_summary: str
    options: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# ==================== Typed Response Models ====================

class CharacterListResponse(ApiResponse[CharacterListData]):
    """Typed response for character list"""
    pass

class CharactersByKeyResponse(ApiResponse[CharactersByKeyData]):
    """Typed response for characters by key"""
    pass

class CharacterDetailResponse(ApiResponse[CharacterDetailData]):
    """Typed response for character detail"""
    pass

class GenerateImageResponse(ApiResponse[GenerateImageData]):
    """Typed response for image generation"""
    pass

class SceneListResponse(ApiResponse[SceneListData]):
    """Typed response for scene list"""
    pass

class ScenesByKeyResponse(ApiResponse[ScenesByKeyData]):
    """Typed response for scenes by key"""
    pass

class PropListResponse(ApiResponse[PropListData]):
    """Typed response for prop list"""
    pass

class PropsByKeyResponse(ApiResponse[PropsByKeyData]):
    """Typed response for props by key"""
    pass

class StoryboardResponse(ApiResponse[StoryboardData]):
    """Typed response for storyboard"""
    pass

class ScriptListResponse(ApiResponse[ScriptListData]):
    """Typed response for script list"""
    pass

class ScriptDetailResponse(ApiResponse[ScriptDetail]):
    """Typed response for script detail"""
    pass

class MemoryResponse(ApiResponse[EpisodeMemory]):
    """Typed response for memory"""
    pass
