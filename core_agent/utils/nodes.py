import os
import logging
import uuid
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langgraph.prebuilt import ToolNode
from .tools import merge_foreground_background, add_text_to_image, get_random_font, get_dominant_color
from .tools import tools
from .prompt import system_prompt, user_prompt_template
from .state import AgentState

load_dotenv()
logger = logging.getLogger(__name__)

def _get_model(model_name: str = "misa-qwen3-235b") -> Runnable:
    try:
        llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model_name,
            temperature=0.7,
            default_headers={"App-Code": "fresher"},
            extra_body={
                "service": "test_agent_app",
                "chat_template_kwargs": {"enable_thinking": False}
            }
        )
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        return None
    return llm


class ResponseLLM(BaseModel):
    greeting_text: str = Field(description="Lời chúc tiếng Việt")
    font_color: str = Field(description="Mã màu hex cho chữ")
    merge_foreground_ratio: float = Field(description="Tỉ lệ foreground")
    text_ratio: float = Field(description="Tỉ lệ vùng text")
    merge_position: str = Field(description="Vị trí foreground")
    font_size: int = Field(description="Cỡ chữ")

def input_node(input_data: AgentState) -> AgentState:
    state = AgentState(**input_data.model_dump())
    return state

def llm_node(state: AgentState) -> AgentState:
    llm_with_tools = _get_model()
    prompt = user_prompt_template.format(**state.model_dump())
    messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content=prompt)]
    parsed: ResponseLLM = llm_with_tools.with_structured_output(ResponseLLM).invoke(messages)
    state.messages.append(AIMessage(content=parsed.model_dump_json()))
    state.greeting_text = parsed.greeting_text
    state.font_color = parsed.font_color
    state.merge_foreground_ratio = parsed.merge_foreground_ratio
    state.text_ratio = parsed.text_ratio
    state.merge_position = parsed.merge_position
    state.font_size = parsed.font_size
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

def merge_node(state: AgentState) -> AgentState:
    """Merge foreground and background with dynamic layout based on greeting length."""
    # Default ratios
    long_text_threshold = 40  # words
    default_fg_ratio = 2/3
    long_text_fg_ratio = 1/3

    greeting_words = len(state.greeting_text.split())
    fg_ratio = long_text_fg_ratio if greeting_words > long_text_threshold else default_fg_ratio
    text_ratio = 1 - fg_ratio

    output_path = f"static/merged/{uuid.uuid4().hex}.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    merge_position = state.merge_position
    margin_ratio = state.merge_margin_ratio
    aspect_ratio = state.aspect_ratio

    merge_foreground_background(
        foreground_path=state.foreground_path,
        background_path=state.background_path,
        output_path=output_path,
        merge_position=merge_position,
        margin_ratio=margin_ratio,
        aspect_ratio=aspect_ratio,
        foreground_ratio=fg_ratio,
    )

    state.merged_image_path = output_path
    state.merge_foreground_ratio = fg_ratio
    state.text_ratio = text_ratio
    return state


tool_node = ToolNode(tools)