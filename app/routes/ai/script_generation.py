import uuid
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.models import JobResponse, JobType
from app.services.job_queue import job_queue
from app.services.text.script_generator import script_generator
from app.services.text.topic_discovery_service import topic_discovery_service
from app.services.research.news_research_service import NewsResearchService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Content"])

logger = logging.getLogger(__name__)

# Language code to full name mapping
LANGUAGE_MAPPING: dict[str, str] = {
    'en': 'english', 'fr': 'french', 'es': 'spanish', 'de': 'german',
    'it': 'italian', 'pt': 'portuguese', 'ru': 'russian', 'zh': 'chinese',
    'ja': 'japanese', 'ko': 'korean', 'ar': 'arabic', 'hi': 'hindi',
    'tr': 'turkish', 'pl': 'polish', 'nl': 'dutch', 'sv': 'swedish',
    'da': 'danish', 'no': 'norwegian', 'fi': 'finnish', 'cs': 'czech',
    'hu': 'hungarian', 'ro': 'romanian', 'bg': 'bulgarian', 'hr': 'croatian',
    'sk': 'slovak', 'sl': 'slovenian', 'et': 'estonian', 'lv': 'latvian',
    'lt': 'lithuanian', 'mt': 'maltese', 'cy': 'welsh', 'ga': 'irish',
}


class NewsResearchRequest(BaseModel):
    searchTerm: str
    targetLanguage: str = "en"
    maxResults: int = 5


class ResearchTopicRequest(BaseModel):
    """Frontend-compatible research topic request."""
    searchTerm: str
    targetLanguage: str = "en"
    sync: bool = False


class FrontendScriptGenerationRequest(BaseModel):
    """Frontend-compatible script generation request."""
    topic: str
    script_type: str = "facts"
    language: str = "en"
    max_duration: int = 60
    style: str = "engaging"
    sync: bool = False
    provider: str = "auto"
    auto_topic: bool = False


# Initialize services
news_research_service = NewsResearchService()


async def process_script_generation_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for script generation job processing."""
    return await script_generator.generate_script(data)


def _build_script_data(request: FrontendScriptGenerationRequest, final_topic: str) -> dict[str, Any]:
    """Build job data dict from a script generation request."""
    script_language = LANGUAGE_MAPPING.get(request.language.lower(), request.language)
    return {
        "topic": final_topic,
        "script_type": request.script_type,
        "language": script_language,
        "max_duration": request.max_duration,
        "target_words": int(request.max_duration * 2.8),
        "provider": request.provider,
        "auto_topic": request.auto_topic,
    }


async def _resolve_topic(request: FrontendScriptGenerationRequest) -> str:
    """Resolve final topic, using auto-discovery if enabled."""
    final_topic = request.topic
    if request.auto_topic:
        logger.info("Auto-topic discovery enabled, discovering trending topic...")
        discovered = await topic_discovery_service.discover_topic(
            script_type=request.script_type,
            use_trending=True,
            language=request.language,
        )
        final_topic = discovered.get('topic', request.topic or f"{request.script_type} content")
        logger.info(f"Discovered trending topic: {final_topic}")

    if not request.auto_topic and not final_topic:
        raise HTTPException(
            status_code=400,
            detail="Topic is required (or enable auto_topic for automatic topic discovery)",
        )
    return final_topic


@router.post("/script-generation")
@router.post("/script/generate")
async def generate_script(
    request: FrontendScriptGenerationRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Generate a video script from a topic using AI. Supports sync and async modes."""
    if request.sync:
        try:
            final_topic = await _resolve_topic(request)
            script_data = _build_script_data(request, final_topic)
            return await script_generator.generate_script(script_data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate script: {str(e)}")

    # Async mode (default)
    job_id = str(uuid.uuid4())
    try:
        final_topic = await _resolve_topic(request)
        job_data = _build_script_data(request, final_topic)

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.AI_SCRIPT_GENERATION,
            process_func=process_script_generation_wrapper,
            data=job_data,
        )
        return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create script generation job: {str(e)}")


async def process_news_research_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for news research job processing."""
    search_term = data.get('searchTerm', '')
    max_results = data.get('maxResults', 5)
    return await news_research_service.research_topic(search_term, max_results)


@router.post("/news-research", response_model=JobResponse)
async def research_topic(
    request: NewsResearchRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Research a topic using news APIs to gather recent information for content creation."""
    job_id = str(uuid.uuid4())
    try:
        job_data = request.model_dump()
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.RESEARCH_NEWS,
            process_func=process_news_research_wrapper,
            data=job_data,
        )
        return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create research job: {str(e)}")


@router.post("/research-topic", response_model=JobResponse)
async def research_topic_frontend(
    request: ResearchTopicRequest,
    _: dict[str, Any] = Depends(get_current_user),
):
    """Research a topic (frontend-compatible endpoint)."""
    job_id = str(uuid.uuid4())
    try:
        job_data = {
            "searchTerm": request.searchTerm,
            "targetLanguage": request.targetLanguage,
            "maxResults": 5,
        }
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.RESEARCH_NEWS,
            process_func=process_news_research_wrapper,
            data=job_data,
        )
        return JobResponse(job_id=job_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create research job: {str(e)}")
