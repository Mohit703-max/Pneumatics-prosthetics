"""
SQLAlchemy ORM models for HASTRA.

Tables
------
gestures          — canonical gesture registry (6 classes)
emg_samples       — references to prerecorded NinaPro windows (metadata only)
predictions       — model inference results linked to gestures
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Gesture(Base):
    """Canonical gesture registry — stable, user-managed reference data."""

    __tablename__ = "gestures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Whether the currently loaded ML model can actually predict this class.
    # Distinct from is_active: a gesture may be active in the registry but
    # not yet supported by the model.
    model_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    predictions: Mapped[list[Prediction]] = relationship(
        "Prediction", back_populates="gesture", lazy="select"
    )


class EmgSample(Base):
    """
    Metadata record for a single prerecorded EMG window sourced from NinaPro DB1.
    Raw signal arrays are NOT stored in the DB; only enough metadata to locate
    and identify the window.
    """

    __tablename__ = "emg_samples"
    __table_args__ = (
        UniqueConstraint("subject_id", "exercise", "repetition", "window_index", name="uq_emg_window"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    exercise: Mapped[int] = mapped_column(Integer, nullable=False)
    repetition: Mapped[int] = mapped_column(Integer, nullable=False)
    # Zero-based index of this window within the repetition
    window_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Canonical gesture code this sample is labelled with (from dataset stimulus)
    gesture_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Number of EMG channels and samples in this window
    n_channels: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    n_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    # Relative path to the source .mat file (relative to data/ directory)
    source_file: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    predictions: Mapped[list[Prediction]] = relationship(
        "Prediction", back_populates="sample", lazy="select"
    )


class Prediction(Base):
    """
    Persisted record of a single inference call.
    Stores the predicted gesture, confidence (when available), and whether
    the result came from a real model or a labelled fallback.
    """

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sample_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("emg_samples.id", ondelete="SET NULL"), nullable=True
    )
    gesture_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("gestures.id", ondelete="SET NULL"), nullable=True
    )
    # Raw predicted gesture code — kept even if gesture_id goes NULL
    predicted_code: Mapped[str] = mapped_column(String(64), nullable=False)
    # Confidence in [0, 1] when available from the model; NULL otherwise
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 'model' | 'fallback' — never hide which mode produced the result
    inference_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="fallback")
    # Optional JSON blob with per-class probabilities (stored as text)
    class_probabilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    gesture: Mapped[Gesture | None] = relationship("Gesture", back_populates="predictions")
    sample: Mapped[EmgSample | None] = relationship("EmgSample", back_populates="predictions")
