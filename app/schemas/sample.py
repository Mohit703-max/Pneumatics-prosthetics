from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    exercise: int
    repetition: int
    window_index: int
    gesture_code: str
    n_channels: int
    n_samples: int
    source_file: str
    created_at: datetime


class SampleListResponse(BaseModel):
    items: list[SampleOut]
    total: int
