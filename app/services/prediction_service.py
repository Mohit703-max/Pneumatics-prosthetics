"""
Prediction service — orchestrates EMG loading, inference, and persistence.
"""
from __future__ import annotations

import json
import logging

import numpy as np
from sqlalchemy.orm import Session

from app.db.models import EmgSample, Gesture, Prediction
from app.ml.inference import predict as run_inference
from app.schemas.prediction import PredictRequest, PredictResponse

logger = logging.getLogger(__name__)


def _load_sample_window(sample: EmgSample) -> np.ndarray:
    """
    Load the raw EMG window for a registered sample.
    Returns ndarray shape (n_samples, n_channels).

    Currently raises NotImplementedError when no dataset loader is available.
    This is the integration point for the NinaPro .mat loader.
    """
    raise NotImplementedError(
        "Dataset loader not yet implemented. "
        "Supply raw_emg directly in the request until the NinaPro dataset is loaded."
    )


def create_prediction(request: PredictRequest, db: Session) -> PredictResponse:
    sample: EmgSample | None = None
    window: np.ndarray

    if request.sample_id is not None:
        sample = db.get(EmgSample, request.sample_id)
        if sample is None:
            raise ValueError(f"Sample {request.sample_id} not found.")
        window = _load_sample_window(sample)
    else:
        # raw_emg is list[list[float]], shape [n_channels][n_samples]
        # Transpose to (n_samples, n_channels)
        window = np.array(request.raw_emg, dtype=np.float64).T

    result = run_inference(window)

    # Resolve gesture FK
    gesture = (
        db.query(Gesture)
        .filter(Gesture.code == result["predicted_code"], Gesture.is_active.is_(True))
        .first()
    )

    class_probs_json: str | None = None
    if result.get("class_probabilities"):
        class_probs_json = json.dumps(result["class_probabilities"])

    prediction = Prediction(
        sample_id=sample.id if sample else None,
        gesture_id=gesture.id if gesture else None,
        predicted_code=result["predicted_code"],
        confidence=result.get("confidence"),
        inference_mode=result["inference_mode"],
        class_probabilities=class_probs_json,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    class_probs_out: dict | None = None
    if prediction.class_probabilities:
        class_probs_out = json.loads(prediction.class_probabilities)

    return PredictResponse(
        prediction_id=prediction.id,
        predicted_code=prediction.predicted_code,
        predicted_display_name=gesture.display_name if gesture else None,
        confidence=prediction.confidence,
        inference_mode=prediction.inference_mode,
        class_probabilities=class_probs_out,
        created_at=prediction.created_at,
    )
