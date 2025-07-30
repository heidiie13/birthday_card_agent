import os
import shutil
from typing import List

from fastapi import HTTPException, Request, UploadFile
from api.models import BackgroundResponse, TemplateResponse, GenerateRequest, GenerateResponse

from core_ai.utils.tools import get_templates_by_style
from core_ai.graph import build_birthday_card_graph

STATIC_DIR = "static"
CARDS_DIR = os.path.join(STATIC_DIR, "images", "cards")

graph = build_birthday_card_graph()

def get_templates_service(style: str, request: Request, page: int = 1, page_size: int = 10) -> List[TemplateResponse]:
    cards = get_templates_by_style(style)
    base_url = str(request.base_url).rstrip("/")
    start = (page - 1) * page_size
    end = start + page_size
    paged_cards = cards[start:end]
    result = []
    for card in paged_cards:
        merged_image_path = card.get("merged_image_path")
        merged_image_url = f"{base_url}/{merged_image_path}"
        result.append(TemplateResponse(
            background_path=card.get("background_path"),
            foreground_path=card.get("foreground_path"),
            merged_image_path=merged_image_path,
            aspect_ratio=card.get("aspect_ratio"),
            merge_position=card.get("merge_position"),
            merge_margin_ratio=card.get("merge_margin_ratio"),
            merge_foreground_ratio=card.get("merge_foreground_ratio"),
            merged_image_url=merged_image_url
        ))
    return result

def get_backgrounds_service(req: Request, page: int = 1, page_size: int = 10) -> List[BackgroundResponse]:
    backgrounds_dir = os.path.join(STATIC_DIR, "images", "backgrounds")
    if not os.path.exists(backgrounds_dir):
        raise HTTPException(status_code=404, detail="Backgrounds directory not found")
    background_files = [f for f in os.listdir(backgrounds_dir) if f.endswith((".png", ".jpg", ".jpeg", ".webp"))]
    if not background_files:
        raise HTTPException(status_code=404, detail="No background images found")
    base_url = str(req.base_url).rstrip("/")
    start = (page - 1) * page_size
    end = start + page_size
    paged_files = background_files[start:end]
    result = []
    for file in paged_files:
        background_path = os.path.join(backgrounds_dir, file)
        background_url = f"{base_url}/static/images/backgrounds/{file}"
        result.append(BackgroundResponse(
            background_url=background_url,
            background_path=background_path
        ))
    return result

def generate_card_service(req: GenerateRequest, request: Request) -> GenerateResponse:
    test_input = {
        "greeting_text_instructions": req.greeting_text_instructions,
        "background_path": req.background_path,
        "foreground_path": req.foreground_path,
        "merged_image_path": req.merged_image_path,
    }
    try:
        result = graph.invoke(test_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    card_path = result.get("card_path")
    if not card_path:
        raise HTTPException(status_code=500, detail="Card generation failed")
    base_url = str(request.base_url).rstrip("/")
    card_url = f"{base_url}/{card_path}"
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