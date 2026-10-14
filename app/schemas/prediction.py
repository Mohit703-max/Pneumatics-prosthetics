from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """
    Request body for POST /api/v1/predictions.

    Either supply a registered sample_id or provide raw_emg directly.
    raw_emg must be a list of 10 channels, each a list of float values
    (minimum 50 samples per channel to support feature extraction).
    """

    sample_id: int | None = Field(
        default=None,
        description="ID of a registered EmgSample. Mutually exclusive with raw_emg.",
    )
    raw_emg: list[list[float]] | None = Field(
        default=None,
        description="10-channel EMG window. Shape: [10][n_samples]. Min 50 samples.",
    )

    def model_post_init(self, __context: object) -> None:
        if self.sample_id is None and self.raw_emg is None:
            raise ValueError("Provide either sample_id or raw_emg.")
        if self.sample_id is not None and self.raw_emg is not None:
            raise ValueError("Provide sample_id or raw_emg, not both.")
        if self.raw_emg is not None:
            if len(self.raw_emg) != 10:
                raise ValueError("raw_emg must have exactly 10 channels.")
            for ch in self.raw_emg:
                if len(ch) < 50:
                    raise ValueError("Each channel must have at least 50 samples.")


class PredictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: int
    predicted_code: str
    predicted_display_name: str | None
    confidence: float | None
    inference_mode: str  # 'model' | 'fallback'
    class_probabilities: dict[str, float] | None
    created_at: datetime


class PredictionHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: int
    predicted_code: str
    predicted_display_name: str | None
    confidence: float | None
    inference_mode: str
    sample_id: int | None
    created_at: datetime


class PredictionHistoryResponse(BaseModel):
    items: list[PredictionHistoryItem]
    total: int
