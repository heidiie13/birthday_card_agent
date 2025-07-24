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

def input_node(input_data: dict) -> AgentState:
    state = AgentState(**input_data)
    return state


# Tách riêng hai schema cho hai nhiệm vụ
class GreetingTextOnly(BaseModel):
    greeting_text: str = Field(description="The greeting text")

class FontColorOnly(BaseModel):
    font_color: str = Field(description="Hex code of the font color")

def llm_suggest_greeting_text(state: AgentState) -> AgentState:
    """
    Chỉ sinh lại greeting_text, giữ nguyên font_color hiện tại.
    """
    llm_with_tools = _get_model()
    prompt = user_prompt_template.format(**state)
    messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content=prompt)]
    parsed: GreetingTextOnly = llm_with_tools.with_structured_output(GreetingTextOnly).invoke(messages)
    state["messages"].append(AIMessage(content=parsed.model_dump_json()))
    state["greeting_text"] = parsed.greeting_text
    return state

def llm_suggest_font_color(state: AgentState) -> AgentState:
    """
    Chỉ sinh lại font_color, giữ nguyên greeting_text hiện tại.
    """
    llm_with_tools = _get_model()
    prompt = user_prompt_template.format(**state)
    messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content=prompt)]
    parsed: FontColorOnly = llm_with_tools.with_structured_output(FontColorOnly).invoke(messages)
    state["messages"].append(AIMessage(content=parsed.model_dump_json()))
    state["font_color"] = parsed.font_color
    return state

def merge_foreground_background_node(state: AgentState) -> AgentState:
    fg_path = state["foreground_path"]
    bg_path = state["background_path"]
    output_path = state.get("merged_image_path")
    if not output_path:
        output_path = f"static/merged/{uuid.uuid4().hex}.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merge_foreground_background(
        foreground_path=fg_path,
        background_path=bg_path,
        output_path=output_path,
        merge_position=state.get("merge_position", "top"),
        margin_ratio=state.get("merge_margin_ratio", 0.05),
        aspect_ratio=state.get("merge_aspect_ratio", 3/4),
        foreground_ratio=state.get("merge_foreground_ratio", 2/3),
    )
    state["merged_image_path"] = output_path
    return state

def add_text_node(state: AgentState) -> AgentState:
    image_path = state["merged_image_path"]
    output_path = f"static/merged/{uuid.uuid4().hex}.png"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    font_path = state.get("font_path") or get_random_font()
    add_text_to_image(
        image_path=image_path,
        output_path=output_path,
        text=state.get("greeting_text", ""),
        font_color=state.get("font_color", "#000000"),
        font_path=font_path,
        font_size=state.get("font_size", 48),
        text_position=state.get("text_position", "bottom"),
        margin_ratio=state.get("text_margin_ratio", 0.05),
        text_ratio=state.get("text_ratio", 1/3),
    )
    state["merged_with_text_path"] = output_path
    state["font_path"] = font_path
    return state

def dominant_color_node(state: AgentState) -> AgentState:
    bg_path = state["background_path"]
    color = get_dominant_color(bg_path)
    state["dominant_color"] = color
    return state

def feedback_node(state: AgentState) -> AgentState:
    llm_with_tools = _get_model()
    
    feedback_content = state.get("feedback") or ""
    user_msg = HumanMessage(content=feedback_content)
    messages = state["messages"] + [user_msg]
    response = llm_with_tools.invoke(messages)
    state["messages"].append(user_msg)
    state["messages"].append(response)
    return state

tool_node = ToolNode(tools)