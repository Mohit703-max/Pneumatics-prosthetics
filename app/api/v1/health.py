from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ml.inference import get_model_classes, model_is_loaded

router = APIRouter()


@router.get("/health", summary="Backend health and readiness check")
def health(db: Session = Depends(get_db)):
    # Probe DB without exposing credentials or internal state
    db_status = "ok"
    db_error: str | None = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        db_error = type(exc).__name__

    ml_status = "model_loaded" if model_is_loaded() else "fallback_active"
    model_classes = get_model_classes()

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "database_error": db_error,
        "ml": {
            "status": ml_status,
            "model_classes": model_classes,
        },
    }
