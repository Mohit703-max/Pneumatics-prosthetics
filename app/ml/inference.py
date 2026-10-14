"""
ML inference module.

Loads a trained scikit-learn pipeline from disk when available.
Falls back to a clearly-labelled deterministic stub when no model exists.

The stub does NOT fabricate predictions — it returns the gesture code
that corresponds to the channel with the highest RMS energy, which is
a heuristic baseline only. inference_mode='fallback' is always set on
stub results so the API and UI can display the appropriate label.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from app.ml.features import extract_features

logger = logging.getLogger(__name__)

# Path where the trained pipeline is expected.
MODEL_PATH = Path(__file__).parent / "model.joblib"

# Ordered class labels that the trained model outputs.
# Index 0 = class 0 in model.classes_, etc.
# This list MUST match the label order used during training.
# Update this when a real model is trained.
MODEL_CLASSES: list[str] = []

_pipeline = None  # type: ignore[assignment]
_model_loaded = False


def _try_load_model() -> bool:
    global _pipeline, _model_loaded, MODEL_CLASSES
    if not MODEL_PATH.exists():
        logger.warning("No model file found at %s. Fallback mode active.", MODEL_PATH)
        return False
    try:
        import joblib

        _pipeline = joblib.load(MODEL_PATH)
        # Expect pipeline to carry a label_list attribute set during training
        if hasattr(_pipeline, "label_list"):
            MODEL_CLASSES = _pipeline.label_list
        logger.info("Model loaded from %s. Classes: %s", MODEL_PATH, MODEL_CLASSES)
        _model_loaded = True
        return True
    except Exception as exc:
        logger.error("Failed to load model from %s: %s", MODEL_PATH, exc)
        return False


def model_is_loaded() -> bool:
    return _model_loaded


def get_model_classes() -> list[str]:
    return list(MODEL_CLASSES)


def predict(window: NDArray) -> dict:
    """
    Run inference on a single EMG window.

    Parameters
    ----------
    window : NDArray, shape (n_samples, n_channels)

    Returns
    -------
    dict with keys:
        predicted_code  : str
        confidence      : float | None
        inference_mode  : 'model' | 'fallback'
        class_probabilities : dict[str, float] | None
    """
    global _pipeline, _model_loaded

    # Lazy load on first call
    if not _model_loaded:
        _try_load_model()

    window_arr = np.asarray(window, dtype=np.float64)

    if _model_loaded and _pipeline is not None:
        return _predict_with_model(window_arr)
    return _predict_fallback(window_arr)


def _predict_with_model(window: NDArray) -> dict:
    features = extract_features(window).reshape(1, -1)
    predicted_idx = int(_pipeline.predict(features)[0])

    proba = None
    confidence = None
    class_probs = None

    if hasattr(_pipeline, "predict_proba"):
        proba_arr = _pipeline.predict_proba(features)[0]
        confidence = float(np.max(proba_arr))
        if MODEL_CLASSES:
            class_probs = {
                label: float(p) for label, p in zip(MODEL_CLASSES, proba_arr)
            }

    # Resolve predicted index to gesture code
    if MODEL_CLASSES and 0 <= predicted_idx < len(MODEL_CLASSES):
        predicted_code = MODEL_CLASSES[predicted_idx]
    else:
        predicted_code = str(predicted_idx)

    return {
        "predicted_code": predicted_code,
        "confidence": confidence,
        "inference_mode": "model",
        "class_probabilities": class_probs,
    }


# Fallback gesture order used for heuristic assignment.
# Based on rough RMS energy signature across 10 forearm channels:
# channel groups loosely associated with flexors vs extensors vs rest.
_FALLBACK_CLASSES = [
    "rest",
    "wrist_flexion",
    "wrist_extension",
    "pointing_index",
    "thumbs_up",
    "fist",
]


def _predict_fallback(window: NDArray) -> dict:
    """
    Heuristic baseline — NOT a real model prediction.
    Returns the gesture associated with dominant channel activity.
    Always sets inference_mode='fallback'.
    """
    rms_per_channel = np.sqrt(np.mean(window**2, axis=0))
    total_rms = float(np.sum(rms_per_channel))

    if total_rms < 1e-6:
        # Near-silence → rest
        predicted_code = "rest"
    else:
        # Map dominant channel index to a gesture bucket
        dominant_ch = int(np.argmax(rms_per_channel))
        # 10 channels → 6 buckets
        bucket = int(dominant_ch * len(_FALLBACK_CLASSES) / 10)
        bucket = min(bucket, len(_FALLBACK_CLASSES) - 1)
        predicted_code = _FALLBACK_CLASSES[bucket]

    return {
        "predicted_code": predicted_code,
        "confidence": None,
        "inference_mode": "fallback",
        "class_probabilities": None,
    }
