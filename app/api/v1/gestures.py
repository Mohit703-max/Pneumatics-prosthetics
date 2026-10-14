from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Gesture
from app.db.session import get_db
from app.schemas.gesture import GestureOut

router = APIRouter()


@router.get("", response_model=list[GestureOut], summary="List canonical gesture registry")
def list_gestures(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Gesture)
    if active_only:
        query = query.filter(Gesture.is_active.is_(True))
    return query.order_by(Gesture.id).all()


@router.get("/{code}", response_model=GestureOut, summary="Get gesture by code")
def get_gesture(code: str, db: Session = Depends(get_db)):
    gesture = db.query(Gesture).filter(Gesture.code == code).first()
    if gesture is None:
        raise HTTPException(status_code=404, detail=f"Gesture '{code}' not found.")
    return gesture
