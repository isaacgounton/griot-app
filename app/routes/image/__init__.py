"""Image-related routes."""
from fastapi import APIRouter
from app.routes.image.image_overlay import router as image_overlay_router
from app.routes.image.enhancement import router as enhancement_router
from app.routes.image.generate import router as generate_router, simple_router as simple_image_router
from app.routes.image.video_overlay import router as video_overlay_router
from app.routes.image.image_to_video import router as image_to_video_router
from app.routes.image.web_screenshot import router as web_screenshot_router

# Create a main router that includes all image-related routes
router = APIRouter()
router.include_router(image_overlay_router)
router.include_router(enhancement_router)
router.include_router(generate_router)
router.include_router(simple_image_router)
router.include_router(video_overlay_router)
router.include_router(image_to_video_router)
router.include_router(web_screenshot_router)
