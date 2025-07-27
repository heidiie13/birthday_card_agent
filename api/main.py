from typing import List
import os, sys
import random

sys.path.append(os.path.dirname(__file__))

import uuid
from fastapi import FastAPI, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.params import File
from fastapi.staticfiles import StaticFiles
from core_ai.graph import build_birthday_card_graph
from api.models import MergedImageResponse, GenerateRequest, GenerateResponse, MergePosition

from core_ai.utils.tools import (
    get_random_background,
    get_random_foreground,
    merge_foreground_background,
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
os.makedirs(MERGED_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

graph = build_birthday_card_graph()


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

        if abs(merge_aspect_ratio - 16/9) < 0.01:
            merge_position = random.choice([MergePosition.LEFT, MergePosition.RIGHT])
        else:
            merge_position = random.choice([MergePosition.TOP, MergePosition.BOTTOM])
        
        img = merge_foreground_background(
            foreground_path=fg_path,
            background_path=bg_path,
            output_path=merged_path,
            merge_position=merge_position.value,
            aspect_ratio=merge_aspect_ratio,
        )
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
    
@app.post("/upload-template", response_model=MergedImageResponse)
async def upload_template(request = Request, 
                       file: UploadFile = File(...),
                       merge_aspect_ratio: float = 3/4):
    """
    Upload a foreground image and merge it with a random background.
    """
    fg_dir = os.path.join(STATIC_DIR, "foregrounds/uploads")
    os.makedirs(fg_dir, exist_ok=True)
    if abs(merge_aspect_ratio - 16/9) < 0.01:
        merge_position = random.choice([MergePosition.LEFT, MergePosition.RIGHT])
    else:
        merge_position = random.choice([MergePosition.TOP, MergePosition.BOTTOM])
        
    fg_name = f"{uuid.uuid4().hex}.png"
    fg_path = os.path.join(fg_dir, fg_name)
    with open(fg_path, "wb") as f:
        f.write(await file.read())

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
        "full_name": req.full_name,
        "gender": req.gender,
        "birthday": req.birthday,
        "aspect_ratio": req.aspect_ratio,
        "extra_requirements": req.extra_requirements,
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
