from fastapi import FastAPI, HTTPException, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid

from core_agent.utils.tools import (
    get_random_background,
    get_random_foreground,
    merge_foreground_background,
)
from core_agent.agent import run_birthday_card_graph

STATIC_DIR = "static"
MERGED_DIR = os.path.join(STATIC_DIR, "merged")

os.makedirs(MERGED_DIR, exist_ok=True)

app = FastAPI(title="Birthday Card API")

# Allow all CORS (since UI may be on a different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class SampleImage(BaseModel):
    background_path: str
    foreground_path: str
    merged_image_path: str

class GenerateRequest(BaseModel):
    full_name: str
    gender: str
    birthday: str
    thread_id: str

    # optional
    background_path: Optional[str] = None
    foreground_path: Optional[str] = None
    merged_image_path: Optional[str] = None
    style: Optional[str] = None
    recipient: Optional[str] = None

class GenerateResponse(BaseModel):
    thread_id: str
    image_url: str
    background_path: str
    foreground_path: str
    merged_image_path: str

class FeedbackRequest(BaseModel):
    thread_id: str
    feedback: str
    background_path: Optional[str] = None
    foreground_path: Optional[str] = None
    merged_image_path: Optional[str] = None

class FeedbackResponse(BaseModel):
    thread_id: str
    image_url: str
    background_path: str
    foreground_path: str
    merged_image_path: str


@app.get("/samples", response_model=List[SampleImage])
def create_random_samples(n: int = 10):
    """Generate n random merged images (without text) and return their paths."""
    samples = []
    for _ in range(n):
        bg_path = get_random_background()
        fg_path = get_random_foreground()
        # Create unique file name to avoid collision
        out_name = f"{uuid.uuid4().hex}.png"
        merged_path = os.path.join(MERGED_DIR, out_name)
        merge_foreground_background(
            foreground_path=fg_path,
            background_path=bg_path,
            output_path=merged_path,
        )
        samples.append(
            SampleImage(
                background_path=bg_path,
                foreground_path=fg_path,
                merged_image_path=merged_path,
            )
        )
    return samples


def _ensure_paths(payload: GenerateRequest):
    """Fill missing paths with random images if necessary."""
    if payload.background_path is None:
        payload.background_path = get_random_background()
    if payload.foreground_path is None:
        payload.foreground_path = get_random_foreground()
    if payload.merged_image_path is None:
        # Merge and create new path
        out_name = f"{uuid.uuid4().hex}.png"
        merged_path = os.path.join(MERGED_DIR, out_name)
        merge_foreground_background(
            foreground_path=payload.foreground_path,
            background_path=payload.background_path,
            output_path=merged_path,
        )
        payload.merged_image_path = merged_path
    return payload


@app.post("/generate", response_model=GenerateResponse)
def generate_card(req: GenerateRequest, request: Request):
    """Generate a birthday card with text."""
    # Ensure required paths exist or create random
    req = _ensure_paths(req)

    input_data = {
        "full_name": req.full_name,
        "gender": req.gender,
        "birthday": req.birthday,
        "recipient": req.recipient,
        "style": req.style,
        "background_path": req.background_path,
        "foreground_path": req.foreground_path,
        "merged_image_path": req.merged_image_path,
    }

    try:
        result_state = run_birthday_card_graph(input_data=input_data, thread_id=req.thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    image_path = result_state.get("merged_image_path") or req.merged_image_path
    base_url = str(request.base_url).rstrip("/")
    # Convert local path to URL path
    if image_path.startswith(STATIC_DIR):
        image_url = f"{base_url}/{image_path}"
    else:
        image_url = f"{base_url}/{STATIC_DIR}/{os.path.relpath(image_path, STATIC_DIR)}"

    return GenerateResponse(
        thread_id=req.thread_id,
        image_url=image_url,
        background_path=req.background_path,
        foreground_path=req.foreground_path,
        merged_image_path=image_path,
    )


@app.post("/feedback", response_model=FeedbackResponse)
def handle_feedback(req: FeedbackRequest, request: Request):
    """Handle user feedback to adjust the card and return updated image."""
    # Ensure we have paths; if missing try to fill in
    req = _ensure_paths(req)  # type: ignore

    input_data = {
        "feedback": req.feedback,
        "background_path": req.background_path,
        "foreground_path": req.foreground_path,
        "merged_image_path": req.merged_image_path,
    }
    try:
        result_state = run_birthday_card_graph(input_data=input_data, thread_id=req.thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    image_path = result_state.get("merged_image_path")
    if image_path is None:
        raise HTTPException(status_code=500, detail="No image generated from feedback")

    base_url = str(request.base_url).rstrip("/")
    if image_path.startswith(STATIC_DIR):
        image_url = f"{base_url}/{image_path}"
    else:
        image_url = f"{base_url}/{STATIC_DIR}/{os.path.relpath(image_path, STATIC_DIR)}"

    return FeedbackResponse(
        thread_id=req.thread_id,
        image_url=image_url,
        background_path=result_state.get("background_path", req.background_path or ""),
        foreground_path=result_state.get("foreground_path", req.foreground_path or ""),
        merged_image_path=image_path,
    )
