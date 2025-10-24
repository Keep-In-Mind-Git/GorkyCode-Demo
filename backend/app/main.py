"""FastAPI application entry point for the AI tourist assistant prototype."""

from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from .models import FeedbackRequest, ItineraryRequest, ItineraryResponse
from .services.feedback import record_feedback
from .services.itinerary import ItineraryPlanner


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent.parent / "frontend"

if not FRONTEND_DIR.exists():
    raise RuntimeError("Frontend directory is missing; expected at ../frontend")


load_dotenv()

planner = ItineraryPlanner()

app = FastAPI(title="AI Tourist Assistant", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_directory = FRONTEND_DIR / "static"
static_directory.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_directory), name="static")


@app.get("/health", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def serve_spa() -> FileResponse:
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="SPA index.html not found")
    return FileResponse(index_file)


@app.post("/api/itinerary", response_model=ItineraryResponse)
async def generate_itinerary(payload: ItineraryRequest) -> ItineraryResponse:
    response, _warnings = planner.plan(
        interests=payload.interests,
        available_hours=payload.available_hours,
        location=payload.location,
    )
    return response


@app.post("/api/feedback", status_code=201)
async def submit_feedback(
    payload: FeedbackRequest, background: BackgroundTasks
) -> dict[str, str]:
    background.add_task(record_feedback, payload)
    return {"status": "received"}
