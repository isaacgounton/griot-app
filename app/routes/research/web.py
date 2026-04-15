"""Web search API routes supporting multiple search engines."""

import time
import logging
from typing import Any, Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.research.news_research_service import news_research_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["Research"])


class WebSearchRequest(BaseModel):
    """Request model for web search."""
    query: str = Field(..., description="Search query")
    engine: Literal["perplexity", "google"] = Field("perplexity", description="Search engine to use: perplexity or google")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results")
    language: str = Field("en", description="Language code for results")


class SearchResult(BaseModel):
    """Search result item."""
    title: str
    description: str | None = None
    url: str
    source: str
    published_at: str | None = None
    content: str | None = None


class WebSearchResponse(BaseModel):
    """Response model for web search."""
    results: list[SearchResult]
    query: str
    engine: str
    total_results: int
    search_time: float


@router.post("/web")
async def web_search(
    request: WebSearchRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Search the web using Perplexity AI or Google Search."""
    start_time = time.time()

    logger.info(f"Starting web search for query: '{request.query}' using engine: {request.engine}")

    try:
        # Route to appropriate search engine
        if request.engine == "perplexity":
            results_data = await _search_perplexity(request.query, request.max_results, request.language)
        elif request.engine == "google":
            results_data = await _search_google(request.query, request.max_results, request.language)
        else:
            raise ValueError(f"Unsupported search engine: {request.engine}")

        search_time = time.time() - start_time

        # Convert to standard response format
        results = []
        if results_data.get("articles"):
            for article in results_data["articles"]:
                results.append(SearchResult(
                    title=article.get("title", ""),
                    description=article.get("description") or article.get("snippet"),
                    url=article.get("url") or article.get("link", ""),
                    source=article.get("source", ""),
                    published_at=article.get("published_at") or article.get("date"),
                    content=article.get("content")
                ))

        return WebSearchResponse(
            results=results,
            query=request.query,
            engine=request.engine,
            total_results=len(results),
            search_time=search_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")


async def _search_perplexity(query: str, max_results: int, language: str) -> dict[str, Any]:
    """Search using Perplexity AI."""
    logger.info(f"Searching Perplexity for: {query}")
    
    try:
        # Prefer a synthesized answer from Perplexity (concise answer + citations)
        if hasattr(news_research_service, '_search_perplexity_synthesis'):
            synth = await news_research_service._search_perplexity_synthesis(query, max_results)
            # synth format: { 'synthesis': str, 'citations': [ {title,url,snippet,source} ] }
            articles = []
            if synth.get('synthesis'):
                # Primary synthesized answer as first result
                articles.append({
                    'title': f"Answer: {query}",
                    'description': None,
                    'url': '',
                    'source': 'Perplexity',
                    'published_at': None,
                    'content': synth.get('synthesis')
                })

            # Append citations as additional results (if any)
            for c in synth.get('citations', [])[:max_results]:
                articles.append({
                    'title': c.get('title') or c.get('source') or '',
                    'description': c.get('snippet') or '',
                    'url': c.get('url') or '',
                    'source': c.get('source') or '',
                    'published_at': None,
                    'content': c.get('snippet') or ''
                })

            return {'articles': articles, 'source': 'perplexity', 'total_found': len(articles)}
        else:
            # Fallback to older news-style Perplexity search
            result = await news_research_service._search_perplexity_news(query, max_results)
            return result
    except Exception as e:
        logger.warning(f"Perplexity search failed: {e}")
        # Return empty results instead of failing completely
        return {"articles": []}


async def _search_google(query: str, max_results: int, language: str) -> dict[str, Any]:
    """Search using Google Custom Search."""
    logger.info(f"Searching Google for: {query}")
    
    try:
        import aiohttp
        import os
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Get credentials from news_research_service or environment variables
        google_api_key = news_research_service.google_api_key or os.getenv('GOOGLE_SEARCH_API_KEY')
        google_search_engine_id = news_research_service.google_search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not google_api_key or not google_search_engine_id:
            logger.warning(f"Google Search not fully configured. GOOGLE_SEARCH_API_KEY present: {bool(google_api_key)}, GOOGLE_SEARCH_ENGINE_ID present: {bool(google_search_engine_id)}. Please set these environment variables to enable Google Search.")
            return {"articles": []}
        
        # General web search (no "news" appended)
        params = {
            'key': google_api_key,
            'cx': google_search_engine_id,
            'q': query,  # Use query directly without appending "news"
            'num': min(10, max_results),
            'lr': f'lang_{language}',
            'sort': 'date'
        }
        
        logger.info(f"Google Search params: {params}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])
                    logger.info(f"Google Search returned {len(items)} items for query: {query}")
                    
                    articles = []
                    for item in items:
                        article = {
                            'title': item.get('title', ''),
                            'description': item.get('snippet', ''),
                            'url': item.get('link', ''),
                            'source': item.get('displayLink', 'Google Search'),
                            'published_at': None,
                            'content': item.get('snippet', '')
                        }
                        if article['title'] and article['url']:
                            articles.append(article)
                    
                    return {"articles": articles}
                else:
                    error_text = await response.text()
                    logger.warning(f"Google Search API returned {response.status}: {error_text}")
                    return {"articles": []}
                    
    except Exception as e:
        logger.warning(f"Google search failed: {e}")
        return {"articles": []}


@router.get("/web/engines")
async def get_search_engines(_: dict[str, Any] = Depends(get_current_user)):
    """Get available search engines and their features."""
    return {
        "available_engines": [
            {
                "name": "perplexity",
                "display_name": "Perplexity AI",
                "description": "AI-powered comprehensive search with analysis",
                "features": [
                    "Real-time web search",
                    "AI-powered synthesis",
                    "Citation sources",
                    "Comprehensive analysis"
                ],
                "max_results": 50,
                "languages_supported": ["en"]
            },
            {
                "name": "google",
                "display_name": "Google Search",
                "description": "Traditional web search results from Google",
                "features": [
                    "Fast results",
                    "Large index",
                    "News filtering",
                    "Date range support"
                ],
                "max_results": 50,
                "languages_supported": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
            }
        ],
        "default_engine": "perplexity",
        "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
    }
