"""News research API routes."""

import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.research.news_research_service import news_research_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["Research"])


class NewsResearchRequest(BaseModel):
    """Request model for news research."""
    query: str = Field(..., description="Search query for news research")
    language: str = Field("en", description="Language code for results")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results")
    sort_by: str = Field("relevance", description="Sort by: relevance, date, popularity")
    time_range: str | None = Field(None, description="Time range: day, week, month, year")


class NewsArticle(BaseModel):
    """News article model."""
    title: str
    description: str
    url: str
    source: str
    published_at: str
    image_url: str | None = None
    tags: list[str] = []


class NewsResearchResponse(BaseModel):
    """Response model for news research."""
    articles: list[NewsArticle]
    total_results: int
    search_query: str
    search_time: float


@router.post("/news", response_model=NewsResearchResponse)
async def research_news(
    request: NewsResearchRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Research news articles based on a query using AI-powered search."""
    try:
        result = await news_research_service.research_news(
            query=request.query,
            language=request.language,
            max_results=request.max_results,
            sort_by=request.sort_by,
            time_range=request.time_range
        )

        # Convert to response format
        articles = []
        for article in result.get("articles", []):
            articles.append(NewsArticle(
                title=article.get("title", ""),
                description=article.get("description", ""),
                url=article.get("url", ""),
                source=article.get("source", ""),
                published_at=article.get("published_at", ""),
                image_url=article.get("image_url"),
                tags=article.get("tags", [])
            ))

        return NewsResearchResponse(
            articles=articles,
            total_results=result.get("total_results", len(articles)),
            search_query=result.get("search_query", request.query),
            search_time=result.get("search_time", 0.0)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error researching news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"News research failed: {str(e)}")


@router.get("/news/sources")
async def get_news_sources(_: dict[str, Any] = Depends(get_current_user)):
    """Get available news sources and their capabilities."""
    return {
        "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh"],
        "sort_options": ["relevance", "date", "popularity"],
        "time_ranges": ["day", "week", "month", "year"],
        "features": [
            "AI-powered search",
            "Multi-language support",
            "Source credibility scoring",
            "Real-time news aggregation",
            "Topic clustering"
        ]
    }