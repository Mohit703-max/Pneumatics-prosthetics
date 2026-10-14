import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import Gesture, Prediction
from app.db.session import get_db
from app.schemas.prediction import (
    PredictRequest,
    PredictResponse,
    PredictionHistoryItem,
    PredictionHistoryResponse,
)
from app.services.prediction_service import create_prediction

router = APIRouter()


@router.post("", response_model=PredictResponse, status_code=201, summary="Submit EMG for prediction")
def predict(request: PredictRequest, db: Session = Depends(get_db)):
    try:
        return create_prediction(request, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference error: {type(exc).__name__}")


@router.get("", response_model=PredictionHistoryResponse, summary="Retrieve prediction history")
def list_predictions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total = db.query(Prediction).count()
    rows = (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []
    for row in rows:
        gesture = (
            db.query(Gesture).filter(Gesture.id == row.gesture_id).first()
            if row.gesture_id
            else None
        )
        items.append(
            PredictionHistoryItem(
                prediction_id=row.id,
                predicted_code=row.predicted_code,
                predicted_display_name=gesture.display_name if gesture else None,
                confidence=row.confidence,
                inference_mode=row.inference_mode,
                sample_id=row.sample_id,
                created_at=row.created_at,
            )
        )

    return PredictionHistoryResponse(items=items, total=total)
