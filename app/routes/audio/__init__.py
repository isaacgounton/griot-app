"""Audio-related routes."""
from fastapi import APIRouter
from app.routes.audio.text_to_speech import router as text_to_speech_router
from app.routes.audio.music import router as music_router
from app.routes.audio.transcription import router as transcription_router

# Create a main router that includes all audio-related routes
router = APIRouter()
router.include_router(text_to_speech_router)
router.include_router(music_router)
router.include_router(transcription_router)