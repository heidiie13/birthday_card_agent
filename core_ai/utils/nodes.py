import json
import os
import logging
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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
            temperature=0.7,
            default_headers={"App-Code": "fresher"},
        )
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        return None
    return llm

def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            return None
    return None

def dominant_color_node(state: AgentState) -> AgentState:
    """Extract dominant color from the background image."""
    bg_path = state.background_path
    color = get_dominant_color(bg_path)
    state.dominant_color = color
    logger.info(f"Dominant color: {color}")
    
    return state

def llm_node(state: AgentState) -> AgentState:
    now = datetime.now().strftime("%d/%m/%Y")
    llm = _get_model()
    user_prompt = user_prompt_template.format(**state.model_dump())
    sys_prompt = system_prompt.format(current_time = now)

    try:
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        parsed = extract_json(response.content)

        logger.info(f"Response from LLM: {parsed}")
    except Exception as e:
        logger.error(f"Error creating messages: {e}")
        return state

    state.messages.append(AIMessage(content=response.content))
    state.greeting_text = parsed.get("greeting_text")
    state.font_color = parsed.get("font_color")
    state.title = parsed.get("title")
    
    return state

def merge_node(state: AgentState) -> AgentState:
    """Process merging foreground and background images with updated state."""
    # Set default values
    # state.font_size = 70
    # state.merge_margin_ratio = 0.05

    # Determine text position based on merge position
    position_map = {
        "left": "right",
        "right": "left",
        "top": "bottom",
        "bottom": "top"
    }
    state.text_position = position_map.get(state.merge_position)

    # greeting_words = len(state.greeting_text.split()) if state.greeting_text else 0

    # # Set merge_foreground_ratio based on aspect ratio and greeting length
    # if greeting_words < 30:
    #     state.merge_foreground_ratio = 2/3
    # elif greeting_words < 50:
    #     state.merge_foreground_ratio = 1/2
    # else:
    #     state.merge_foreground_ratio = 1/3
    #     state.font_size = 60

    state.text_ratio = 1 - state.merge_foreground_ratio

    # Perform merge
    output_path = f"static/images/cards/{uuid.uuid4().hex}.png"
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

def add_text_node(state: AgentState) -> AgentState:
    image_path = state.merged_image_path
    state.card_path = image_path
    logger.info(f"Card generated at: {state.card_path}")

    font_path = get_random_font()
    title_font_path = get_random_font()

    logger.info(f"Font path: {font_path}")
    try:
        add_text_to_image(
            image_path=image_path,
            output_path=state.card_path,
            text=state.greeting_text,
            title=state.title,
            title_font_path=title_font_path,
            title_font_size=state.title_font_size,
            font_color=state.font_color,
            font_path=font_path,
            font_size=state.font_size,
            text_position=state.text_position,
            margin_ratio=state.text_margin_ratio,
            text_ratio=state.text_ratio,
        )
    except Exception as e:
        logger.error(f"Error adding text to image: {e}")
        return state

    state.font_path = font_path
    return state