import os, sys 
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import uuid
import json
from pathlib import Path
from core_ai.utils.tools import merge_foreground_background

def add_card_info_to_json(foreground_path: str, background_path: str, json_path: str, card_type: str):
    """
    Merge a foreground and background image, save the merged image, and append its metadata to a JSON file.

    Args:
        foreground_path (str): Path to the foreground image.
        background_path (str): Path to the background image.
        json_path (str): Path to the JSON file to append card info.
        card_type (str): Type/category of the card (e.g., 'birthday', 'graduation').
    """
    output_dir = Path(f"static/images/card_types/{card_type}")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = str(output_dir / f"{uuid.uuid4()}.png")

    img = merge_foreground_background(
        foreground_path=foreground_path,
        background_path=background_path,
        output_path=output_path
    )

    img["card_type"] = card_type

    json_file = Path(json_path)
    if json_file.exists() and json_file.stat().st_size > 0:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    for item in data:
        if (
            item.get("foreground_path") == foreground_path and
            item.get("background_path") == background_path
        ):
            return

    data.append(img)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_txt_file(txt_path: str, json_path: str, card_type: str):
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
            add_card_info_to_json(
                foreground_path=fg_path,
                background_path=bg_path,
                json_path=json_path,
                card_type=card_type
            )

if __name__ == "__main__":
    # Example usage
    process_txt_file(
        txt_path="christmas.txt",
        json_path="static/images/template_card_info.json",
        card_type="christmas"
    )
    
    process_txt_file(
        txt_path="general.txt",
        json_path="static/images/template_card_info.json",
        card_type="general"
    )

    process_txt_file(
        txt_path="new_year.txt",
        json_path="static/images/template_card_info.json",
        card_type="new_year"
    )
    process_txt_file(
        txt_path="teacher_day.txt",
        json_path="static/images/template_card_info.json",
        card_type="teacher_day"
    )
    process_txt_file(
        txt_path="valentine.txt",
        json_path="static/images/template_card_info.json",
        card_type="valentine"
    )