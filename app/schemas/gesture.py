from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GestureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    display_name: str
    description: str | None
    model_supported: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
