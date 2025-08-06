import colorsys
import json
import logging
import math
import os
import random
from typing import Optional
from PIL import ImageDraw, ImageFont, Image, ImageDraw, ImageFont, ImageChops
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource
from colorthief import ColorThief

logger = logging.getLogger(__name__)

def get_dominant_color(image_path: str, quality=100) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    color_thief = ColorThief(image_path)
    dominant_color = color_thief.get_color(quality=quality)
    return '#{:02x}{:02x}{:02x}'.format(*dominant_color)

def merge_foreground_background_with_blending(
    foreground_path: str,
    background_path: str,
    output_path: str,
    merge_position: str = 'top',
    aspect_ratio: float = 3/4,
    foreground_ratio: float = 1/2,
    blend_ratio: float = 0.4,
    logo_path: str = "static/images/Logo-MISA.webp",
    logo_scale: float = 0.03,
) -> dict:
    """
    Merge a foreground image onto a background image with blending effects.
    
    Args:
        foreground_path (str): Path to the foreground image.
        background_path (str): Path to the background image.
        output_path (str): Path to save the merged image.
        merge_position (str): Position to place the foreground image ('top', 'bottom', 'left', 'right').
        margin_ratio (float): Margin ratio relative to the smaller dimension of the background.
        aspect_ratio (float): Aspect ratio of the final image (width/height).
        foreground_ratio (float): Ratio of the foreground image size relative to the background.
        blend_ratio (float): Ratio for blending the foreground with the background.
        logo_path (str): Path to the logo image to be added.
        logo_scale (float): Scale factor for the logo relative to the final image size.
    Returns:
        dict: Information about the merged image including paths and parameters.
    """
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background file not found: {background_path}")
    if not os.path.exists(foreground_path):
        raise FileNotFoundError(f"Foreground file not found: {foreground_path}")

    standard_height = 1600
    standard_width = int(standard_height * aspect_ratio)

    # Load and crop background
    bg = Image.open(background_path).convert('RGB')
    bg_w, bg_h = bg.size
    if bg_w / bg_h > aspect_ratio:
        new_w = int(bg_h * aspect_ratio)
        left = (bg_w - new_w) // 2
        bg = bg.crop((left, 0, left + new_w, bg_h))
    else:
        new_h = int(bg_w / aspect_ratio)
        top = (bg_h - new_h) // 2
        bg = bg.crop((0, top, bg_w, top + new_h))
    bg = bg.resize((standard_width, standard_height), Image.LANCZOS)

    # Load foreground
    fg = Image.open(foreground_path).convert('RGBA')
    fg_aspect = fg.width / fg.height

    if merge_position in ['top', 'bottom']:
        fg_width = standard_width
        fg_height = int(fg_width / fg_aspect)
        fg = fg.resize((fg_width, fg_height), Image.LANCZOS)
        fg_x = 0
        fg_y = 0 if merge_position == 'top' else standard_height - fg_height

        gradient = Image.new('L', (1, fg_height), color=0x00)
        blend_len = int(fg_height * blend_ratio)
        if fg_height <= standard_height * 2/3:
            if merge_position == 'top':
                # Blend only at the bottom edge
                blend_start = fg_height - blend_len
                for y in range(fg_height):
                    if y < blend_start:
                        alpha = 255
                    else:
                        alpha = int(255 * (fg_height - y) / blend_len)
                    gradient.putpixel((0, y), alpha)
                logger.info("Blending at bottom edge")
            else:  # 'bottom'
                # Blend only at the top edge
                for y in range(fg_height):
                    if y < blend_len:
                        alpha = int(255 * y / blend_len)
                    else:
                        alpha = 255
                    gradient.putpixel((0, y), alpha)
        else:
            if merge_position == 'bottom':
                blend_start = int(fg_height * (1 - foreground_ratio))
                for y in range(fg_height):
                    if y < blend_start:
                        alpha = 0
                    elif y < blend_start + blend_len:
                        alpha = int(255 * (y - blend_start) / blend_len)
                    else:
                        alpha = 255
                    gradient.putpixel((0, y), alpha)

            else:  # 'top'
                blend_start = int(fg_height * foreground_ratio)
                for y in range(fg_height):
                    if y > blend_start:
                        alpha = 0
                    elif y > blend_start - blend_len:
                        alpha = int(255 * (blend_start - y) / blend_len)
                    else:
                        alpha = 255
                    gradient.putpixel((0, y), alpha)

        alpha_mask = gradient.resize((fg_width, fg_height))

    elif merge_position in ['left', 'right']:
        fg_height = standard_height
        fg_width = int(fg_aspect * fg_height)
        fg = fg.resize((fg_width, fg_height), Image.LANCZOS)
        fg_y = 0
        fg_x = 0 if merge_position == 'left' else standard_width - fg_width

        gradient = Image.new('L', (fg_width, 1), color=0x00)
        blend_len = int(fg_width * blend_ratio)

        if fg_width <= standard_width * 2/3:
            if merge_position == 'left':
                # Blend only at the right edge
                blend_start = fg_width - blend_len
                for x in range(fg_width):
                    if x < blend_start:
                        alpha = 255
                    else:
                        alpha = int(255 * (fg_width - x) / blend_len)
                    gradient.putpixel((x, 0), alpha)
            else:  # 'right'
                # Blend only at the left edge
                for x in range(fg_width):
                    if x < blend_len:
                        alpha = int(255 * x / blend_len)
                    else:
                        alpha = 255
                    gradient.putpixel((x, 0), alpha)
                logger.info("Blending at right edge")
        else:
            if merge_position == 'right':
                blend_start = int(fg_width * (1 - foreground_ratio))
                for x in range(fg_width):
                    if x < blend_start:
                        alpha = 0
                    elif x < blend_start + blend_len:
                        alpha = int(255 * (x - blend_start) / blend_len)
                    else:
                        alpha = 255
                    gradient.putpixel((x, 0), alpha)

            else:  # 'left'
                blend_start = int(fg_width * foreground_ratio)
                for x in range(fg_width):
                    if x > blend_start:
                        alpha = 0
                    elif x > blend_start - blend_len:
                        alpha = int(255 * (blend_start - x) / blend_len)
                    else:
                        alpha = 255
                    gradient.putpixel((x, 0), alpha)

        alpha_mask = gradient.resize((fg_width, fg_height))

    else:
        raise ValueError("merge_position must be one of 'top', 'bottom', 'left', 'right'")

    # Apply alpha mask
    r, g, b, a = fg.split()
    a = ImageChops.multiply(a, alpha_mask)
    fg = Image.merge('RGBA', (r, g, b, a))

    # Paste onto background
    result = bg.copy()
    result.paste(fg, (fg_x, fg_y), fg)

    # Add logo if exists
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_h = int(standard_height * logo_scale)
        logo_ratio = logo.width / logo.height
        logo_w = int(logo_h * logo_ratio)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

        logo_margin = int(standard_height * 0.02)
        logo_x = standard_width - logo_w - logo_margin
        logo_y = standard_height - logo_h - logo_margin
        result.paste(logo, (logo_x, logo_y), logo)
        logo.close()

    result.save(output_path)
    result.close()
    bg.close()
    fg.close()

    return {
        "foreground_path": foreground_path,
        "background_path": background_path,
        "merged_image_path": output_path,
        "aspect_ratio": aspect_ratio,
        "merge_position": merge_position,
        "merge_foreground_ratio": foreground_ratio,
        "blend_ratio": blend_ratio,
    }


