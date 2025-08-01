from PIL import ImageDraw, ImageFont, Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource
from collections import Counter
from typing import Optional
import os
import random
import io

def cleanup_merged_folder(merged_dir: str, max_files: int = 10):
    """
    Giữ lại tối đa max_files file gần nhất trong folder merged.
    Xóa những file cũ nhất nếu vượt quá giới hạn.
    
    Args:
        merged_dir (str): Đường dẫn đến folder merged
        max_files (int): Số file tối đa giữ lại (default: 10)
    """
    if not os.path.exists(merged_dir):
        return
    
    # Lấy danh sách tất cả file trong folder
    files = []
    for filename in os.listdir(merged_dir):
        filepath = os.path.join(merged_dir, filename)
        if os.path.isfile(filepath):
            # Lấy thời gian tạo file
            mtime = os.path.getmtime(filepath)
            files.append((mtime, filepath))
    
    # Sắp xếp theo thời gian (mới nhất trước)
    files.sort(reverse=True)
    
    # Xóa file cũ nếu vượt quá giới hạn
    if len(files) > max_files:
        files_to_delete = files[max_files:]
        for _, filepath in files_to_delete:
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Lỗi khi xóa file {filepath}: {e}")

def get_dominant_color(image_path: str, resize=50) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    img = Image.open(image_path).convert("RGB")
    img = img.resize((resize, resize))  # Resize nhỏ để giảm tính toán
    pixels = list(img.getdata())
    most_common = Counter(pixels).most_common(1)[0][0]  # pixel phổ biến nhất
    return '#{:02x}{:02x}{:02x}'.format(*most_common)

def merge_foreground_background(
    foreground_path: str,
    background_path: str,
    output_path: str,
    merge_position: str = 'top',
    margin_ratio: float = 0,
    aspect_ratio: float = 3/4,
    foreground_ratio: float = 1/2
) -> dict:
    """
    Merge a foreground image onto a background image with foreground fixed at TOP position.
    The background is cropped to the given aspect ratio (3:4).
    Foreground occupies foreground_ratio of the height at the top.
    Text area will be at the bottom.

    Args:
        foreground_path (str): Path to foreground image.
        background_path (str): Path to background image.
        output_path (str): Path to save the merged image.
        merge_position (str): Fixed to 'top' (kept for compatibility).
        margin_ratio (float): Margin as a fraction of the smallest image dimension (default 0.05).
        aspect_ratio (float): Aspect ratio (width/height) for cropping background, fixed to 3/4.
        foreground_ratio (float): Fraction of background occupied by foreground height (default 1/2).

    Returns:
        dict: Details of the merged image including paths and parameters.
    """
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background file not found: {background_path}")
    if not os.path.exists(foreground_path):
        raise FileNotFoundError(f"Foreground file not found: {foreground_path}")
    bg = Image.open(background_path).convert('RGB')
    fg = Image.open(foreground_path).convert('RGBA')

    # Crop background to target aspect ratio (3:4)
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

    # Fixed position: foreground at TOP
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
    y = margin  # Always TOP position
    
    # Paste foreground onto background
    result = bg.copy()
    result.paste(fg, (x, y), fg)
    
    # Resize to standard dimensions
    standard_height = 1600  # Standard height for resizing
    standard_width = int(standard_height * aspect_ratio)
    result = result.resize((standard_width, standard_height), Image.LANCZOS)
    
    # Convert to RGB if needed
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
    Add text to the bottom area of the image (not covered by foreground), with margin and adjustable area ratio.
    Text area is fixed at BOTTOM position where foreground is at TOP.

    Args:
        image_path (str): Path to the merged image.
        text (str): Text to add.
        output_path (str): Path to save the image with text.
        font_path (str): Path to .ttf font file (optional).
        font_color (str): Text color in hex (default black).
        font_size (int): Font size (optional, auto-fit if None).
        title (str): Title text (optional).
        title_font_path (str): Path to .ttf font file for title (optional).
        title_font_size (int): Title font size (optional, auto-fit if None).
        text_position (str): Fixed to 'bottom' (kept for compatibility).
        margin_ratio (float): Margin as a fraction of image size (default 0.05).
        text_ratio (float): Fraction of background occupied by text height (default 1/2).

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
    
    # Fixed position: text at BOTTOM
    text_area_h = int(H * text_ratio) - margin
    text_area_w = W - 2 * margin

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

    # Position: always BOTTOM
    max_w = max(text_w, title_w if title else 0)
    x = margin + (text_area_w - max_w) // 2
    y = H - text_area_h - margin + (text_area_h - (title_h + text_h)) // 2

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

