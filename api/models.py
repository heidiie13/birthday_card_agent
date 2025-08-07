from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class CardType(str, Enum):
    """
    Enum representing different types of cards.
    """
    birthday = "birthday"
    christmas = "christmas"
    graduation = "graduation"
    newyear = "newyear"
    lunar_newyear = "lunar_newyear"
    mid_autumn_festival = "mid_autumn_festival"
    valentine = "valentine"
    vietnam_teacherday = "vietnam_teacherday"
    vietnam_nationalday = "vietnam_nationalday"
    vietnam_womenday = "vietnam_womenday"
    wedding = "wedding"
    international_womenday = "international_womenday"
    general = "general"

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
    aspect_ratio: AspectRatio = Field(3/4, description="Aspect ratio of the card, 3:4 or 4:3")

    class Config:
        json_schema_extra = {
            "example": {
                "greeting_text_instructions": "Tạo lời chúc sinh nhật vui vẻ và ý nghĩa cho bạn thân",
                "background_path": "static/images/backgrounds/back_23.png",
                "foreground_path": "static/images/foregrounds/birthday_3.webp",
                "merged_image_path": "static/images/card_types/birthday/6db7ec52-da44-4eed-98da-7f366be230c4.png",
                "aspect_ratio": 0.75
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

class BackgroundUploadResponse(BaseModel):
    background_url: str = Field(..., description="URL of the background image")
    background_path: str = Field(..., description="Path to the background image")
    color: str = Field(..., description="Dominant color of the background image")

    class Config:
        json_schema_extra = {
            "example": {
                "background_url": "https://example.com/static/images/backgrounds/uploads/background.png",
                "background_path": "static/images/backgrounds/uploads/background.png",
                "color": "#FF5733"
            }
        }

class TemplateUploadResponse(BaseModel):
    merged_image_url: str = Field(..., description="URL of the merged template image")
    merged_image_path: str = Field(..., description="Path to the merged template image")
    foreground_path: str = Field(..., description="Path to the foreground image")
    background_path: str = Field(..., description="Path to the background image")
    card_type: str = Field(..., description="Type of the card")
    aspect_ratio: AspectRatio = Field(..., description="Aspect ratio of the template")

    class Config:
        json_schema_extra = {
            "example": {
                "merged_image_url": "https://example.com/static/images/card_types/birthday/template.png",
                "merged_image_path": "static/images/card_types/birthday/template.png",
                "foreground_path": "static/images/foregrounds/uploads/foreground.png",
                "background_path": "static/images/backgrounds/uploads/background.png",
                "card_type": "birthday",
                "aspect_ratio": 0.75
            }
        }

class TemplateResponse(BaseModel):
    background_path: str = Field(..., description="Path to the background image")
    foreground_path: str = Field(..., description="Path to the foreground image")
    merged_image_path: str = Field(..., description="Path to the merged image")
    aspect_ratio: AspectRatio = Field(..., description="Aspect ratio of the template")
    merged_image_url: str = Field(..., description="URL of the merged image")

    class Config:
        json_schema_extra = {
            "example": {
                "background_path": "static/images/backgrounds/back_1.png",
                "foreground_path": "static/images/foregrounds/fore_1.png",
                "merged_image_path": "static/images/cards/template_1.png",
                "aspect_ratio": 0.75,
                "merged_image_url": "https://example.com/static/images/cards/template_1.png"
            }
        }