def merge_foreground_background(
    foreground_path: str,
    background_path: str,
    output_path: str,
    merge_position: str = 'top',
    margin_ratio: float = 0.05,
    aspect_ratio: float = 3/4,
    foreground_ratio: float = 1/2,
    logo_path: str = "static/images/Logo-MISA.webp",
    logo_scale: float = 0.03,
) -> dict:
    """
    Merge a foreground image onto a background image with specified position.
    
    Args:
        foreground_path (str): Path to the foreground image.
        background_path (str): Path to the background image.
        output_path (str): Path to save the merged image.
        merge_position (str): Position to place the foreground image ('top', 'bottom', 'left', 'right').
        margin_ratio (float): Margin ratio relative to the smaller dimension of the background.
        aspect_ratio (float): Aspect ratio of the final image (width/height).
        foreground_ratio (float): Ratio of the foreground image size relative to the background.
        logo_path (str): Path to the logo image to be added.
        logo_scale (float): Scale factor for the logo relative to the final image size.
    Returns:
        dict: Information about the merged image including paths and parameters.
    """
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background file not found: {background_path}")
    if not os.path.exists(foreground_path):
        raise FileNotFoundError(f"Foreground file not found: {foreground_path}")
    bg = Image.open(background_path).convert('RGB')
    fg = Image.open(foreground_path).convert('RGBA')

    # Standard size
    standard_height = 1600
    standard_width = int(standard_height * aspect_ratio)
    
    # Crop background to target aspect ratio
    target_ratio = aspect_ratio
    bg_w, bg_h = bg.size
    if bg_w / bg_h > target_ratio:
        # Too wide, crop width
        new_w = int(bg_h * target_ratio)
        left = (bg_w - new_w) // 2
        bg = bg.crop((left, 0, left + new_w, bg_h))
    else:
        # Too tall, crop height
        new_h = int(bg_w / target_ratio)
        top = (bg_h - new_h) // 2
        bg = bg.crop((0, top, bg_w, top + new_h))
    
    # Resize background to standard size early
    bg = bg.resize((standard_width, standard_height), Image.LANCZOS)
    bg_w, bg_h = standard_width, standard_height

    margin = int(min(bg_w, bg_h) * margin_ratio)
    # Ensure foreground_ratio does not exceed 1
    if foreground_ratio > 1:
        foreground_ratio = 1.0
    fg_w, fg_h = fg.size
    fg_ratio = fg_w / fg_h

    # Always allow 4 positions: top, bottom, left, right
    if merge_position in ['top', 'bottom']:
        fg_max_h = int(bg_h * foreground_ratio) - margin
        fg_max_w = bg_w - 2 * margin
        # Fit foreground inside fg_max_w x fg_max_h
        if fg_max_w / fg_max_h > fg_ratio:
            new_fg_h = fg_max_h
            new_fg_w = int(fg_ratio * new_fg_h)
        else:
            new_fg_w = fg_max_w
            new_fg_h = int(new_fg_w / fg_ratio)
        fg = fg.resize((new_fg_w, new_fg_h), Image.LANCZOS)
        x = margin + (fg_max_w - new_fg_w) // 2
        if merge_position == 'top':
            y = margin
        else:
            y = bg_h - new_fg_h - margin
    elif merge_position in ['left', 'right']:
        fg_max_w = int(bg_w * foreground_ratio) - margin
        fg_max_h = bg_h - 2 * margin
        if fg_max_w / fg_max_h > fg_ratio:
            new_fg_h = fg_max_h
            new_fg_w = int(fg_ratio * new_fg_h)
        else:
            new_fg_w = fg_max_w
            new_fg_h = int(new_fg_w / fg_ratio)
        fg = fg.resize((new_fg_w, new_fg_h), Image.LANCZOS)
        y = margin + (fg_max_h - new_fg_h) // 2
        if merge_position == 'left':
            x = margin
        else:
            x = bg_w - new_fg_w - margin
    else:
        raise ValueError("position must be one of 'top', 'bottom', 'left', 'right'")

    result = bg.copy()
    result.paste(fg, (x, y), fg)

    # Add logo if exists
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_h = int(standard_height * logo_scale)
        logo_ratio = logo.width / logo.height
        logo_w = int(logo_h * logo_ratio)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

        logo_margin = int(standard_height * 0.02)
        logo_x = standard_width - logo_w - logo_margin
        logo_y = standard_height - logo_h - logo_margin
        result.paste(logo, (logo_x, logo_y), logo)
        logo.close()

    if result.mode == "RGBA":
        result = result.convert("RGB")

    result.save(output_path)

    bg.close()
    fg.close()
    result.close()
    
    return {
        "foreground_path": foreground_path,
        "background_path": background_path,
        "merged_image_path": output_path,
        "aspect_ratio": aspect_ratio,
        "merge_position": merge_position,
        "merge_margin_ratio": margin_ratio,
        "merge_foreground_ratio": foreground_ratio,
    }

