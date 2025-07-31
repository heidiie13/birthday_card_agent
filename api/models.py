from typing import Optional
from enum import Enum
from pydantic import BaseModel

class CardType(str, Enum):
    birthday = "birthday"
    graduation = "graduation"

class GenerateRequest(BaseModel):
    greeting_text_instructions: str
    background_path: Optional[str] = None
    foreground_path: Optional[str] = None
    merged_image_path: Optional[str] = None

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
