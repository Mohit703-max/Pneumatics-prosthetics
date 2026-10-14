"""
EMG feature extraction.

All features applied identically during training and inference.
Window shape expected: (n_samples, n_channels) — (rows=time, cols=channels).
"""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def _mean_absolute_value(window: NDArray) -> NDArray:
    """MAV per channel."""
    return np.mean(np.abs(window), axis=0)


def _root_mean_square(window: NDArray) -> NDArray:
    """RMS per channel."""
    return np.sqrt(np.mean(window**2, axis=0))


def _waveform_length(window: NDArray) -> NDArray:
    """WL per channel — cumulative length of waveform."""
    return np.sum(np.abs(np.diff(window, axis=0)), axis=0)


def _zero_crossings(window: NDArray, threshold: float = 0.01) -> NDArray:
    """ZC per channel — number of sign changes above threshold."""
    diff = window[1:] * window[:-1]
    above = np.abs(window[1:] - window[:-1]) >= threshold
    return np.sum((diff < 0) & above, axis=0).astype(float)


def _slope_sign_changes(window: NDArray, threshold: float = 0.01) -> NDArray:
    """SSC per channel."""
    d1 = window[1:-1] - window[:-2]
    d2 = window[2:] - window[1:-1]
    sign_change = (d1 * d2) < 0
    above = (np.abs(d1) >= threshold) | (np.abs(d2) >= threshold)
    return np.sum(sign_change & above, axis=0).astype(float)


def extract_features(window: NDArray) -> NDArray:
    """
    Extract a flat feature vector from an EMG window.

    Parameters
    ----------
    window : NDArray, shape (n_samples, n_channels)

    Returns
    -------
    features : NDArray, shape (n_channels * 5,)
        [MAV, RMS, WL, ZC, SSC] concatenated across channels.
    """
    window = np.asarray(window, dtype=np.float64)
    if window.ndim != 2:
        raise ValueError(f"Window must be 2-D (n_samples, n_channels), got shape {window.shape}")

    feats = np.concatenate(
        [
            _mean_absolute_value(window),
            _root_mean_square(window),
            _waveform_length(window),
            _zero_crossings(window),
            _slope_sign_changes(window),
        ]
    )
    return feats