def add_text_to_image(
    image_path: str,
    text: str,
    output_path: str,
    font_path: Optional[str] = None,
    font_color: str = '#000000',
    font_size: Optional[int] = None,
    title: Optional[str] = None,
    title_font_path: Optional[str] = None,
    title_font_size: int = 140,
    text_position: str = 'bottom',
    margin_ratio: float = 0.05,
    text_ratio: float = 1/2,
) -> dict:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    img = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    W, H = img.size
    margin = int(min(W, H) * margin_ratio)

    if text_ratio > 1:
        text_ratio = 1.0
    if text_position in ['top', 'bottom']:
        text_area_h = int(H * text_ratio) - margin
        text_area_w = W - 2 * margin
    elif text_position in ['left', 'right']:
        text_area_w = int(W * text_ratio) - margin
        text_area_h = H - 2 * margin
    else:
        raise ValueError("position must be one of 'top', 'bottom', 'left', 'right'")

    # Title
    if title:
        if title_font_size is None:
            title_font_size = text_area_h // 4
        if title_font_path:
            title_font = ImageFont.truetype(title_font_path, title_font_size)
        else:
            title_font = ImageFont.load_default()
        wrapped_title = _get_wrapped(title, title_font, text_area_w + 10)
        title_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font)
        title_w, title_h = title_bbox[2] - title_bbox[0], title_bbox[3] - title_bbox[1]
    else:
        title_h = 0
        title_w = 0
        wrapped_title = ''
        title_font = None

    # Text
    if font_size is None:
        cur_font_size = text_area_h // 3
    else:
        cur_font_size = font_size
    if font_path:
        font = ImageFont.truetype(font_path, cur_font_size)
    else:
        font = ImageFont.load_default()

    while True:
        wrapped_text = _get_wrapped(text, font, text_area_w)
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        total_h = title_h + text_h
        if (text_w <= text_area_w and total_h <= text_area_h) or cur_font_size <= 10:
            break
        cur_font_size -= 2
        if font_path:
            font = ImageFont.truetype(font_path, cur_font_size)
        else:
            font = ImageFont.load_default()

    # Position
    if text_position == 'top':
        base_x = margin
        base_y = margin + (text_area_h - (title_h + text_h)) // 2
    elif text_position == 'bottom':
        base_x = margin
        base_y = H - text_area_h - margin + (text_area_h - (title_h + text_h)) // 2
    elif text_position == 'left':
        base_x = margin
        base_y = margin + (text_area_h - (title_h + text_h)) // 2
    elif text_position == 'right':
        base_x = W - text_area_w - margin
        base_y = margin + (text_area_h - (title_h + text_h)) // 2

    # Calculate centered positions for title and text separately
    title_x = base_x + (text_area_w - title_w) // 2 if title else base_x
    text_x = base_x + (text_area_w - text_w) // 2

    with Pilmoji(img, source=GoogleEmojiSource()) as pilmoji:
        if title:
            pilmoji.text((title_x, base_y), wrapped_title, font=title_font, fill=font_color, align='center')
            text_y = base_y + title_h + 70
        else:
            text_y = base_y
        pilmoji.text((text_x, text_y), wrapped_text, font=font, fill=font_color, align='center', spacing=12)

    img.save(output_path)
    return {
        "image_path": image_path,
        "image_with_text_path": output_path,
        "text": text,
        "title": title,
        "text_position": text_position,
        "margin_ratio": margin_ratio,
        "text_ratio": text_ratio,
        "font_path": font_path,
        "font_color": font_color,
        "font_size": cur_font_size,
        "title_font_path": title_font_path,
        "title_font_size": title_font_size,
    }

