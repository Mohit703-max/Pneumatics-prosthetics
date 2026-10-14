from fastapi import APIRouter

from app.api.v1 import gestures, health, predictions, samples

router = APIRouter(prefix="/api/v1")

router.include_router(health.router, tags=["health"])
router.include_router(gestures.router, prefix="/gestures", tags=["gestures"])
router.include_router(samples.router, prefix="/samples", tags=["samples"])
router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
