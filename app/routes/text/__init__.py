"""
Text generation and processing API routes.
"""

from .completions import router as text_generation_router
from .article_to_script import router as article_to_script_router

__all__ = ["text_generation_router", "article_to_script_router"]