"""
Idempotent database initialisation.

Creates all tables and seeds the canonical gesture registry.
Safe to call at every startup — uses INSERT ... ON CONFLICT DO NOTHING
so duplicate rows are never created and existing user edits are preserved.
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)

# Canonical gesture definitions for HASTRA.
# model_supported starts False — set to True once a real model is trained
# and the mapping is verified against the dataset.
CANONICAL_GESTURES = [
    {
        "code": "rest",
        "display_name": "Rest",
        "description": "Hand at rest with no deliberate movement.",
        "model_supported": False,
        "is_active": True,
    },
    {
        "code": "wrist_flexion",
        "display_name": "Wrist Flexion",
        "description": "Wrist bends downward (palmar flexion).",
        "model_supported": False,
        "is_active": True,
    },
    {
        "code": "wrist_extension",
        "display_name": "Wrist Extension",
        "description": "Wrist bends upward (dorsiflexion).",
        "model_supported": False,
        "is_active": True,
    },
    {
        "code": "pointing_index",
        "display_name": "Pointing Index",
        "description": "Index finger extended; other fingers closed.",
        "model_supported": False,
        "is_active": True,
    },
    {
        "code": "thumbs_up",
        "display_name": "Thumbs Up",
        "description": "Thumb extended upward; other fingers closed in fist.",
        "model_supported": False,
        "is_active": True,
    },
    {
        "code": "fist",
        "display_name": "Fist",
        "description": "All fingers fully flexed into closed fist.",
        "model_supported": False,
        "is_active": True,
    },
]


def create_tables() -> None:
    """Create all tables defined in the ORM models (no-op if already exist)."""
    # Import models so metadata is populated before create_all
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created or verified.")


def seed_gestures(db: Session) -> None:
    """
    Insert canonical gestures using INSERT ... ON CONFLICT DO NOTHING.
    Idempotent: safe to call on every startup.
    """
    stmt = text(
        """
        INSERT INTO gestures (code, display_name, description, model_supported, is_active,
                              created_at, updated_at)
        VALUES (:code, :display_name, :description, :model_supported, :is_active,
                NOW(), NOW())
        ON CONFLICT (code) DO NOTHING
        """
    )
    inserted = 0
    for gesture in CANONICAL_GESTURES:
        result = db.execute(stmt, gesture)
        inserted += result.rowcount
    db.commit()
    if inserted:
        logger.info("Seeded %d new gesture(s) into the registry.", inserted)
    else:
        logger.info("Gesture registry already complete — no new rows inserted.")


def init_db(db: Session) -> None:
    create_tables()
    seed_gestures(db)
