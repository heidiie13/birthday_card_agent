from typing import Optional, List
from langchain_core.messages import AnyMessage
from pydantic import BaseModel

class AgentState(BaseModel):
    # Conversation and feedback
    messages: List[AnyMessage] = []

    # User info and style
    full_name: str
    gender: str
    birthday: str
    extra_requirements: Optional[str] = None

    # Image info
    background_path: Optional[str] = None
    foreground_path: Optional[str] = None
    merged_image_path: Optional[str] = None
    dominant_color: Optional[str] = None
    merged_with_text_path: Optional[str] = None
    
    # Text info
    greeting_text: Optional[str] = None
    font_color: Optional[str] = None
    font_path: Optional[str] = None

    # Merge params
    merge_position: str = "top"
    merge_margin_ratio: float = 0.05
    aspect_ratio: float = 3/4
    merge_foreground_ratio: float = 2/3

    # Text params
    text_position: str = "bottom"
    text_margin_ratio: float = 0.05
    text_ratio: float = 1/3
    font_size: int = 20
   