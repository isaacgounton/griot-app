"""
Article to Script route — converts a web article URL into a video script.

Chains: URL → markdown extraction → script generation.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.auth import get_current_user
from app.services.documents.url_to_markdown_service import url_to_markdown_service
from app.services.text.script_generator import script_generator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Text Generation"])


class ArticleToScriptRequest(BaseModel):
    url: str = Field(..., description="Web page URL of the article")
    script_type: str = Field("educational", description="Script type (educational, facts, story, etc.)")
    max_duration: int = Field(60, ge=15, le=300, description="Max script duration in seconds")
    language: str = Field("english", description="Output language")
    use_browser: bool = Field(False, description="Use Browserless for JS-rendered pages")


class ArticleToScriptResponse(BaseModel):
    script: str
    article_title: str = ""
    article_word_count: int = 0
    script_word_count: int = 0
    source_url: str = ""
    script_type: str = ""


@router.post("/article-to-script", response_model=ArticleToScriptResponse)
async def article_to_script(
    request: ArticleToScriptRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """
    Convert a web article into a video script.

    Extracts article content from the URL, then generates a script
    based on the article content using the specified script type and duration.
    """
    # Step 1: Extract article
    try:
        article = await url_to_markdown_service.convert(
            url=request.url,
            use_browser=request.use_browser,
            article_only=True,
            include_metadata=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Article extraction failed: {e}")
    except Exception as e:
        logger.error("Article extraction error: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to extract article: {e}")

    article_markdown = article.get("markdown", "")
    article_title = article.get("title", "")

    # Step 2: Generate script from article content
    # Pass article content as topic with context prefix
    topic = (
        f"Based on this article titled '{article_title}':\n\n"
        f"{article_markdown}\n\n"
        f"Create a {request.script_type} script summarizing the key points of this article."
    )

    # Truncate if too long (LLM context limits)
    if len(topic) > 6000:
        topic = topic[:6000] + "\n\n[Article truncated for length]"

    try:
        result = await script_generator.generate_script({
            "topic": topic,
            "script_type": request.script_type,
            "max_duration": request.max_duration,
            "language": request.language,
        })
    except Exception as e:
        logger.error("Script generation error: %s", e)
        raise HTTPException(status_code=500, detail=f"Script generation failed: {e}")

    script_text = result.get("script", "") if isinstance(result, dict) else str(result)

    return ArticleToScriptResponse(
        script=script_text,
        article_title=article_title,
        article_word_count=article.get("word_count", 0),
        script_word_count=len(script_text.split()),
        source_url=request.url,
        script_type=request.script_type,
    )
