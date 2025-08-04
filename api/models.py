from typing import Optional
from enum import Enum
from pydantic import BaseModel

class CardType(str, Enum):
    birthday = "birthday"
    graduation = "graduation"
    wedding = "wedding"
    valentine = "valentine"
    new_year = "new_year"
    general = "general"
    christmas = "christmas"
    teacher_day = "teacher_day"

class AspectRatio(float, Enum):
    ratio_3_4 = 3 / 4
    ratio_4_3 = 4 / 3

class GenerateRequest(BaseModel):
    greeting_text_instructions: str
    background_path: Optional[str] = None
    foreground_path: Optional[str] = None
    merged_image_path: Optional[str] = None
    aspect_ratio: Optional[float] = 3/4

class BackgroundResponse(BaseModel):
    background_url: str
    background_path: str

class GenerateResponse(BaseModel):
    card_url: str

class TemplateResponse(BaseModel):
    background_path: str
    foreground_path: str
    merged_image_path: str
    aspect_ratio: Optional[float] = None
    merge_position: Optional[str] = None
    merge_margin_ratio: Optional[float] = None
    merge_foreground_ratio: Optional[float] = None
    merged_image_url: str
