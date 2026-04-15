"""Search skill — web search, news, stock images and videos."""

from typing import Any

from app.services.tools.skills.base import Skill

skill = Skill(
    name="search",
    description="Web search, news search, stock image and video search",
)


# ---------------------------------------------------------------------------
# Web search
# ---------------------------------------------------------------------------

async def _web_search(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.research.news_research_service import news_research_service

    query = args["query"]
    max_results = args.get("max_results", 10)

    # Try Perplexity synthesis first (best results)
    try:
        result = await news_research_service._search_perplexity_synthesis(query, max_results)
        articles = result.get("articles", [])
        if articles:
            return {
                "results": [
                    {
                        "title": a.get("title", ""),
                        "content": a.get("content", a.get("description", "")),
                        "url": a.get("url", ""),
                        "source": a.get("source", ""),
                    }
                    for a in articles[:max_results]
                ]
            }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Perplexity synthesis failed, falling back: %s", e)

    # Fallback to regular research
    result = await news_research_service.research_news(
        query=query, max_results=max_results, language="en"
    )
    articles = result.get("articles", [])
    return {
        "results": [
            {
                "title": a.get("title", ""),
                "content": a.get("content", a.get("description", "")),
                "url": a.get("url", ""),
                "source": a.get("source", ""),
            }
            for a in articles[:max_results]
        ]
    }


skill.action(
    name="web_search",
    description=(
        "Search the web for information on any topic. Returns synthesized answers "
        "with source citations."
    ),
    handler=_web_search,
    properties={
        "query": {
            "type": "string",
            "description": "The search query",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return (1-20)",
            "default": 10,
        },
    },
    required=["query"],
)


# ---------------------------------------------------------------------------
# News search
# ---------------------------------------------------------------------------

async def _news_search(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.research.news_research_service import news_research_service

    result = await news_research_service.research_news(
        query=args["query"],
        language=args.get("language", "en"),
        max_results=args.get("max_results", 5),
        sort_by=args.get("sort_by", "relevance"),
    )
    articles = result.get("articles", [])
    return {
        "articles": [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", ""),
                "published_at": a.get("published_at", ""),
            }
            for a in articles
        ],
        "total": result.get("total_results", len(articles)),
    }


skill.action(
    name="news_search",
    description=(
        "Search for recent news articles on a topic. Returns news headlines, "
        "summaries, and source links."
    ),
    handler=_news_search,
    properties={
        "query": {
            "type": "string",
            "description": "The news search query",
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of articles (1-20)",
            "default": 5,
        },
        "sort_by": {
            "type": "string",
            "enum": ["relevance", "date", "popularity"],
            "description": "How to sort results",
            "default": "relevance",
        },
        "language": {
            "type": "string",
            "description": "Language code (e.g., 'en', 'fr')",
            "default": "en",
        },
    },
    required=["query"],
)


# ---------------------------------------------------------------------------
# Stock images
# ---------------------------------------------------------------------------

async def _search_stock_images(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.media.pexels_image_service import PexelsImageService

    svc = PexelsImageService()
    params: dict[str, Any] = {
        "query": args["query"],
        "per_page": args.get("per_page", 6),
    }
    if "orientation" in args:
        params["orientation"] = args["orientation"]

    result = await svc.search_images(params)
    images = result.get("images", [])
    return {
        "images": [
            {
                "url": img.get("url") or img.get("src", {}).get("large2x", ""),
                "thumbnail": img.get("thumbnail") or img.get("src", {}).get("medium", ""),
                "width": img.get("width"),
                "height": img.get("height"),
                "photographer": img.get("photographer", ""),
                "alt": img.get("alt", ""),
            }
            for img in images
        ],
        "total": result.get("total_results", len(images)),
    }


skill.action(
    name="search_stock_images",
    description=(
        "Search for professional stock photos. Returns image URLs with metadata."
    ),
    handler=_search_stock_images,
    properties={
        "query": {
            "type": "string",
            "description": "Search keywords for stock images",
        },
        "orientation": {
            "type": "string",
            "enum": ["landscape", "portrait", "square"],
            "description": "Image orientation filter",
        },
        "per_page": {
            "type": "integer",
            "description": "Number of results (1-20)",
            "default": 6,
        },
    },
    required=["query"],
)


# ---------------------------------------------------------------------------
# Stock videos
# ---------------------------------------------------------------------------

async def _search_stock_videos(args: dict[str, Any]) -> dict[str, Any]:
    from app.services.media.pexels_service import PexelsVideoService

    svc = PexelsVideoService()
    params: dict[str, Any] = {
        "query": args["query"],
        "per_page": args.get("per_page", 5),
    }
    if "orientation" in args:
        params["orientation"] = args["orientation"]

    result = await svc.search_videos(params)
    videos = result.get("videos", [])
    formatted = []
    for v in videos:
        video_files = v.get("video_files", [])
        video_url = ""
        for vf in video_files:
            if vf.get("quality") == "hd" or vf.get("width", 0) >= 1280:
                video_url = vf.get("link", "")
                break
        if not video_url and video_files:
            video_url = video_files[0].get("link", "")

        formatted.append({
            "url": video_url or v.get("url", ""),
            "thumbnail": v.get("image", ""),
            "width": v.get("width"),
            "height": v.get("height"),
            "duration": v.get("duration"),
        })
    return {"videos": formatted, "total": result.get("total_results", len(formatted))}


skill.action(
    name="search_stock_videos",
    description=(
        "Search for professional stock video footage. Returns video URLs with metadata."
    ),
    handler=_search_stock_videos,
    properties={
        "query": {
            "type": "string",
            "description": "Search keywords for stock videos",
        },
        "per_page": {
            "type": "integer",
            "description": "Number of results (1-10)",
            "default": 5,
        },
        "orientation": {
            "type": "string",
            "enum": ["landscape", "portrait", "square"],
            "description": "Video orientation filter",
        },
    },
    required=["query"],
)
