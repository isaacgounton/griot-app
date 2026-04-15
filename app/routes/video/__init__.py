"""
Routes for video manipulation operations.
"""
from fastapi import APIRouter

from app.routes.video.concatenate import router as concatenate_router
from app.routes.video.add_audio import router as add_audio_router
from app.routes.video.caption import router as caption_router
from app.routes.video.text_overlay import router as text_overlay_router
from app.routes.video.thumbnails import router as thumbnails_router
from app.routes.video.clips import router as clips_router
from app.routes.video.frames import router as frames_router
from app.routes.video.generate import router as generate_router
from app.routes.video.advanced import router as advanced_router
from app.routes.video.videos import router as videos_router

router = APIRouter()
router.include_router(concatenate_router)
router.include_router(add_audio_router)
router.include_router(caption_router)
router.include_router(text_overlay_router)
router.include_router(thumbnails_router)
router.include_router(clips_router)
router.include_router(frames_router)
router.include_router(generate_router)
router.include_router(advanced_router)
router.include_router(videos_router)