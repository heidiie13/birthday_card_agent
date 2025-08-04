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
from .tools import (merge_foreground_background,
                    merge_foreground_background_with_blending,
                    add_text_to_image, 
                    get_random_font,
                    get_dominant_color,
                    get_random_template_by_type
                    )

from .prompt import system_prompt, user_prompt_template, system_color_prompt, dominant_color_prompt_template
from .state import State

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
            extra_body={
                # ...
                "chat_template_kwargs": {
                    "enable_thinking": False  # Hoặc False để tắt
                }
            }
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

def dominant_color_node(state: State) -> State:
    """Extract dominant color from the background image."""
    bg_path = state.background_path
    if not bg_path:
        logger.warning("No background_path provided for dominant color extraction.")
        return state
    color = get_dominant_color(bg_path)
    state.dominant_color = color
    logger.info(f"Dominant color: {color}")
    return state

def llm_node(state: State) -> State:
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
        if not parsed:
            logger.error("Failed to parse JSON from LLM response.")
            logger.error(f"LLM response content: {response.content}")
            
        logger.info(f"Response from LLM: {parsed}")
        state.messages.append(AIMessage(content=response.content))
        state.title = parsed.get("title")
        state.greeting_text = parsed.get("greeting_text")
        state.card_type = parsed.get("card_type")
    except Exception as e:
        logger.error(f"Error creating messages: {e}")
        return state

    
    return state

def route_random_template(state: State) -> State:
    """Route to a random template based on card type."""
    if state.foreground_path and state.background_path:
        return "dominant_color"
    
    return "random_template"

def random_template_node(state: State) -> State:
    """Select a random template for the card."""
    template = get_random_template_by_type(state.card_type)
    if not template:
        logger.warning(f"No template found for card_type: {state.card_type}")
        return state
    state.foreground_path = template.get("foreground_path")
    state.background_path = template.get("background_path")
    state.merged_image_path = template.get("merged_image_path")

    logger.info(f"Foreground path: {state.foreground_path}")
    logger.info(f"Background path: {state.background_path}")
    logger.info(f"Merged image path: {state.merged_image_path}")
    return state
    
def font_color_node(state: State) -> State:
    """Select font color using LLM based on dominant_color and card_type."""
    llm = _get_model()
    user_prompt = dominant_color_prompt_template.format(**state.model_dump())
    sys_prompt = system_color_prompt.format()
    try:
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        parsed = extract_json(response.content)
        state.messages.append(AIMessage(content=response.content))
        state.font_color = parsed.get("font_color")
        logger.info(f"Response from LLM: {parsed}")
    except Exception as e:
        logger.error(f"Error in font_color_node: {e}")

    return state

def merge_node(state: State) -> State:
    """Process merging foreground and background images with updated state."""
    if not state.foreground_path or not state.background_path:
        logger.warning(f"Missing foreground or background for merge: {state.foreground_path}, {state.background_path}")
        return state

    position_map = {
        "left": "right",
        "right": "left",
        "top": "bottom",
        "bottom": "top"
    }
    

    greeting_words = len(state.greeting_text.split()) if state.greeting_text else 0

    # Set merge_foreground_ratio based on aspect ratio and greeting length
    if greeting_words < 40:
        state.merge_foreground_ratio = 1/2
    else:
        state.merge_foreground_ratio = 1/3

    state.text_ratio = 1 - state.merge_foreground_ratio + 0.05

    if state.aspect_ratio > 1:
        state.merge_position = "right"
        state.text_ratio = 1 - state.merge_foreground_ratio - 0.02
        state.title_font_size = 150
        
    state.text_position = position_map.get(state.merge_position)
    # Generate output path
    output_path = f"static/images/cards/{uuid.uuid4().hex}.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check if this is a user upload (no merged_image_path provided)
    if not state.merged_image_path:
        # User upload - use merge with blending
        logger.info("Using merge with blending for user upload")
        merge_foreground_background_with_blending(
            foreground_path=state.foreground_path,
            background_path=state.background_path,
            output_path=output_path,
            aspect_ratio=state.aspect_ratio,
            foreground_ratio=state.merge_foreground_ratio,
            merge_position=state.merge_position,
        )
    else:
        # Template selection - use normal merge
        logger.info("Using normal merge for template")
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

def add_text_node(state: State) -> State:
    image_path = state.merged_image_path
    state.card_path = image_path
    logger.info(f"Card generated at: {state.card_path}")

    font_path = get_random_font("static/fonts/text_fonts")
    title_font_path = get_random_font("static/fonts/title_fonts")

    logger.info(f"Font path: {font_path}")
    logger.info(f"Title font path: {title_font_path}")

    if state.merge_foreground_ratio < 1/2:
        state.font_size = 70

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