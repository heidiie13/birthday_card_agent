from typing_extensions import Optional
from langchain_core.messages import AnyMessage
from pydantic import BaseModel

class AgentState(BaseModel):
    # Conversation and feedback
    messages: list[AnyMessage]
    feedback: Optional[str]

    # User info and style
    full_name: str
    gender: str
    birthday: str
    recipient: Optional[str]
    style: Optional[str]

    # Image info
    background_path: Optional[str]
    foreground_path: Optional[str]
    merged_image_path: Optional[str]
    dominant_color: Optional[str]
    merged_with_text_path: Optional[str]
    
    # Text info
    greeting_text: Optional[str]
    font_color: Optional[str]
    font_path: Optional[str]

    # Merge params
    merge_position: str
    merge_margin_ratio: float
    merge_aspect_ratio: float
    merge_foreground_ratio: float

    # Text params
    text_position: str = "bottom"
    text_margin_ratio: float = 0.05
    text_ratio: float = 1/3
    font_size: int = 48
   