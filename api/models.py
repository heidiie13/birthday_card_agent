from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class CardType(str, Enum):
    """
    Enum representing different types of cards.
    """
    birthday = "birthday"
    graduation = "graduation"
    wedding = "wedding"
    valentine = "valentine"
    new_year = "new_year"
    general = "general"
    christmas = "christmas"
    teacher_day = "teacher_day"

class AspectRatio(float, Enum):
    """
    Enum representing common aspect ratios for cards.
    """
    ratio_3_4 = 3 / 4
    ratio_4_3 = 4 / 3

class GenerateRequest(BaseModel):
    greeting_text_instructions: str = Field(..., description="Instructions for the greeting text")
    background_path: Optional[str] = Field(None, description="Path to the background image")
    foreground_path: Optional[str] = Field(None, description="Path to the foreground image")
    merged_image_path: Optional[str] = Field(None, description="Path to the merged image")
    aspect_ratio: Optional[float] = Field(3/4, description="Aspect ratio of the card, 3:4 or 4:3")

    class Config:
        json_schema_extra = {
            "example": {
                "greeting_text_instructions": "Tạo lời chúc sinh nhật vui vẻ và ý nghĩa cho bạn thân",
                "background_path": "static/images/backgrounds/back_23.png",
                "foreground_path": "static/images/foregrounds/birthday_4.png",
                "merged_image_path": "static/images/card_types/birthday/77cf8c00-0e67-4ea5-96e9-b29d530a3fbc.png",
                "aspect_ratio": 0.75
            }
        }

class ImageUploadResponse(BaseModel):
    foreground_url: str = Field(..., description="URL of the foreground image")
    foreground_path: str = Field(..., description="Path to the foreground image")

    class Config:
        json_schema_extra = {
            "example": {
                "foreground_url": "https://example.com/static/images/foregrounds/uploads/upload.png",
                "foreground_path": "static/images/foregrounds/uploads/upload.png"
            }
        }

class GenerateResponse(BaseModel):
    card_url: str = Field(..., description="URL of the generated card")

    class Config:
        json_schema_extra = {
            "example": {
                "card_url": "https://example.com/static/images/cards/generated_card.png"
            }
        }

class TemplateResponse(BaseModel):
    background_path: str = Field(..., description="Path to the background image")
    foreground_path: str = Field(..., description="Path to the foreground image")
    merged_image_path: str = Field(..., description="Path to the merged image")
    aspect_ratio: Optional[float] = Field(None, description="Aspect ratio of the template")
    merge_position: Optional[str] = Field(None, description="Merge position of the foreground image")
    merge_margin_ratio: Optional[float] = Field(None, description="Merge margin ratio")
    merge_foreground_ratio: Optional[float] = Field(None, description="Merge foreground ratio")
    merged_image_url: str = Field(..., description="URL of the merged image")

    class Config:
        json_schema_extra = {
            "example": {
                "background_path": "static/images/backgrounds/back_1.png",
                "foreground_path": "static/images/foregrounds/fore_1.png",
                "merged_image_path": "static/images/cards/template_1.png",
                "aspect_ratio": 0.75,
                "merge_position": "top",
                "merge_margin_ratio": 0.02,
                "merge_foreground_ratio": 0.5,
                "merged_image_url": "https://example.com/static/images/cards/template_1.png"
            }
        }
