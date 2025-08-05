from typing import Optional, List
from langchain_core.messages import AnyMessage
from pydantic import BaseModel

class State(BaseModel):
    # Conversation and feedback
    messages: List[AnyMessage] = []

    greeting_text_instructions: str = None

    # Image info
    background_path: Optional[str] = None
    foreground_path: Optional[str] = None
    merged_image_path: Optional[str] = None
    dominant_color: Optional[str] = None
    card_path: Optional[str] = None
    card_type: Optional[str] = None
    
    # Text info
    greeting_text: Optional[str] = None
    title: Optional[str] = None
    font_color: Optional[str] = None
    font_path: Optional[str] = None
    font_size: int = 80
    title_font_path: Optional[str] = None
    title_font_size: int = 100

    # Merge params
    merge_position: str = "top"
    merge_margin_ratio: float = 0.02
    aspect_ratio: float = 3/4
    merge_foreground_ratio: float = 1/2

    # Text params
    text_position: Optional[str] = None
    text_margin_ratio: float = 0.06
    text_ratio: Optional[float] = None