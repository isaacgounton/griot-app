"""Document processing routes."""
from fastapi import APIRouter
from app.routes.documents.to_markdown import router as to_markdown_router
from app.routes.documents.langextract import router as langextract_router
from app.routes.documents.marker import router as marker_router
from app.routes.documents.url_to_markdown import router as url_to_markdown_router

# Create a main router that includes all document-related routes with /documents prefix
# All sub-routers will have /documents prefix from this main router
router = APIRouter(prefix="/documents")
router.include_router(to_markdown_router, prefix="/to-markdown")
router.include_router(langextract_router)
router.include_router(marker_router)
router.include_router(url_to_markdown_router, prefix="/url-to-markdown")