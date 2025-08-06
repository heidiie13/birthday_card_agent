import os, sys 
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import uuid
import json
from pathlib import Path
from core_ai.utils.tools import merge_foreground_background, get_dominant_color

def add_template_metadata(foreground_path: str, background_path: str, json_path: str, card_type: str, aspect_ratio: float = 3/4):
    """
    Merge a foreground and background image, save the merged image, and append its metadata to a JSON file.

    Args:
        foreground_path (str): Path to the foreground image.
        background_path (str): Path to the background image.
        json_path (str): Path to the JSON file to append card info.
        card_type (str): Type/category of the card (e.g., 'birthday', 'graduation').
    """
    # Normalize paths to use forward slashes for consistency across OS
    foreground_path_normalized = Path(foreground_path).as_posix()
    background_path_normalized = Path(background_path).as_posix()
    
    json_file = Path(json_path)
    if json_file.exists() and json_file.stat().st_size > 0:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # Check for existing entry using normalized paths
    for item in data:
        if (
            item.get("foreground_path") == foreground_path_normalized and
            item.get("background_path") == background_path_normalized and
            item.get("aspect_ratio") == aspect_ratio and
            item.get("card_type") == card_type
        ):
            return item

    output_dir = Path(f"static/images/card_types/{card_type}")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{uuid.uuid4()}.png"

    img = merge_foreground_background(
        foreground_path=foreground_path,
        background_path=background_path,
        output_path=str(output_path),
        aspect_ratio=aspect_ratio,
        merge_position="right" if aspect_ratio == 4/3 else "top",
    )

    # Use normalized paths in metadata
    img["foreground_path"] = foreground_path_normalized
    img["background_path"] = background_path_normalized
    img["merged_image_path"] = output_path.as_posix()
    img["card_type"] = card_type
    img["aspect_ratio"] = aspect_ratio

    data.append(img)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return img

def add_background_metadata(background_path: str, json_path: str):
    """
    Add metadata for a single background image to a JSON file.
    Args:
        background_path (str): Path to the background image.
        json_path (str): Path to the JSON file to append background info.
    """
    # Normalize path to use forward slashes for consistency across OS
    background_path_normalized = Path(background_path).as_posix()
    
    json_file = Path(json_path)
    if json_file.exists() and json_file.stat().st_size > 0:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # Check for existing entry using normalized path
    for item in data:
        if item.get("background_path") == background_path_normalized:
            return item

    color = get_dominant_color(background_path)
    item = {
        "background_path": background_path_normalized,
        "color": color
    }
    data.append(item)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return item

def process_background_folder(dir_path: str, json_path: str):
    """
    Process all background images in a folder and add their metadata to a JSON file.

    Args:
        dir_path (str): Path to the directory containing background images.
        json_path (str): Path to the JSON file to save background info.
    """
    file_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    for ext in file_extensions:
        for img_path in dir_path.glob(f"*{ext}"):
            add_background_metadata(
                background_path=str(img_path),
                json_path=json_path
            )

def process_template_txt_file(txt_path: str, json_path: str, card_type: str, aspect_ratio: float = 3/4):
    """
    Read a text file containing lines of '<foreground_path> <background_path>',
    merge each pair, and append their info to a JSON file for the specified card type.

    Args:
        txt_path (str): Path to the text file with image path pairs.
        json_path (str): Path to the JSON file to append card info.
        card_type (str): Type/category of the card (e.g., 'birthday', 'graduation').
    """
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fg_path, bg_path = line.split()
            add_template_metadata(
                foreground_path=fg_path,
                background_path=bg_path,
                json_path=json_path,
                card_type=card_type,
                aspect_ratio=aspect_ratio
            )

def process_template_folder(dir_path: str, json_path: str, aspect_ratio: float = 3/4):
    """
    Process all template images in a folder and add their metadata to a JSON file.
    Card types are determined by the file names.

    Args:
        dir_path (str): Path to the directory containing template images.
        json_path (str): Path to the JSON file to save template info.
        aspect_ratio (float): Aspect ratio for the templates.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    for txt_file in dir_path.glob("*.txt"):
        process_template_txt_file(
            txt_path=str(txt_file),
            json_path=json_path,
            card_type=txt_file.stem,
            aspect_ratio=aspect_ratio
        )

if __name__ == "__main__":
    process_background_folder("static/images/backgrounds", "static/images/background_metadata.json")
    process_template_folder("utils/infor_template", "static/images/template_metadata.json", aspect_ratio=3/4)
    process_template_folder("utils/infor_template", "static/images/template_metadata.json", aspect_ratio=4/3)
