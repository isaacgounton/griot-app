"""
Route for URL to Markdown conversion.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.auth import get_current_user
from app.services.documents.url_to_markdown_service import url_to_markdown_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Documents"])


class UrlToMarkdownRequest(BaseModel):
    url: str = Field(..., description="Web page URL to convert")
    use_browser: bool = Field(False, description="Use Browserless for JS-rendered pages")
    article_only: bool = Field(False, description="Extract only article content (strip nav/ads/boilerplate)")
    include_metadata: bool = Field(True, description="Include title, author, date")


class UrlToMarkdownResponse(BaseModel):
    title: str = ""
    author: str = ""
    date: str = ""
    description: str = ""
    sitename: str = ""
    markdown: str
    word_count: int
    source_url: str


@router.post("/", response_model=UrlToMarkdownResponse)
async def url_to_markdown(
    request: UrlToMarkdownRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """
    Convert a web page URL to structured Markdown.

    By default converts the full page. Enable `article_only` to extract
    only the article content (strips navigation, ads, and boilerplate).
    """
    try:
        result = await url_to_markdown_service.convert(
            url=request.url,
            use_browser=request.use_browser,
            article_only=request.article_only,
            include_metadata=request.include_metadata,
        )
        return UrlToMarkdownResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("URL to markdown failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