def get_random_background() -> str:
    """
    Randomly select a background image from static/images/backgrounds.

    Returns:
        str: The file path to the randomly selected background image.
    """
    backgrounds_dir = os.path.join('static', 'images', 'backgrounds')
    files = [f for f in os.listdir(backgrounds_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not files:
        raise FileNotFoundError('No background images found in static/images/backgrounds/')
    selected = random.choice(files)
    return os.path.join(backgrounds_dir, selected)


def get_random_foreground() -> str:
    """
    Randomly select a foreground image from static/images/foregrounds.

    Returns:
        str: The file path to the randomly selected foreground image.
    """
    foregrounds_dir = os.path.join('static', 'images', 'foregrounds')
    files = [f for f in os.listdir(foregrounds_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not files:
        raise FileNotFoundError('No foreground images found in static/images/foregrounds/')
    selected = random.choice(files)
    return os.path.join(foregrounds_dir, selected)


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


def get_current_time() -> str:
    """
    Get current date and time in Vietnamese format for LLM to calculate age.
    
    Returns:
        str: Current date in DD/MM/YYYY format
    """
    from datetime import datetime
    return datetime.now().strftime("%d/%m/%Y")


from PIL import Image

def create_alpha_mask_with_gradient_edges(fg_size, gradient_region, gradient_smoothness,
                                         gradient_top=False, gradient_bottom=True,
                                         gradient_left=False, gradient_right=False):
    """
    Tạo mask với gradient edges thay vì blur, giữ nguyên phần giữa
    
    Args:
        fg_size: (width, height) của ảnh
        gradient_region: Kích thước vùng gradient ở mỗi cạnh (pixels)
        gradient_smoothness: Độ mềm mại của gradient (1.0 = linear, >1.0 = smooth curve)
        gradient_top, gradient_bottom, gradient_left, gradient_right: Có áp dụng gradient cho từng cạnh không
    """
    width, height = fg_size
    alpha = Image.new('L', (width, height), 255)  # Bắt đầu với mask hoàn toàn opaque
    data = alpha.load()
    
    for y in range(height):
        for x in range(width):
            # Tính khoảng cách đến từng cạnh cần gradient
            distances = []
            
            if gradient_top:
                distances.append(y)
            if gradient_bottom:
                distances.append(height - y - 1)
            if gradient_left:
                distances.append(x)
            if gradient_right:
                distances.append(width - x - 1)
            
            # Nếu không có cạnh nào được chọn, giữ nguyên opaque
            if not distances:
                data[x, y] = 255
                continue
                
            # Lấy khoảng cách ngắn nhất đến các cạnh được chọn
            min_distance = min(distances)
            
            # Áp dụng gradient từ 0 (mép) → 255 (giữa)
            if min_distance <= gradient_region:
                # Sử dụng công thức gradient có thể điều chỉnh độ mềm mại
                ratio = min_distance / gradient_region
                # Áp dụng curve để làm mềm gradient
                smooth_ratio = pow(ratio, 1.0 / gradient_smoothness)
                alpha_value = int(smooth_ratio * 255)
                data[x, y] = alpha_value
            else:
                data[x, y] = 255  # Opaque hoàn toàn ở giữa
    
    return alpha


def apply_gradient_mask_edges(input_path: str, output_path: str, gradient_region,
                             gradient_smoothness, gradient_top=True, gradient_bottom=True,
                             gradient_left=True, gradient_right=True) -> str:
    """
    Áp dụng gradient mask viền cho ảnh đã upload thay vì Gaussian blur.
    
    Args:
        input_path (str): Path to the input image
        output_path (str): Path to save the processed image
        gradient_region (int): Kích thước vùng gradient ở mỗi cạnh (pixels)
        gradient_smoothness (float): Độ mềm mại của gradient (1.0 = linear, >1.0 = smooth curve)
        gradient_top, gradient_bottom, gradient_left, gradient_right (bool): Có áp dụng gradient cho từng cạnh không
        
    Returns:
        str: Path to the processed image
    """
    
    try:
        # Load the input image
        img = Image.open(input_path).convert('RGBA')
        
        # Tạo alpha mask với gradient edges
        alpha_mask = create_alpha_mask_with_gradient_edges(
            img.size,
            gradient_region=gradient_region,
            gradient_smoothness=gradient_smoothness,
            gradient_top=gradient_top,
            gradient_bottom=gradient_bottom,
            gradient_left=gradient_left,
            gradient_right=gradient_right
        )
        
        # Áp dụng alpha mask lên ảnh
        img.putalpha(alpha_mask)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the processed image
        img.save(output_path, 'PNG')
        
        return output_path
        
    except Exception as e:
        # If any error occurs, fall back to copying the original
        import shutil
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy2(input_path, output_path)
        return output_path

def get_templates_by_type(card_type: str):
    """
    Get a list of image info dictionaries by type from the template_card_info.json file.
    Args:
        card_type (str): The type name (e.g., 'birthday')
    Returns:
        List[dict]: A list of image info dictionaries matching the type
    """
    import json
    json_path = 'static/images/template_card_info.json'
    if not os.path.exists(json_path):
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return []
    return [item for item in data if item.get('card_type') == card_type]

def get_random_template_by_type(card_type: str):
    """
    Get a random template image info dictionary by type from the template_card_info.json file.
    Args:
        card_type (str): The type name (e.g., 'birthday')
    Returns:
        dict: A random image info dictionary matching the type, or None if not found
    """
    templates = get_templates_by_type(card_type)
    if not templates:
        return None
    return random.choice(templates)

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