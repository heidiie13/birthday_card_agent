import json
import os
from collections import Counter
import random
from typing import Optional
from PIL import ImageDraw, ImageFont, Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource

def get_dominant_color(image_path: str, resize=50) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    img = Image.open(image_path).convert("RGB")
    img = img.resize((resize, resize))
    pixels = list(img.getdata())
    most_common = Counter(pixels).most_common(1)[0][0]
    return '#{:02x}{:02x}{:02x}'.format(*most_common)

def merge_foreground_background(
    foreground_path: str,
    background_path: str,
    output_path: str,
    merge_position: str = 'top',
    margin_ratio: float = 0.05,
    aspect_ratio: float = 3/4,
    foreground_ratio: float = 1/2
) -> dict:
    """
    Merge a foreground image onto a background image with a specified aspect ratio (width/height, float) and adjustable foreground area.
    The background is cropped to the given aspect ratio. Foreground placement and size depend on the position:
    - 'top': foreground occupies foreground_ratio of the height at the top.
    - 'bottom': foreground occupies foreground_ratio of the height at the bottom.
    - 'left': foreground occupies foreground_ratio of the width at the left.
    - 'right': foreground occupies foreground_ratio of the width at the right.
    Margin is applied to avoid touching the edges.

    Args:
        foreground_path (str): Path to foreground image.
        background_path (str): Path to background image.
        output_path (str): Path to save the merged image.
        merge_position (str): One of 'top', 'bottom', 'left', 'right'.
        margin_ratio (float): Margin as a fraction of the smallest image dimension (default 0.05).
        aspect_ratio (float): Aspect ratio (width/height) for cropping background, e.g. 1.0 (1:1), 0.75 (3:4), 1.33 (4:3), 0.5625 (9:16), 1.77 (16:9). 1.33 (4:3).
        foreground_ratio (float): Fraction of background occupied by foreground in the chosen direction (default 1/2).

    Returns:
        dict: Details of the merged image including paths and parameters.
    """
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background file not found: {background_path}")
    if not os.path.exists(foreground_path):
        raise FileNotFoundError(f"Foreground file not found: {foreground_path}")
    bg = Image.open(background_path).convert('RGB')
    fg = Image.open(foreground_path).convert('RGBA')

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
    bg_w, bg_h = bg.size

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
    
    standard_height = 1600  # Standard height for resizing
    standard_width = int(standard_height * aspect_ratio)
    result = result.resize((standard_width, standard_height), Image.LANCZOS)
    
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
    """
    Add text to a specified area of the image (not covered by foreground), with margin and adjustable area ratio.
    Text area and position are always one of: 'top', 'bottom', 'left', 'right'.
    - 'top': text occupies text_ratio (default 1-foreground_ratio) of the height at the top.
    - 'bottom': text occupies text_ratio of the height at the bottom.
    - 'left': text occupies text_ratio (default 1-foreground_ratio) of the width at the left.
    - 'right': text occupies text_ratio of the width at the right.
    Margin is applied to avoid touching the edges.

    Args:
        image (Image.Image): The merged image (PIL Image).
        output_path (str): Path to save the image with text.
        text (str): Text to add.
        font_path (str): Path to .ttf font file (optional).
        font_color (str): Text color in hex (default black).
        font_size (int): Font size (optional, auto-fit if None).
        title (str): Title text (optional).
        title_font_path (str): Path to .ttf font file (optional).
        title_font_size (int): Title font size (optional, auto-fit if None).
        text_position (str): One of 'top', 'bottom', 'left', 'right'.
        margin_ratio (float): Margin as a fraction of image size (default 0.05).
        text_ratio (float): Fraction of background occupied by text in the chosen direction (default 1-foreground_ratio).

    Returns:
        dict: Details of the image with text including paths and parameters.
        
    """
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
        wrapped_title = _get_wrapped(title, title_font, text_area_w)
        title_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font)
        title_w, title_h = title_bbox[2] - title_bbox[0], title_bbox[3] - title_bbox[1]
    else:
        title_h = 0
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
    max_w = max(text_w, title_w if title else 0)
    if text_position == 'top':
        x = margin + (text_area_w - max_w) // 2
        y = margin + (text_area_h - (title_h + text_h)) // 2
    elif text_position == 'bottom':
        x = margin + (text_area_w - max_w) // 2
        y = H - text_area_h - margin + (text_area_h - (title_h + text_h)) // 2
    elif text_position == 'left':
        x = margin + (text_area_w - max_w) // 2
        y = margin + (text_area_h - (title_h + text_h)) // 2
    elif text_position == 'right':
        x = W - text_area_w - margin + (text_area_w - max_w) // 2
        y = margin + (text_area_h - (title_h + text_h)) // 2

    with Pilmoji(img, source=GoogleEmojiSource()) as pilmoji:
        if title:
            pilmoji.text((x, y), wrapped_title, font=title_font, fill=font_color, align='center')
            y += title_h + 70
        pilmoji.text((x, y), wrapped_text, font=font, fill=font_color, align='center', spacing=12)

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
        if not paragraph:
            lines.append('')
            continue
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

def get_templates_by_style(card_style: str):
    """
    Get a list of image info dictionaries by style from the template_card_info.json file.
    Args:
        card_style (str): The style name (e.g., 'birthday')
    Returns:
        List[dict]: A list of image info dictionaries matching the style
    """

    json_path = 'static/images/template_card_info.json'
    if not os.path.exists(json_path):
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return []
    return [item for item in data if item.get('card_style') == card_style]
    
def get_random_font() -> str:
    """
    Randomly select a font file from static/fonts.

    Returns:
        str: The file path to the randomly selected font file.
    """

    fonts_dir = os.path.join("static", "fonts")
    files = [f for f in os.listdir(fonts_dir) if f.endswith(".ttf") or f.endswith(".otf")]
    if not files:
        raise FileNotFoundError("No font files found in static/fonts/")
    return os.path.join(fonts_dir, random.choice(files))