def _get_wrapped(text, font, max_width):
    """
    Wrap text to fit within a given width using a given font.
    """
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            test_line = line + (' ' if line else '') + word
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w > max_width and line:
                lines.append(line)
                line = word
            else:
                line = test_line
        lines.append(line)
    return '\n'.join(lines)

def get_templates_by_type(card_type: str, aspect_ratio: float = 3/4, json_path: str = 'static/images/template_metadata.json') -> list:
    """
    Get a list of image info dictionaries by type from metadata file.
    Args:
        card_type (str): The type name (e.g., 'birthday')
        aspect_ratio (float): Aspect ratio of the templates to filter by.
        json_path (str): Path to the JSON file containing template metadata.
    Returns:
        List[dict]: A list of image info dictionaries matching the type
    """
    if not os.path.exists(json_path):
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return []
    return [item for item in data if item.get('card_type') == card_type and item.get('aspect_ratio') == aspect_ratio]


def get_random_template_by_type(card_type: str, aspect_ratio: float = 3/4) -> Optional[dict]:
    """
    Get a random template image info dictionary by type from the template_card_info.json file.
    Args:
        card_type (str): The type name (e.g., 'birthday')
        aspect_ratio (float): Aspect ratio of the templates to filter by.
    Returns:
        dict: A random image info dictionary matching the type, or None if not found
    """
    templates = get_templates_by_type(card_type, aspect_ratio)
    if not templates:
        return None
    return random.choice(templates)

