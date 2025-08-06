import json
import os
from pathlib import Path
import shutil
from typing import List
import logging
from fastapi import HTTPException, Request, UploadFile
from api.models import ImageUploadResponse, TemplateResponse, GenerateRequest, GenerateResponse, BackgroundUploadResponse, TemplateUploadResponse, CardType

from core_ai.utils.tools import get_templates_by_type, get_random_template_by_type, get_dominant_color
from core_ai.graph import build_card_gen_graph
from utils.metadata import add_background_metadata, add_template_metadata

logger = logging.getLogger(__name__)

STATIC_DIR = "static"
CARDS_DIR = os.path.join(STATIC_DIR, "images", "cards")

graph = build_card_gen_graph()

def get_templates_service(card_type: str, aspect_ratio: float, request: Request, page: int = 1, page_size: int = 10) -> List[TemplateResponse]:
    templates = get_templates_by_type(card_type, aspect_ratio)
    start = (page - 1) * page_size
    end = start + page_size
    paged_cards = templates[start:end]
    result = []
    for temp in paged_cards:
        merged_image_path = temp.get("merged_image_path")
        merged_image_url = str(request.base_url).rstrip("/") + f"/{merged_image_path.replace(os.sep, '/')}"
        result.append(TemplateResponse(
            background_path=temp.get("background_path"),
            foreground_path=temp.get("foreground_path"),
            merged_image_path=merged_image_path,
            aspect_ratio=temp.get("aspect_ratio"),
            merge_position=temp.get("merge_position"),
            merge_margin_ratio=temp.get("merge_margin_ratio"),
            merge_foreground_ratio=temp.get("merge_foreground_ratio"),
            merged_image_url=merged_image_url
        ))
    return result

def get_random_template_service(card_type: str, aspect_ratio: float, request: Request) -> TemplateResponse:
    template = get_random_template_by_type(card_type, aspect_ratio)
    merged_image_url = str(request.base_url).rstrip("/") + f"/{template['merged_image_path'].replace(os.sep, '/')}"
    template['merged_image_url'] = merged_image_url
    if not template:
        raise HTTPException(status_code=404, detail="No template found")
    return TemplateResponse(**template)

