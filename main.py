"""
HASTRA backend entry point.

Run with:
    .venv\\Scripts\\uvicorn.exe main:app --reload --host 0.0.0.0 --port 8000
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HASTRA API",
    description=(
        "EMG-based hand-gesture recognition backend.\n\n"
        "Prediction results marked `inference_mode='fallback'` are produced by a "
        "heuristic baseline — **not** a trained model. This label is always "
        "present in API responses and must be surfaced in the UI."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten before any public deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("HASTRA backend starting up…")
    db = SessionLocal()
    try:
        init_db(db)
    except Exception as exc:
        logger.error("Database initialisation failed: %s", exc)
    finally:
        db.close()
