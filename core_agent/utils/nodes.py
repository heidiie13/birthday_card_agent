import os
import logging
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
    state = AgentState(
        messages=[],
        full_name=input_data.get("full_name"),
        gender=input_data.get("gender"),
        birthday=input_data.get("birthday"),
        recipient=input_data.get("recipient"),
        style=input_data.get("style"),
        merged_image_path=input_data.get("merged_image_path"),
        background_path=input_data.get("background_path"),
        foreground_path=input_data.get("foreground_path"),
    )
    return state

class TextAndColor(BaseModel):
    font_color: str = Field(description="Hex code of the font color")
    greeting_text: str = Field(description="The greeting text")
    
def llm_suggest_text_and_color(state: AgentState) -> AgentState:
    llm_with_tools = _get_model()
    if llm_with_tools is None:
        # Fallback nếu LLM không khả dụng
        state["font_color"] = "#000000"
        state["greeting_text"] = f"Chúc mừng sinh nhật {state['full_name']}!"
        return state
    prompt = user_prompt_template.format(
        full_name=state["full_name"],
        gender=state["gender"],
        birthday=state["birthday"],
        recipient=state["recipient"],
        style=state["style"],
        background_path=state["background_path"],
        foreground_path=state["foreground_path"],
        merged_image_path=state["merged_image_path"],
    )
    
    messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content=prompt)]
    parsed: TextAndColor = llm_with_tools.with_structured_output(TextAndColor).invoke(messages)
    
    state["messages"].append(AIMessage(content=parsed.model_dump_json()))
    state["font_color"] = parsed.font_color
    state["greeting_text"] = parsed.greeting_text
    
    return state

def merge_foreground_background_node(state: AgentState) -> AgentState:
    fg_path = state["foreground_path"]
    bg_path = state["background_path"]
    fg_name = os.path.splitext(os.path.basename(fg_path))[0]
    bg_name = os.path.splitext(os.path.basename(bg_path))[0]
    output_path = f"static/merged/{bg_name}__{fg_name}_merged.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merge_foreground_background(
        foreground_path=fg_path,
        background_path=bg_path,
        output_path=output_path
    )
    state["merged_image_path"] = output_path
    return state

def add_text_node(state: AgentState) -> AgentState:
    image_path = state["merged_image_path"]
    img_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = f"static/merged/{img_name}_with_text.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    font_path = get_random_font()
    
    print(state.get("greeting_text"))
    add_text_to_image(
        image_path=image_path,
        output_path=output_path,
        text=state.get("greeting_text", ""),
        font_color=state["font_color"],
        font_path=font_path
    )
    state["merged_image_path"] = output_path
    state["font_path"] = font_path
    return state

def dominant_color_node(state: AgentState) -> AgentState:
    bg_path = state["background_path"]
    color = get_dominant_color(bg_path)
    state["dominant_color"] = color
    return state

def feedback_node(state: AgentState) -> AgentState:
    llm_with_tools = _get_model()
    if llm_with_tools is None:
        # Nếu không có LLM, bỏ qua xử lý feedback và trả về state như cũ
        return state
    feedback_content = state.get("feedback")
    if feedback_content is None:
        feedback_content = ""
    user_msg = HumanMessage(content=feedback_content)
    messages = state["messages"] + [user_msg]
    response = llm_with_tools.invoke(messages)
    state["messages"].append(user_msg)
    state["messages"].append(response)
    return state

tool_node = ToolNode(tools)