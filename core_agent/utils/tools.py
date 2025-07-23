from PIL import ImageDraw, ImageFont
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from sklearn.cluster import KMeans

def get_dominant_color(image_path: str, k: int = 5) -> str:
    """
    Get dominant color using KMeans clustering.

    Args:
        image_path (str): Path to image.
        k (int): Number of clusters.

    Returns:
        str: Dominant color in hex.
    """
    image = Image.open(image_path)
    image = image.convert('RGB')
    image = image.resize((100, 100))  # speedup
    arr = np.array(image).reshape(-1, 3)

    kmeans = KMeans(n_clusters=k, n_init='auto')
    kmeans.fit(arr)
    counts = np.bincount(kmeans.labels_)
    dominant = kmeans.cluster_centers_[counts.argmax()]
    dominant = dominant.astype(int)
    return '#{:02x}{:02x}{:02x}'.format(*dominant)

def merge_foreground_background(
    foreground_path: str,
    background_path: str,
    output_path: str,
    position: str = 'top',
    margin_ratio: float = 0.05,
    aspect_ratio: float = 4/3,
    foreground_ratio: float = 2/3
) -> str:
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
        position (str): One of 'top', 'bottom', 'left', 'right'.
        margin_ratio (float): Margin as a fraction of the smallest image dimension (default 0.05).
        aspect_ratio (float): Aspect ratio (width/height) for cropping background, e.g. 1.0 (1:1), 0.75 (3:4), 1.33 (4:3), 0.5625 (9:16), 1.77 (16:9). 1.33 (4:3).
        foreground_ratio (float): Fraction of background occupied by foreground in the chosen direction (default 2/3).

    Returns:
        str: The output file path of the merged image.
    """
    bg = Image.open(background_path).convert('RGBA')
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
    # Foreground occupies 2/3 theo hướng position, 1/3 còn lại cho text
    if position in ['top', 'bottom']:
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
        if position == 'top':
            y = margin
        else:
            y = bg_h - new_fg_h - margin
    elif position in ['left', 'right']:
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
        if position == 'left':
            x = margin
        else:
            x = bg_w - new_fg_w - margin
    else:
        raise ValueError("position must be one of 'top', 'bottom', 'left', 'right'")

    result = bg.copy()
    result.paste(fg, (x, y), fg)
    result.save(output_path)
    return output_path

def add_text_to_image(
    image_path: str,
    output_path: str,
    text: str,
    position: str = 'bottom',
    margin_ratio: float = 0.05,
    text_ratio: float = 1/3,
    font_path: str = None,
    font_color: str = '#000000',
    font_size: int = None
) -> str:
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
        text (str): Text to add.
        position (str): One of 'top', 'bottom', 'left', 'right'.
        margin_ratio (float): Margin as a fraction of image size (default 0.05).
        text_ratio (float): Fraction of background occupied by text in the chosen direction (default 1-foreground_ratio or 1/3).
        font_path (str): Path to .ttf font file (optional).
        font_color (str): Text color in hex (default black).
        font_size (int): Font size (optional, auto-fit if None).

    Returns:
        str: The output file path of the image with text added.
    """
    img = Image.open(image_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    W, H = img.size
    margin = int(min(W, H) * margin_ratio)
    # Always allow 4 positions: top, bottom, left, right
    if text_ratio is None:
        text_ratio = 1 - (2/3)  # default: 1/3
    if text_ratio > 1:
        text_ratio = 1.0
    if position in ['top', 'bottom']:
        text_area_h = int(H * text_ratio) - margin
        text_area_w = W - 2 * margin
    elif position in ['left', 'right']:
        text_area_w = int(W * text_ratio) - margin
        text_area_h = H - 2 * margin
    else:
        raise ValueError("position must be one of 'top', 'bottom', 'left', 'right'")
    # Font size: try to fit text in text_area_h, or use provided font_size
    if font_size is None:
        cur_font_size = text_area_h // 3
    else:
        cur_font_size = font_size
    if font_path:
        font = ImageFont.truetype(font_path, cur_font_size)
    else:
        font = ImageFont.load_default()
    # Wrap text to fit text_area_w
    def get_wrapped(text, font, max_width):
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

    # Adjust font size to fit if not provided
    if font_size is None:
        while True:
            wrapped = get_wrapped(text, font, text_area_w)
            bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if (tw <= text_area_w and th <= text_area_h) or cur_font_size <= 10:
                break
            cur_font_size -= 2
            if font_path:
                font = ImageFont.truetype(font_path, cur_font_size)
            else:
                font = ImageFont.load_default()
    else:
        wrapped = get_wrapped(text, font, text_area_w)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Position
    if position == 'top':
        x = margin + (text_area_w - tw) // 2
        y = margin + (text_area_h - th) // 2
    elif position == 'bottom':
        x = margin + (text_area_w - tw) // 2
        y = H - text_area_h - margin + (text_area_h - th) // 2
    elif position == 'left':
        x = margin + (text_area_w - tw) // 2
        y = margin + (text_area_h - th) // 2
    elif position == 'right':
        x = W - text_area_w - margin + (text_area_w - tw) // 2
        y = margin + (text_area_h - th) // 2
    # Draw text
    draw.multiline_text((x, y), wrapped, font=font, fill=font_color, align='center')
    img.save(output_path)
    return output_path
