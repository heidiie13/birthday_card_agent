from pydantic import BaseModel
from typing import Optional

class MergedImage(BaseModel):
    background_path: str
    foreground_path: str
    merged_image_path: str
    aspect_ratio: float
    merge_position: str
    merge_margin_ratio: float
    merge_foreground_ratio: float

class MergedImageResponse(MergedImage):
    merged_image_url: str

class GenerateRequest(MergedImage):
    full_name: str
    gender: str
    birthday: str
    extra_requirements: Optional[str] = None

class GenerateResponse(BaseModel):
    image_url: str
    background_path: str
    foreground_path: str
    merged_image_path: str