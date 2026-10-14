from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import EmgSample
from app.db.session import get_db
from app.schemas.sample import SampleListResponse, SampleOut

router = APIRouter()


@router.get("", response_model=SampleListResponse, summary="List available EMG samples")
def list_samples(
    gesture_code: str | None = Query(default=None, description="Filter by gesture code"),
    subject_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(EmgSample)
    if gesture_code:
        query = query.filter(EmgSample.gesture_code == gesture_code)
    if subject_id is not None:
        query = query.filter(EmgSample.subject_id == subject_id)

    total = query.count()
    items = query.order_by(EmgSample.id).offset(offset).limit(limit).all()

    return SampleListResponse(
        items=[SampleOut.model_validate(s) for s in items],
        total=total,
    )
