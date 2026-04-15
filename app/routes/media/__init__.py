"""Media-related routes."""
from fastapi import APIRouter
from app.routes.media.download import router as download_router
from app.routes.media.youtube_transcripts import router as youtube_transcripts_router
from app.routes.media.metadata import router as metadata_router
from app.routes.media.silence import router as silence_router
from app.routes.media.media_conversions import router as media_conversions_router

# Create a main router that includes all media-related routes
router = APIRouter()
router.include_router(download_router)
router.include_router(youtube_transcripts_router)
router.include_router(metadata_router)
router.include_router(silence_router)
router.include_router(media_conversions_router)