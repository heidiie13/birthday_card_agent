import os, sys
from typing import List
sys.path.append(os.path.dirname(__file__))

from fastapi import UploadFile, File
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.models import BackgroundResponse, TemplateResponse, GenerateRequest, GenerateResponse, CardType, AspectRatio
from api.services import get_random_template_service, get_templates_service, get_random_backgrounds_service, generate_card_service, upload_images_service

app = FastAPI(title="Card Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = "static"
CARDS_DIR = os.path.join(STATIC_DIR, "images", "cards")
os.makedirs(CARDS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/templates/{card_type}", response_model=List[TemplateResponse])
def get_templates(
    card_type: CardType,
    aspect_ratio: AspectRatio,
    request: Request,
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """Get template cards by type with pagination."""
    return get_templates_service(card_type.value, aspect_ratio.value, request, page, page_size)


@app.get("/random-template/{card_type}", response_model=TemplateResponse)
def get_random_template(card_type: CardType, aspect_ratio: AspectRatio, request: Request):
    """Get a random template card by type."""
    return get_random_template_service(card_type.value, aspect_ratio.value, request)

@app.get("/random-background", response_model=BackgroundResponse)
def get_random_background(req: Request):
    """Get a random background image."""
    return get_random_backgrounds_service(req)

@app.post("/generate-card", response_model=GenerateResponse)
def generate_card(req: GenerateRequest, request: Request):
    """Generate a birthday card based on the provided request."""
    return generate_card_service(req, request)

@app.post("/upload-foreground")
async def upload_foreground(req: Request, file: UploadFile = File(...)):
    try:
        result = upload_images_service(file, req)
        return {"foreground_url": result["foreground_url"], "foreground_path": result["foreground_path"]}
    except ValueError as e:
        return {"error": str(e)}