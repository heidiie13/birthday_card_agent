from typing import List
import os, sys
import random
from PIL import Image

sys.path.append(os.path.dirname(__file__))

import uuid
from fastapi import FastAPI, HTTPException, UploadFile, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import File
from fastapi.staticfiles import StaticFiles
from core_ai.graph import build_birthday_card_graph
from api.models import MergedImageResponse, GenerateRequest, GenerateResponse, MergePosition, BackgroundResponse, TemplateResponse
from api.services import get_random_template_service, get_templates_service, get_backgrounds_service, generate_card_service, save_upload_file

from core_ai.utils.tools import (
    get_random_background,
    get_random_foreground,
    merge_foreground_background,
    apply_gaussian_blur_edges,
    cleanup_merged_folder,
)

app = FastAPI(title="Birthday Card API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files

STATIC_DIR = "static"
MERGED_DIR = os.path.join(STATIC_DIR, "merged")
THUMBNAILS_DIR = os.path.join(STATIC_DIR, "thumbnails")
os.makedirs(MERGED_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

graph = build_birthday_card_graph()

def create_3_4_thumbnail(image_path: str, output_path: str, thumbnail_size: int = 240) -> str:
    """
    Tạo thumbnail theo tỉ lệ 3:4 (portrait) từ ảnh gốc.
    Nếu ảnh gốc là landscape (rộng > cao), sẽ xoay thành portrait.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Kiểm tra tỉ lệ ảnh gốc
            width, height = img.size
            
            # Nếu ảnh là landscape (rộng > cao), xoay 90 độ để thành portrait
            if width > height:
                img = img.rotate(90, expand=True)
                width, height = img.size
            
            # Tính toán kích thước thumbnail theo tỉ lệ 3:4
            target_width = int(thumbnail_size * 3 / 4)  # 180 nếu thumbnail_size = 240
            target_height = thumbnail_size  # 240
            
            # Resize ảnh để fit vào khung 3:4, crop nếu cần
            img_ratio = width / height
            target_ratio = 3 / 4
            
            if img_ratio > target_ratio:
                # Ảnh rộng hơn target ratio, crop theo chiều rộng
                new_height = height
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                img = img.crop((left, 0, left + new_width, new_height))
            else:
                # Ảnh hẹp hơn target ratio, crop theo chiều cao
                new_width = width
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                img = img.crop((0, top, new_width, top + new_height))
            
            # Resize về kích thước cuối cùng
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Lưu thumbnail
            img.save(output_path, 'JPEG', quality=85)
            return output_path
            
    except Exception as e:
        return None


@app.get("/templates", response_model=List[MergedImageResponse])
def create_random_template(request: Request,
                          n: int = 10,
                          merge_aspect_ratio: float = 3/4):
    """Create a list of random templates by merging foregrounds and backgrounds."""
    if n <= 0:
        raise HTTPException(status_code=400, detail="Number of templates must be positive.")
    
    templates = []
    for _ in range(n):
        bg_path = get_random_background()
        fg_path = get_random_foreground()
        # Create unique file name to avoid collision
        out_name = f"{uuid.uuid4().hex}.png"
        merged_path = os.path.join(MERGED_DIR, out_name)

        # Always use TOP position for foreground (text will be at bottom)
        merge_position = MergePosition.TOP
        
        img = merge_foreground_background(
            foreground_path=fg_path,
            background_path=bg_path,
            output_path=merged_path,
            merge_position=merge_position.value,
            aspect_ratio=merge_aspect_ratio,
        )
        
        # Cleanup merged folder to keep only 10 newest files
        cleanup_merged_folder(MERGED_DIR, max_files=10)
        
        base_url = str(request.base_url).rstrip("/")
        merged_image_url = f"{base_url}/{merged_path}"
        
        templates.append(
            MergedImageResponse(
                background_path=bg_path,
                foreground_path=fg_path,
                merged_image_path=merged_path,
                aspect_ratio=merge_aspect_ratio,
                merge_position=merge_position,
                merge_margin_ratio=img["merge_margin_ratio"],
                merge_foreground_ratio=img["merge_foreground_ratio"],
                merged_image_url=merged_image_url,
            )
        )
    return templates

@app.get("/backgrounds")
def get_backgrounds(request: Request, n: int = 8):
    """Get a list of available backgrounds with 3:4 thumbnails for display."""
    backgrounds_dir = os.path.join(STATIC_DIR, "images", "backgrounds")
    if not os.path.exists(backgrounds_dir):
        raise HTTPException(status_code=404, detail="Backgrounds directory not found")
    
    # Get all background files
    background_files = []
    for file in os.listdir(backgrounds_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            background_files.append(file)
    
    # Randomly select n backgrounds
    selected_backgrounds = random.sample(background_files, min(n, len(background_files)))
    
    base_url = str(request.base_url).rstrip("/")
    backgrounds = []
    for bg_file in selected_backgrounds:
        bg_path = os.path.join("static", "images", "backgrounds", bg_file)
        
        # Tạo thumbnail path
        bg_name, bg_ext = os.path.splitext(bg_file)
        thumbnail_filename = f"{bg_name}_3x4_thumb.jpg"
        thumbnail_path = os.path.join(THUMBNAILS_DIR, thumbnail_filename)
        
        # Tạo thumbnail nếu chưa có hoặc ảnh gốc mới hơn
        original_path = os.path.join(backgrounds_dir, bg_file)
        if (not os.path.exists(thumbnail_path) or 
            os.path.getmtime(original_path) > os.path.getmtime(thumbnail_path)):
            create_3_4_thumbnail(original_path, thumbnail_path)
        
        # Sử dụng thumbnail URL cho hiển thị, original path cho xử lý
        if os.path.exists(thumbnail_path):
            thumbnail_url = f"{base_url}/static/thumbnails/{thumbnail_filename}"
        else:
            # Fallback về ảnh gốc nếu không tạo được thumbnail
            thumbnail_url = f"{base_url}/{bg_path}"
        
        backgrounds.append({
            "path": bg_path,  # Path gốc để xử lý
            "url": thumbnail_url,  # Thumbnail URL để hiển thị
            "filename": bg_file
        })
    
    return backgrounds
    
@app.post("/upload-template", response_model=MergedImageResponse)
async def upload_template(request = Request, 
                       file: UploadFile = File(...),
                       merge_aspect_ratio: float = 3/4,
                       background_path: str = None):
    """
    Upload a foreground image and merge it with a selected or random background.
    Automatically removes background and crops to bounding box.
    """
    fg_dir = os.path.join(STATIC_DIR, "images", "foregrounds", "uploads")
    os.makedirs(fg_dir, exist_ok=True)
    
    # Always use TOP position for foreground (text will be at bottom)
    merge_position = MergePosition.TOP
        
    # Save original uploaded file
    original_name = f"{uuid.uuid4().hex}_original.png"
    original_path = os.path.join(fg_dir, original_name)
    with open(original_path, "wb") as f:
        f.write(await file.read())
    
    # Process uploaded image: apply gaussian blur edges
    processed_name = f"{uuid.uuid4().hex}_processed.png"
    fg_path = os.path.join(fg_dir, processed_name)

    try:
        # Apply gaussian blur to edges
        processed_path = apply_gaussian_blur_edges(
            original_path, 
            fg_path,
            blur_region=150,
            blur_radius=10,
            blur_top=True,
            blur_bottom=True,
            blur_left=True,
            blur_right=True
        )
        
        # Verify the processed file exists and has content
        if os.path.exists(processed_path) and os.path.getsize(processed_path) > 0:
            fg_path = processed_path
        else:
            import shutil
            shutil.copy2(original_path, fg_path)
            
    except Exception as e:
        # If processing fails, use original file
        import shutil
        shutil.copy2(original_path, fg_path)

    # Use selected background or get random one
    if background_path and os.path.exists(background_path):
        bg_path = background_path
    else:
        bg_path = get_random_background()

    out_name = f"{uuid.uuid4().hex}.png"
    merged_path = os.path.join(MERGED_DIR, out_name)
    img = merge_foreground_background(
        foreground_path=fg_path,
        background_path=bg_path,
        output_path=merged_path,
        merge_position=merge_position.value,
        aspect_ratio=merge_aspect_ratio,
    )
    
    # Cleanup merged folder to keep only 10 newest files
    cleanup_merged_folder(MERGED_DIR, max_files=10)
    
    base_url = str(request.base_url).rstrip("/")
    merged_image_url = f"{base_url}/{merged_path}"

    return MergedImageResponse(
        background_path=bg_path,
        foreground_path=fg_path,
        merged_image_path=merged_path,
        aspect_ratio=merge_aspect_ratio,
        merge_position=merge_position,
        merge_margin_ratio=img["merge_margin_ratio"],
        merge_foreground_ratio= img["merge_foreground_ratio"],
        merged_image_url=merged_image_url,
    )

@app.post("/generate-card", response_model=GenerateResponse)
def generate_card(req: GenerateRequest, request: Request):
    """Generate a birthday card with text."""

    input_data = {
        "aspect_ratio": req.aspect_ratio,
        "greeting_text_instructions": req.greeting_text_instructions,
        "card_type": req.card_type,  # Truyền loại thiệp đã chọn
        "background_path": req.background_path,
        "foreground_path": req.foreground_path,
        "merged_image_path": req.merged_image_path,
        "merge_position": req.merge_position,
        "merge_margin_ratio": req.merge_margin_ratio,
        "merge_foreground_ratio": req.merge_foreground_ratio,
    }

    try:
        result_state = graph.invoke(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    image_path = result_state.get("merged_with_text_path") or req.merged_image_path
    base_url = str(request.base_url).rstrip("/")
    # Convert local path to URL path
    if image_path.startswith(STATIC_DIR):
        image_url = f"{base_url}/{image_path}"
    else:
        image_url = f"{base_url}/{STATIC_DIR}/{os.path.relpath(image_path, STATIC_DIR)}"

    return GenerateResponse(
        image_url=image_url,
        background_path=req.background_path,
        foreground_path=req.foreground_path,
        merged_image_path=image_path,
    )

@app.get("/templates/{type}", response_model=List[TemplateResponse])
def get_templates_by_type(
    type: str,
    request: Request,
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """Get template cards by type with pagination."""
    return get_templates_service(type, request, page, page_size)

@app.get("/random-template/{type}", response_model=TemplateResponse)
def get_random_template_by_type_endpoint(type: str, request: Request):
    """Get a random template card by type."""
    return get_random_template_service(type, request)
