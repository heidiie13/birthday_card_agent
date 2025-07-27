import os
import logging
import uuid
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from .tools import merge_foreground_background, add_text_to_image, get_random_font, get_dominant_color
from .prompt import system_prompt, user_prompt_template
from .state import AgentState

load_dotenv()
logger = logging.getLogger(__name__)

def _get_model() -> Runnable:
    try:
        llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("MODEL_NAME"),
        )
        # llm = ChatOpenAI(
        #     base_url=os.getenv("OPENAI_BASE_URL"),
        #     api_key=os.getenv("OPENAI_API_KEY"),
        #     model=model_name,
        #     temperature=0.7,
        #     default_headers={"App-Code": "fresher"},
        #     extra_body={
        #         "service": "test_agent_app",
        #         "chat_template_kwargs": {"enable_thinking": False}
        #     }
        # )
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        return None
    return llm


class ResponseLLM(BaseModel):
    greeting_text: str = Field(description="Greeting text in Vietnamese")
    font_color: str = Field(description="Font color in hex format, e.g., #FFFFFF")

def llm_node(state: AgentState) -> AgentState:
    llm = _get_model()
    prompt = user_prompt_template.format(**state.model_dump())
    messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content=prompt)]
    parsed: ResponseLLM = llm.with_structured_output(ResponseLLM).invoke(messages)
    state.messages.append(AIMessage(content=parsed.model_dump_json()))
    state.greeting_text = parsed.greeting_text
    state.font_color = parsed.font_color
    return state

def add_text_node(state: AgentState) -> AgentState:
    image_path = state.merged_image_path
    output_path = f"static/merged/{uuid.uuid4().hex}.png"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    font_path = state.font_path or get_random_font()
    add_text_to_image(
        image_path=image_path,
        output_path=output_path,
        text=state.greeting_text,
        font_color=state.font_color,
        font_path=font_path,
        font_size=state.font_size,
        text_position=state.text_position,
        margin_ratio=state.text_margin_ratio,
        text_ratio=state.text_ratio,
    )
    state.merged_with_text_path = output_path
    state.font_path = font_path
    return state

def dominant_color_node(state: AgentState) -> AgentState:
    bg_path = state.background_path
    color = get_dominant_color(bg_path)
    state.dominant_color = color
    return state

import os
import uuid
from .tools import merge_foreground_background

def merge_node(state: AgentState) -> AgentState:
    """Process merging foreground and background images with updated state."""
    # Set default values
    state.font_size = 70
    state.merge_margin_ratio = 0.05

    # Determine text position based on merge position
    position_map = {
        "left": "right",
        "right": "left",
        "top": "bottom",
        "bottom": "top"
    }
    state.text_position = position_map.get(state.merge_position, "top")

    greeting_words = len(state.greeting_text.split()) if state.greeting_text else 0

    # Set merge_foreground_ratio based on aspect ratio and greeting length
    if greeting_words < 20:
        state.merge_foreground_ratio = 2/3
    elif greeting_words < 40:
        state.merge_foreground_ratio = 1/2
    elif greeting_words < 70:
        state.merge_foreground_ratio = 1/3
    else:
        state.merge_foreground_ratio = 1/3
        state.font_size = 60
    state.text_ratio = 1 - state.merge_foreground_ratio

    state.merge_foreground_ratio = 1 / 2 if state.aspect_ratio == 16 / 9 else state.merge_foreground_ratio

    # Perform merge
    output_path = f"static/merged/{uuid.uuid4().hex}.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merge_foreground_background(
        foreground_path=state.foreground_path,
        background_path=state.background_path,
        output_path=output_path,
        merge_position=state.merge_position,
        margin_ratio=state.merge_margin_ratio,
        aspect_ratio=state.aspect_ratio,
        foreground_ratio=state.merge_foreground_ratio,
    )
    state.merged_image_path = output_path

    return state
