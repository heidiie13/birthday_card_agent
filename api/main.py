import os, sys
from typing import List
sys.path.append(os.path.dirname(__file__))

from fastapi import UploadFile, File
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.models import ImageUploadResponse, TemplateResponse, GenerateRequest, GenerateResponse, CardType, AspectRatio
from api.services import get_random_template_service, get_templates_service, generate_card_service, upload_images_service

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

@app.get(
    "/templates/{card_type}",
    response_model=List[TemplateResponse],
    description="Get template cards by type with pagination",
    tags=["Templates"]
)
def get_templates(
    card_type: CardType,
    aspect_ratio: AspectRatio,
    request: Request,
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """Get template cards by type with pagination."""
    return get_templates_service(card_type.value, aspect_ratio.value, request, page, page_size)

@app.get(
    "/random-template/{card_type}",
    response_model=TemplateResponse,
    description="Get a random template card by type",
    tags=["Templates"]
)
def get_random_template(card_type: CardType, aspect_ratio: AspectRatio, request: Request):
    """Get a random template card by type."""
    return get_random_template_service(card_type.value, aspect_ratio.value, request)

@app.post(
    "/generate-card",
    response_model=GenerateResponse,
    description="""
    Generate a birthday card based on the provided request.

    - The `greeting_text_instructions` is used to generate a meaningful greeting text (required).
    - If just `foreground_path` is provided, it will use the provided foreground image with a similar background to merge.
    - If `merge_image_path`, `background_path` and `foreground_path` are not provided, it will automatically select appropriate templates based on the `greeting_text_instructions`.
    - The `aspect_ratio` can be 3:4 or 4:3, which determines the layout of the card.
    """,
    tags=["Card Generation"]
)
def generate_card(req: GenerateRequest, request: Request):
    """Generate a birthday card based on the provided request."""
    return generate_card_service(req, request)

@app.post(
    "/upload-foreground",
    response_model=ImageUploadResponse,
    description="Upload a foreground image for the card.",
    tags=["Image Upload"]
)
async def upload_foreground(req: Request, file: UploadFile = File(...)):
    """Upload a foreground image for the card."""
    return upload_images_service(file, req)