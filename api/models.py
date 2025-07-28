from pydantic import BaseModel, Field, field_validator
from typing import Optional

from enum import Enum


class MergePosition(Enum):
    TOP = 'top'
    BOTTOM = 'bottom'
    LEFT = 'left'
    RIGHT = 'right'
    
class MergedImage(BaseModel):
    background_path: str
    foreground_path: str
    merged_image_path: str
    aspect_ratio: float
    merge_position: MergePosition
    merge_margin_ratio: float
    merge_foreground_ratio: float

    @field_validator('aspect_ratio')
    def validate_aspect_ratio(cls, v):
        if v < 0.1 or v > 100:
            raise ValueError('aspect_ratio must be in range (0.1, 100)')
        return v

    @field_validator('merge_margin_ratio')
    def validate_merge_margin_ratio(cls, v):
        if v < 0 or v > 1:
            raise ValueError('merge_margin_ratio must be in range (0, 1)')
        return v

    @field_validator('merge_foreground_ratio')
    def validate_merge_foreground_ratio(cls, v):
        if v < 0 or v > 1:
            raise ValueError('merge_foreground_ratio must be in range (0, 1)')
        return v

class MergedImageResponse(MergedImage):
    merged_image_url: str

class GenerateRequest(MergedImage):
    full_name: str = Field(..., description="Full name of the person")
    gender: str = Field(..., description="Gender of the person")
    birthday: str = Field(..., description="Birthday in ISO format (YYYY-MM-DD)")
    greeting_text_instructions: Optional[str] = None

class GenerateResponse(BaseModel):
    image_url: str
    background_path: str
    foreground_path: str
    merged_image_path: str