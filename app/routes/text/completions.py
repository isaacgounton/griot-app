"""Text generation API routes for scripts, prompts, and content."""

import uuid
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.text.script_generator import script_generator
from app.services.text.image_prompt_generator import image_prompt_generator
from app.services.text.topic_discovery_service import topic_discovery_service
from app.services.job_queue import job_queue
from app.services.ai.unified_ai_service import unified_ai_service
from app.models import JobType, JobResponse
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/text", tags=["AI Content"])


class ScriptGenerationRequest(BaseModel):
    """Request model for script generation."""
    topic: str = Field(..., description="Topic or subject for the script")
    script_type: str = Field("facts", description="Type of script: facts, story, educational, promotional")
    language: str = Field("en", description="Language code (en, es, fr, de, etc.)")
    max_duration: int = Field(60, description="Maximum script duration in seconds")
    style: str = Field("engaging", description="Script style: engaging, formal, casual, dramatic")
    target_audience: str | None = Field(None, description="Target audience description")


class ImagePromptRequest(BaseModel):
    """Request model for image prompt generation."""
    topic: str = Field(..., description="Topic or subject for image generation")
    style: str = Field("realistic", description="Image style: realistic, artistic, cartoon, etc.")
    mood: str | None = Field(None, description="Desired mood or atmosphere")
    context: str | None = Field(None, description="Additional context for the image")


class TopicDiscoveryRequest(BaseModel):
    """Request model for topic discovery."""
    keywords: str = Field(..., description="Keywords to search for topics")
    category: str | None = Field(None, description="Category filter")
    language: str = Field("en", description="Language code")
    max_results: int = Field(10, description="Maximum number of topics to return")


class ScriptGenerationResponse(BaseModel):
    """Response model for script generation."""
    script: str
    title: str
    duration_estimate: int
    word_count: int


class ImagePromptResponse(BaseModel):
    """Response model for image prompt generation."""
    prompt: str
    style: str
    suggested_parameters: dict[str, Any]


class TopicDiscoveryResponse(BaseModel):
    """Response model for topic discovery."""
    topics: list[str]
    search_query: str
    total_found: int


class TextGenerationRequest(BaseModel):
    """Request model for general text generation."""
    prompt: str = Field(..., description="Text prompt for generation")
    max_tokens: int = Field(1000, description="Maximum tokens in response")
    temperature: float = Field(0.7, description="Creativity level 0.0-1.0")
    style: str = Field("general", description="Generation style: general, creative, formal, casual")
    provider: str | None = Field(None, description="AI provider: auto, pollinations, openai, groq")


class TextGenerationResponse(BaseModel):
    """Response model for general text generation."""
    content: str
    style: str
    word_count: int


@router.post("/generate/script", response_model=JobResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate a video script using AI. Supports multiple script types, languages, and styles."""
    try:
        # Create job data
        job_data = {
            "topic": request.topic,
            "script_type": request.script_type,
            "language": request.language,
            "max_duration": request.max_duration,
            "style": request.style,
            "target_audience": request.target_audience
        }

        # Create and queue the job
        job_id = str(uuid.uuid4())

        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.AI_SCRIPT_GENERATION,
            process_func=process_script_generation,
            data=job_data
        )

        logger.info(f"Created script generation job: {job_id}")
        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating script generation job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create script generation job: {str(e)}")


@router.post("/generate/image-prompt", response_model=ImagePromptResponse)
async def generate_image_prompt(
    request: ImagePromptRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate optimized prompts for AI image generation with style and parameter suggestions."""
    try:
        result = await image_prompt_generator.generate_prompt(
            topic=request.topic,
            style=request.style,
            mood=request.mood,
            context=request.context
        )

        return ImagePromptResponse(
            prompt=result["prompt"],
            style=result["style"],
            suggested_parameters=result.get("parameters", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image prompt: {str(e)}")


@router.post("/discover/topics", response_model=TopicDiscoveryResponse)
async def discover_topics(
    request: TopicDiscoveryRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Discover trending topics and content ideas based on keywords and categories."""
    try:
        result = await topic_discovery_service.discover_topics(
            keywords=request.keywords,
            category=request.category,
            language=request.language,
            max_results=request.max_results
        )

        return TopicDiscoveryResponse(
            topics=result["topics"],
            search_query=result["search_query"],
            total_found=result["total_found"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to discover topics: {str(e)}")


async def process_script_generation(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Process a script generation job."""
    try:
        result = await script_generator.generate_script(data)
        return result
    except Exception as e:
        logger.error(f"Error processing script generation job {job_id}: {str(e)}")
        raise


@router.post("/generate", response_model=TextGenerationResponse)
async def generate_text(
    request: TextGenerationRequest,
    _: dict[str, Any] = Depends(get_current_user)
):
    """Generate general text content using AI with configurable style and provider."""
    try:
        # Build system prompt based on style
        system_prompt = None
        if request.style == "creative":
            system_prompt = "You are a creative writer. Write engaging, imaginative content that captures attention and inspires."
        elif request.style == "formal":
            system_prompt = "You are a professional writer. Write in a formal, professional, and authoritative tone suitable for business contexts."
        elif request.style == "casual":
            system_prompt = "You are a friendly writer. Write in a casual, conversational, and approachable tone as if talking to a friend."
        else:
            system_prompt = "You are a helpful AI assistant. Provide clear, accurate, and useful responses."

        # Use unified AI service to generate text
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.prompt}
        ]
        
        response = await unified_ai_service.create_chat_completion(
            messages=messages,
            provider=request.provider or "auto",
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Extract the generated content
        content = response.get("content", "").strip()
        if not content:
            # Try to get from choices if response format is different
            choices = response.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "").strip()
        
        word_count = len(content.split()) if content else 0

        return TextGenerationResponse(
            content=content,
            style=request.style,
            word_count=word_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate text: {str(e)}")