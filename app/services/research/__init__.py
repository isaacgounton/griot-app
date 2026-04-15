"""
Research and information gathering services.
"""

from .news_research_service import NewsResearchService

# Create service instance
news_research_service = NewsResearchService()

__all__ = [
    "news_research_service",
    "NewsResearchService"
]