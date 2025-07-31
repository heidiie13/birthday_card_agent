import os, sys
from typing import List
sys.path.append(os.path.dirname(__file__))

from fastapi import UploadFile, File
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.models import BackgroundResponse, TemplateResponse, GenerateRequest, GenerateResponse
from api.services import get_random_template_service, get_templates_service, get_backgrounds_service, generate_card_service, save_upload_file


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

@app.get("/templates/{type}", response_model=List[TemplateResponse])
def get_templates(
    type: str,
    request: Request,
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """Get template cards by type with pagination."""
    return get_templates_service(type, request, page, page_size)

@app.get("/random-template/{type}", response_model=TemplateResponse)
def get_random_template(type: str, request: Request):
    """Get a random template card by type."""
    return get_random_template_service(type, request)

@app.get("/backgrounds", response_model=List[BackgroundResponse])
def get_backgrounds(req: Request, page: int = Query(1, ge=1, description="Page number, starting from 1"),
                    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")):
    """Get available background images with pagination."""
    return get_backgrounds_service(req, page, page_size)

@app.post("/generate-card", response_model=GenerateResponse)
def generate_card(req: GenerateRequest, request: Request):
    """Generate a birthday card based on the provided request."""
    return generate_card_service(req, request)

@app.post("/upload_foreground")
async def upload_foreground(req: Request, file: UploadFile = File(...)):
    try:
        result = save_upload_file(file, "foregrounds", req)
        return {"foreground_url": result["url"], "foreground_path": result["path"]}
    except ValueError as e:
        return {"error": str(e)}

@app.post("/upload_background")
async def upload_background(req: Request, file: UploadFile = File(...)):
    try:
        result = save_upload_file(file, "backgrounds", req)
        return {"background_url": result["url"], "background_path": result["path"]}
    except ValueError as e:
        return {"error": str(e)}