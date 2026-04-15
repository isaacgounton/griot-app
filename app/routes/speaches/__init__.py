"""Speaches sidecar proxy routes."""

from fastapi import APIRouter
from app.routes.speaches.models import router as models_router
from app.routes.speaches.vad import router as vad_router

router = APIRouter(tags=["Content Tools"])
router.include_router(models_router)
router.include_router(vad_router)

__all__ = ["router"]
