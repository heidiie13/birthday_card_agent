import os
import shutil
from typing import List

from fastapi import HTTPException, Request, UploadFile
from api.models import BackgroundResponse, TemplateResponse, GenerateRequest, GenerateResponse

from core_ai.utils.tools import get_templates_by_type, get_random_template_by_type
from core_ai.graph import build_card_gen_graph

STATIC_DIR = "static"
CARDS_DIR = os.path.join(STATIC_DIR, "images", "cards")

graph = build_card_gen_graph()

def get_templates_service(type: str, request: Request, page: int = 1, page_size: int = 10) -> List[TemplateResponse]:
    templates = get_templates_by_type(type)
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

def get_random_template_service(type: str, request: Request) -> TemplateResponse:
    template = get_random_template_by_type(type)
    merged_image_url = str(request.base_url).rstrip("/") + f"/{template['merged_image_path'].replace(os.sep, '/')}"
    template['merged_image_url'] = merged_image_url
    if not template:
        raise HTTPException(status_code=404, detail="No template found")
    return TemplateResponse(**template)

def get_backgrounds_service(req: Request, page: int = 1, page_size: int = 10) -> List[BackgroundResponse]:
    backgrounds_dir = os.path.join(STATIC_DIR, "images", "backgrounds")
    if not os.path.exists(backgrounds_dir):
        raise HTTPException(status_code=404, detail="Backgrounds directory not found")
    background_files = [f for f in os.listdir(backgrounds_dir) if f.endswith((".png", ".jpg", ".jpeg", ".webp"))]
    if not background_files:
        raise HTTPException(status_code=404, detail="No background images found")
    start = (page - 1) * page_size
    end = start + page_size
    paged_files = background_files[start:end]
    result = []
    for file in paged_files:
        background_path = os.path.join(backgrounds_dir, file)
        background_url = str(req.base_url).rstrip("/") + f"/{background_path.replace(os.sep, '/')}"
        result.append(BackgroundResponse(
            background_url=background_url,
            background_path=background_path
        ))
    return result

def generate_card_service(req: GenerateRequest, request: Request) -> GenerateResponse:
    input = {
        "greeting_text_instructions": req.greeting_text_instructions,
    }
    
    # Add paths if provided - support both template mode and user upload mode
    if req.background_path:
        input["background_path"] = req.background_path
    if req.foreground_path:
        input["foreground_path"] = req.foreground_path
    if req.merged_image_path:
        input["merged_image_path"] = req.merged_image_path
        
    try:
        result = graph.invoke(input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    card_path = result.get("card_path")
    if not card_path:
        raise HTTPException(status_code=500, detail="Card generation failed")
    card_url = str(request.base_url).rstrip("/") + f"/{card_path.replace(os.sep, '/')}"
    return GenerateResponse(card_url=card_url)


def save_upload_file(file: UploadFile, subfolder: str, request: Request) -> dict:
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp")
    if not file.filename.lower().endswith(allowed_ext):
        raise ValueError("Only image files are allowed (png, jpg, jpeg, webp)")

    upload_dir = os.path.join("static", "images", subfolder, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = str(request.base_url).rstrip("/") + f"/{file_path.replace(os.sep, '/')}"
    return {"url": file_url, "path": file_path}