def get_random_font(fonts_dir: str = "static/fonts/text_fonts") -> str:
    """
    Randomly select a font file from the specified directory.

    Args:
        fonts_dir (str): The directory path to search for font files.

    Returns:
        str: The file path to the randomly selected font file.
    """
    files = [f for f in os.listdir(fonts_dir) if f.endswith(".ttf") or f.endswith(".otf")]
    if not files:
        raise FileNotFoundError(f"No font files found in {fonts_dir}")
    return os.path.join(fonts_dir, random.choice(files))

def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color (str): Hex color string (e.g., '#ff0000' or 'ff0000')
    
    Returns:
        tuple: RGB values as (r, g, b)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def color_distance_hsv(hsv1: tuple, hsv2: tuple) -> float:
    """Calculate the distance between two colors in HSV space.
    Args:
        hsv1 (tuple): First color in HSV format (hue, saturation, value).
        hsv2 (tuple): Second color in HSV format (hue, saturation, value).
    Returns:
        float: The distance between the two colors.
    """
    h1, s1, v1 = hsv1
    h2, s2, v2 = hsv2
    h1_rad = h1 * 2 * math.pi
    h2_rad = h2 * 2 * math.pi
    distance = math.sqrt(
        (v1 - v2) ** 2 +
        (s1 * math.cos(h1_rad) - s2 * math.cos(h2_rad)) ** 2 +
        (s1 * math.sin(h1_rad) - s2 * math.sin(h2_rad)) ** 2
    )
    return distance

def get_best_matching_background(target_color: str, json_path: str = 'static/images/background_metadata.json') -> Optional[dict]:
    """
    Find the best matching background color from the metadata file based on the target color.
    Args:
        target_color (str): The target color in hex format (e.g., '#ff0000').
        json_path (str): Path to the JSON file containing background metadata.
    Returns:
        Optional[dict]: The background metadata dictionary with the closest color match, or None if not found.
    """
    if not os.path.exists(json_path):
        logger.warning(f"Background metadata file not found: {json_path}")
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading background metadata: {e}")
        return None
    
    if not data:
        logger.warning("No background data found in metadata file")
        return None
    
    target_rgb = hex_to_rgb(target_color)
    target_hsv = colorsys.rgb_to_hsv(target_rgb[0] / 255.0, target_rgb[1] / 255.0, target_rgb[2] / 255.0)
    
    best_match = None
    min_distance = float('inf')
    
    for background in data:
        if 'color' not in background:
            continue
        
        try:
            bg_rgb = hex_to_rgb(background['color'])
            bg_hsv = colorsys.rgb_to_hsv(bg_rgb[0] / 255.0, bg_rgb[1] / 255.0, bg_rgb[2] / 255.0)
            distance = color_distance_hsv(target_hsv, bg_hsv)
            
            if distance < min_distance:
                min_distance = distance
                best_match = background
        except Exception as e:
            logger.warning(f"Error processing background color {background.get('color', 'unknown')}: {e}")
            continue
    
    if best_match:
        logger.info(f"Found best matching background: {best_match['background_path']} with color {best_match['color']} (distance: {min_distance:.2f})")
    else:
        logger.warning("No matching background found")
    
    return best_match