def generate_card_service(req: GenerateRequest, request: Request, foreground_file: UploadFile = None) -> GenerateResponse:
    input = {
        "greeting_text_instructions": req.greeting_text_instructions,
        "aspect_ratio": req.aspect_ratio,
    }
    
    # Handle foreground file upload if provided
    if foreground_file:
        allowed_ext = (".png", ".jpg", ".jpeg", ".webp")
        if not foreground_file.filename.lower().endswith(allowed_ext):
            raise HTTPException(status_code=400, detail="Only image files are allowed (png, jpg, jpeg, webp)")

        upload_dir = os.path.join("static", "images", "foregrounds", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, foreground_file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(foreground_file.file, buffer)
        
        input["foreground_path"] = file_path
    elif req.foreground_path:
        input["foreground_path"] = req.foreground_path
    
    if req.merged_image_path and req.background_path:
        input["merged_image_path"] = req.merged_image_path
        input["background_path"] = req.background_path

    try:
        result = graph.invoke(input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    card_path = result.get("card_path")
    if not card_path:
        raise HTTPException(status_code=500, detail="Card generation failed")
    card_url = str(request.base_url).rstrip("/") + f"/{card_path.replace(os.sep, '/')}"
    return GenerateResponse(card_url=card_url)

def upload_image_service(file: UploadFile, request: Request) -> ImageUploadResponse:
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp")
    if not file.filename.lower().endswith(allowed_ext):
        raise ValueError("Only image files are allowed (png, jpg, jpeg, webp)")

    upload_dir = os.path.join("static", "images", "foregrounds", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = str(request.base_url).rstrip("/") + f"/{file_path.replace(os.sep, '/')}"
    return ImageUploadResponse(foreground_url=file_url, foreground_path=file_path)

def upload_background_service(file: UploadFile, request: Request) -> BackgroundUploadResponse:
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp")
    if not file.filename.lower().endswith(allowed_ext):
        raise ValueError("Only image files are allowed (png, jpg, jpeg, webp)")

    upload_dir = os.path.join("static", "images", "backgrounds")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    if os.path.exists(file_path):
        file_url = str(request.base_url).rstrip("/") + f"/{file_path.replace(os.sep, '/')}"
        color = get_dominant_color(file_path)
        return BackgroundUploadResponse(
            background_url=file_url, 
            background_path=file_path,
            color=color
        )
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    json_path = "static/images/background_metadata.json"
    try:
        result = add_background_metadata(file_path, json_path)
        if result:
            color = result.get("color", "#000000")
        else:
            color = get_dominant_color(file_path)
    except Exception as e:
        color = "#000000"
        logger.error(f"Failed to add background metadata: {e}")

    file_url = str(request.base_url).rstrip("/") + f"/{file_path.replace(os.sep, '/')}"
    return BackgroundUploadResponse(
        background_url=file_url, 
        background_path=file_path,
        color=color
    )

def upload_template_service(
    foreground_file: UploadFile, 
    background_file: UploadFile, 
    card_type: CardType,
    aspect_ratio: float,
    request: Request
) -> TemplateUploadResponse:
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp")
    
    if not foreground_file.filename.lower().endswith(allowed_ext):
        raise ValueError("Only image files are allowed for foreground (png, jpg, jpeg, webp)")
    if not background_file.filename.lower().endswith(allowed_ext):
        raise ValueError("Only image files are allowed for background (png, jpg, jpeg, webp)")

    fg_upload_dir = os.path.join("static", "images", "foregrounds")
    bg_upload_dir = os.path.join("static", "images", "backgrounds")
    os.makedirs(fg_upload_dir, exist_ok=True)
    os.makedirs(bg_upload_dir, exist_ok=True)
    
    fg_file_path = os.path.join(fg_upload_dir, foreground_file.filename)
    bg_file_path = os.path.join(bg_upload_dir, background_file.filename)
    
    if not os.path.exists(fg_file_path):
        with open(fg_file_path, "wb") as buffer:
            shutil.copyfileobj(foreground_file.file, buffer)
    
    if not os.path.exists(bg_file_path):
        with open(bg_file_path, "wb") as buffer:
            shutil.copyfileobj(background_file.file, buffer)
        
        bg_json_path = "static/images/background_metadata.json"
        try:
            add_background_metadata(bg_file_path, bg_json_path)
        except Exception as e:
            logger.error(f"Warning: Failed to add background metadata: {e}")

    json_path = "static/images/template_metadata.json"
    try:
        result = add_template_metadata(
            foreground_path=fg_file_path,
            background_path=bg_file_path,
            json_path=json_path,
            card_type=card_type.value,
            aspect_ratio=aspect_ratio
        )
        
        if result:
            merged_image_path = result.get("merged_image_path")
        else:
            fg_path_normalized = Path(fg_file_path).as_posix()
            bg_path_normalized = Path(bg_file_path).as_posix()
            
            with open(json_path, "r", encoding="utf-8") as f:
                templates = json.load(f)
            
            merged_image_path = None
            for template in templates:
                if (template.get("foreground_path") == fg_path_normalized and 
                    template.get("background_path") == bg_path_normalized and
                    template.get("aspect_ratio") == aspect_ratio and
                    template.get("card_type") == card_type.value):
                    merged_image_path = template.get("merged_image_path")
                    break
        
        if not merged_image_path:
            raise HTTPException(status_code=500, detail="Failed to find generated template")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

    merged_image_url = str(request.base_url).rstrip("/") + f"/{merged_image_path.replace(os.sep, '/')}"
    
    return TemplateUploadResponse(
        merged_image_url=merged_image_url,
        merged_image_path=merged_image_path,
        foreground_path=fg_file_path,
        background_path=bg_file_path,
        card_type=card_type.value,
        aspect_ratio=aspect_ratio
    )