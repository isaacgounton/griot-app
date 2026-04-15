"""Studio V2 API routes."""
from fastapi import APIRouter

from app.routes.studio.projects import router as projects_router
from app.routes.studio.scenes import router as scenes_router
from app.routes.studio.generation import router as generation_router

router = APIRouter(tags=["Studio"])
router.include_router(projects_router)
router.include_router(scenes_router)
router.include_router(generation_router)
