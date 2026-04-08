from pydantic import BaseModel, Field, validator
from typing import Literal


# =============================================================================
# REQUEST
# =============================================================================
class StoryRequest(BaseModel):
    language: Literal["Hindi", "English", "Gujarati"] = "Hindi"
    age_group: Literal["4-6", "6-8", "8-10"] = "6-8"
    theme: str = Field(..., min_length=2, max_length=100)

    @validator("language", pre=True)
    def normalize_language(cls, v: str) -> str:
        return v.strip().capitalize()

    @validator("theme", pre=True)
    def normalize_theme(cls, v: str) -> str:
        return v.strip()


# =============================================================================
# RESPONSE
# =============================================================================
class StoryData(BaseModel):
    title: str
    story: str
    audio_url: str
    tts_status: Literal["success", "failed"]
    language: str
    age_group: str
    theme: str
    duration_seconds: float = 0.0


class StoryResponse(BaseModel):
    status: Literal["success", "error"]
    request_id: str
    data: StoryData | None = None
    message: str = ""
    duration_seconds: float = 0.0