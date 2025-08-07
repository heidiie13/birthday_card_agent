import os
from typing import Optional
import logging
import json
import re
import uuid
from dotenv import load_dotenv
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .tools import (merge_foreground_background,
                    merge_foreground_background_with_blending,
                    add_text_to_image, 
                    get_random_font,
                    get_dominant_color,
                    get_random_template_by_type,
                    get_best_matching_background,
                    )

from .prompt import system_prompt, user_prompt_template, system_color_prompt, dominant_color_prompt_template, system_poem_prompt
from .state import State

load_dotenv()
logger = logging.getLogger(__name__)

@lru_cache(maxsize=4)
def _get_model(model: Optional[str] = None) -> Runnable:
    try:
        llm = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model if model else os.getenv("MODEL_NAME", "misa-qwen3-235b"),
            default_headers={"App-Code": "fresher"},
            temperature=0.5,
            # extra_body={
            #     "chat_template_kwargs": {
            #         "enable_thinking": False
            #     }
            # }
        )
        logger.info(f"Using model: {llm.model_name}")
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

def is_poem_request(greeting_instructions: str) -> bool:
    """Check if the user is requesting a poem (thơ lục bát)."""
    if not greeting_instructions:
        return False
    
    poem_keywords = [
        "thơ", "thơ lục bát", "lục bát", "câu thơ", "bài thơ", 
        "viết thơ", "làm thơ", "sáng tác thơ", "thơ việt nam"
    ]
    
    text_lower = greeting_instructions.lower()
    return any(keyword in text_lower for keyword in poem_keywords)

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

def upload_image_node(state: State) -> State:
    foreground_color = get_dominant_color(state.foreground_path, quality=50)
    best_background = get_best_matching_background(foreground_color)
    state.background_path = best_background.get("background_path")
    state.dominant_color = best_background.get("color")

    logger.info(f"Foreground color: {foreground_color}")
    logger.info(f"Selected background path: {state.background_path}")
    return state

def llm_node(state: State) -> State:
    llm = _get_model()
    user_prompt = user_prompt_template.format(**state.model_dump())
    
    # Check if user is requesting a poem
    is_poem = is_poem_request(state.greeting_text_instructions)
    
    try:
        if is_poem:
            # If poem is requested, use system_poem_prompt
            messages = [
                SystemMessage(content=system_poem_prompt),
                HumanMessage(content=user_prompt)
            ]
            logger.info("Using poem template for poem request")
        else:
            # Normal case - use only system_prompt
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            logger.info("Using standard system prompt")

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

    if greeting_words < 40:
        state.merge_foreground_ratio = 1/2
    else:
        state.merge_foreground_ratio = 1/3

    state.text_ratio = 1 - state.merge_foreground_ratio + 0.05
    is_poem = is_poem_request(state.greeting_text_instructions)
    state.font_size = 80 if not is_poem else 70

    if state.aspect_ratio > 1:
        state.merge_foreground_ratio = state.merge_foreground_ratio if not is_poem else 1/3
        state.merge_position = "right"
        state.text_ratio = 1 - state.merge_foreground_ratio - 0.02
        state.title_font_size = 130
        state.font_size = 100 if not is_poem else 80

    state.text_position = position_map.get(state.merge_position)
    output_path = f"static/images/cards/{uuid.uuid4().hex}.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not state.merged_image_path:
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

def route_random_template(state: State) -> State:
    """Route to appropriate processing based on the provided inputs."""
    if state.merged_image_path and state.background_path and state.foreground_path:
        return "dominant_color"
    if state.foreground_path and not state.background_path and not state.merged_image_path:
        return "upload_image"
    return "random_template"