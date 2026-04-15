"""
Pollinations AI Routes

Vision analysis, audio generation, and model listing endpoints.
Image generation is handled by app/routes/image/generate.py.
Text generation is handled by app/routes/anyllm/completions.py.
Video generation is handled by app/routes/video/generate.py.
"""
from fastapi import APIRouter

from app.routes.pollinations.image import router as image_router
from app.routes.pollinations.audio import router as audio_router
from app.routes.pollinations.video import router as video_router

# Create a main router that includes remaining Pollinations AI routes
router = APIRouter()
router.include_router(image_router)
router.include_router(audio_router)
router.include_router(video_router)
