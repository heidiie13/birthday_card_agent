from typing import Annotated
from typing_extensions import TypedDict, Optional
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    messages: list[AnyMessage]
    full_name: str
    gender: str
    birthday: str
    recipient: Optional[str]
    style: Optional[str]
    merged_image_path: str
    background_path: Optional[str]
    foreground_path: Optional[str]
    greeting_text: Optional[str]
    font_color: Optional[str]
    dominant_color: Optional[str]
    feedback: Optional[str]
   