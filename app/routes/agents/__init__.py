"""Convenience exports for agent-related routers."""

from fastapi import APIRouter
from app.routes.agents.agents import router as agents_router
from app.routes.agents.sessions import router as sessions_router
from app.routes.agents.knowledge import router as knowledge_router
from app.routes.agents.preferences import router as preferences_router
from app.routes.agents.voice import router as voice_router

# Create a combined router for all agent routes.
# IMPORTANT: agents_router MUST be last because it has a /{agent_type} catch-all
# that would intercept /sessions, /knowledge-bases, etc. if registered first.
router = APIRouter()
router.include_router(sessions_router)
router.include_router(knowledge_router)
router.include_router(preferences_router)
router.include_router(voice_router)
router.include_router(agents_router)

__all__ = [
	"router",
	"agents_router",
	"sessions_router",
	"knowledge_router",
	"preferences_router",
	"voice_router",
]
