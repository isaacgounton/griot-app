"""
Postiz integration routes for social media scheduling.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from loguru import logger

from app.utils.auth import get_current_user
from app.services.postiz import postiz_service
from app.services.job_queue import job_queue
from app.services.s3.s3_service import s3_upload_service
from app.services.ai.unified_ai_service import UnifiedAIService
from app.models import JobStatus


router = APIRouter(prefix="/postiz", tags=["System"])


class PostizIntegrationResponse(BaseModel):
    """Response model for Postiz integrations."""
    id: str
    name: str
    provider: str


class SchedulePostRequest(BaseModel):
    """Request model for scheduling a post."""
    content: str = Field(..., description="Post content text")
    integrations: List[str] = Field(..., description="List of integration IDs to post to")
    post_type: str = Field(default="now", description="Post type: now, schedule, or draft")
    schedule_date: Optional[datetime] = Field(None, description="Schedule date for scheduled posts")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the post")
    media_urls: Optional[List[str]] = Field(None, description="Optional media URLs to attach to the post")


class ScheduleJobPostRequest(BaseModel):
    """Request model for scheduling a post from a completed job."""
    job_id: str = Field(..., description="ID of the completed job")
    content: Optional[str] = Field(None, description="Custom post content (uses suggested if not provided)")
    integrations: List[str] = Field(..., description="List of integration IDs to post to")
    post_type: str = Field(default="now", description="Post type: now, schedule, or draft")
    schedule_date: Optional[datetime] = Field(None, description="Schedule date for scheduled posts")
    tags: Optional[List[str]] = Field(None, description="Optional tags for the post")


class PostizResponse(BaseModel):
    """Generic Postiz API response."""
    success: bool
    message: str
    data: Optional[dict] = None


@router.get("/integrations", response_model=List[PostizIntegrationResponse])
async def get_integrations(_: Dict[str, Any] = Depends(get_current_user)):
    """Get available Postiz social media integrations."""
    try:
        integrations = await postiz_service.get_integrations()
        return [
            PostizIntegrationResponse(
                id=integration.id,
                name=integration.name,
                provider=integration.provider
            )
            for integration in integrations
        ]
    except HTTPException:
        raise
    except ValueError as e:
        # Handle configuration errors (like missing API key)
        logger.error(f"Postiz configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Postiz configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get Postiz integrations: {e}")
        # Provide more specific error message
        error_msg = str(e)
        if "401" in error_msg or "Invalid API key" in error_msg:
            raise HTTPException(status_code=500, detail="Invalid Postiz API key. Please check your POSTIZ_API_KEY environment variable.")
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            raise HTTPException(status_code=500, detail="Failed to connect to Postiz API. Please check your POSTIZ_API_URL.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get integrations: {error_msg}")


@router.post("/schedule", response_model=PostizResponse)
async def schedule_post(request: SchedulePostRequest, _: Dict[str, Any] = Depends(get_current_user)):
    """Schedule a post to social media platforms."""
    try:
        if request.post_type == "schedule" and not request.schedule_date:
            raise HTTPException(status_code=400, detail="Schedule date is required for scheduled posts")
        
        result = await postiz_service.schedule_post(
            content=request.content,
            integrations=request.integrations,
            post_type=request.post_type,
            schedule_date=request.schedule_date,
            media_paths=request.media_urls,
            tags=request.tags
        )

        # Store in post history
        postiz_service.add_to_post_history({
            "content": request.content,
            "integrations": request.integrations,
            "post_type": request.post_type,
            "media_urls": request.media_urls,
            "tags": request.tags,
            "response_data": result
        })

        return PostizResponse(
            success=True,
            message="Post scheduled successfully",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule post: {str(e)}")


@router.post("/schedule-job", response_model=PostizResponse)
async def schedule_job_post(request: ScheduleJobPostRequest, _: Dict[str, Any] = Depends(get_current_user)):
    """Schedule a post from a completed job result."""
    try:
        # Get the job information
        job_info = await job_queue.get_job_info(request.job_id)
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status_value = job_info.status.value if isinstance(job_info.status, JobStatus) else job_info.status
        if status_value != "completed":
            raise HTTPException(status_code=400, detail="Job must be completed to schedule")
        
        # Check if job has scheduling information
        scheduling_info = None
        if isinstance(job_info.result, dict) and "scheduling" in job_info.result:
            scheduling_info = job_info.result["scheduling"]
        
        # If no explicit scheduling info, check if job has media content that can be scheduled
        if not scheduling_info or not scheduling_info.get("available"):
            # Check if this is a video/image/audio job with media content
            schedulable_operations = [
                'footage_to_video', 'aiimage_to_video', 'scenes_to_video',
                'short_video_creation', 'image_to_video', 'image_generation', 'audio_generation',
                'youtube_shorts'
            ]
            
            has_media_content = False
            if isinstance(job_info.result, dict):
                # Check for video, image, or audio URLs
                media_keys = [
                    'final_video_url', 'video_url', 'video_with_audio_url',
                    'image_url', 'thumbnail_url', 'audio_url', 'file_url'
                ]
                has_media_content = any(
                    key in job_info.result and job_info.result[key]
                    for key in media_keys
                )
            
            # Allow scheduling if it's a schedulable operation with media content
            operation = getattr(job_info, 'job_type', '').lower()
            if not (operation in schedulable_operations and has_media_content):
                raise HTTPException(status_code=400, detail="Job is not available for scheduling")
            
            # Create temporary scheduling info for jobs without explicit metadata
            content_type = "unknown"
            if isinstance(job_info.result, dict):
                video_keys = ['final_video_url', 'video_url']
                result_dict = job_info.result  # Type narrowing for Pylance
                content_type = "video" if any(k in result_dict for k in video_keys) else "unknown"
            
            scheduling_info = {
                "available": True,
                "content_type": content_type,
                "suggested_content": f"✨ Check out this amazing {operation.replace('_', ' ')} creation! #AI #automation #creation"
            }
        
        # Use custom content or suggested content
        content = request.content
        if not content:
            content = scheduling_info.get("suggested_content", "Check out this amazing creation!")
        
        # Handle media content from job result
        media_url = None
        media_type = None
        if isinstance(job_info.result, dict):
            # Look for various possible media URL fields (prioritize video URLs)
            video_keys = ["final_video_url", "video_url", "video_with_audio_url"]
            image_keys = ["image_url", "thumbnail_url"]
            audio_keys = ["audio_url"]
            other_keys = ["file_url"]

            # For YouTube Shorts jobs, the video URL is stored as "url"
            if operation == "youtube_shorts" and "url" in job_info.result:
                video_keys.append("url")
            else:
                other_keys.append("url")

            # Check for video content first
            for key in video_keys:
                if key in job_info.result and job_info.result[key]:
                    media_url = job_info.result[key]
                    media_type = "video"
                    break
            
            # Then check for images
            if not media_url:
                for key in image_keys:
                    if key in job_info.result and job_info.result[key]:
                        media_url = job_info.result[key]
                        media_type = "image"
                        break
            
            # Then check for audio
            if not media_url:
                for key in audio_keys:
                    if key in job_info.result and job_info.result[key]:
                        media_url = job_info.result[key]
                        media_type = "audio"
                        break
            
            # Finally check other URLs
            if not media_url:
                for key in other_keys:
                    if key in job_info.result and job_info.result[key]:
                        media_url = job_info.result[key]
                        media_type = "unknown"
                        break
        
        if request.post_type == "schedule" and not request.schedule_date:
            raise HTTPException(status_code=400, detail="Schedule date is required for scheduled posts")
        
        # Choose the appropriate scheduling method based on media type
        if media_url and media_type == "video":
            result = await postiz_service.schedule_video_post(
                video_url=media_url,
                content=content,
                integrations=request.integrations,
                post_type=request.post_type,
                schedule_date=request.schedule_date,
                tags=request.tags
            )
        elif media_url and media_type == "image":
            # For images, download and upload as attachment
            result = await postiz_service.schedule_post(
                content=content,
                integrations=request.integrations,
                post_type=request.post_type,
                schedule_date=request.schedule_date,
                media_paths=[media_url] if media_url.startswith('http') else None,
                tags=request.tags
            )
        else:
            # For other content types or no media, use regular posting
            result = await postiz_service.schedule_post(
                content=content,
                integrations=request.integrations,
                post_type=request.post_type,
                schedule_date=request.schedule_date,
                tags=request.tags
            )
        
        return PostizResponse(
            success=True,
            message=f"Post from job {request.job_id} scheduled successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule job post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule job post: {str(e)}")


@router.post("/schedule-now", response_model=PostizResponse)
async def schedule_post_now(request: SchedulePostRequest, _: Dict[str, Any] = Depends(get_current_user)):
    """Schedule a post to be published immediately."""
    try:
        result = await postiz_service.schedule_post_now(
            content=request.content,
            integrations=request.integrations,
            media_paths=request.media_urls,
            tags=request.tags
        )

        # Store in post history
        postiz_service.add_to_post_history({
            "content": request.content,
            "integrations": request.integrations,
            "post_type": "now",
            "media_urls": request.media_urls,
            "tags": request.tags,
            "response_data": result
        })

        return PostizResponse(
            success=True,
            message="Post published successfully",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish post: {str(e)}")


@router.post("/create-draft", response_model=PostizResponse)
async def create_draft_post(request: SchedulePostRequest, _: Dict[str, Any] = Depends(get_current_user)):
    """Create a draft post."""
    try:
        result = await postiz_service.create_draft_post(
            content=request.content,
            integrations=request.integrations,
            media_paths=request.media_urls,
            tags=request.tags
        )

        # Store in post history
        postiz_service.add_to_post_history({
            "content": request.content,
            "integrations": request.integrations,
            "post_type": "draft",
            "media_urls": request.media_urls,
            "tags": request.tags,
            "response_data": result
        })

        return PostizResponse(
            success=True,
            message="Draft post created successfully",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create draft: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create draft: {str(e)}")


@router.get("/job/{job_id}/scheduling-info")
async def get_job_scheduling_info(job_id: str, _: Dict[str, Any] = Depends(get_current_user)):
    """Get scheduling information for a completed job."""
    try:
        job_info = await job_queue.get_job_info(job_id)
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")
        
        scheduling_info = None
        if isinstance(job_info.result, dict) and "scheduling" in job_info.result:
            scheduling_info = job_info.result["scheduling"]
        
        return {
            "job_id": job_id,
            "job_status": job_info.status.value if isinstance(job_info.status, JobStatus) else job_info.status,
            "scheduling_available": scheduling_info.get("available", False) if scheduling_info else False,
            "content_type": scheduling_info.get("content_type", "unknown") if scheduling_info else "unknown",
            "suggested_content": scheduling_info.get("suggested_content", "") if scheduling_info else "",
            "marked_at": scheduling_info.get("marked_at") if scheduling_info else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job scheduling info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduling info: {str(e)}")


@router.get("/history", response_model=List[dict])
async def get_post_history(_: Dict[str, Any] = Depends(get_current_user)):
    """Get post history."""
    try:
        return postiz_service.get_post_history()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get post history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get post history: {str(e)}")


class AttachmentUploadResponse(BaseModel):
    """Response model for attachment upload."""
    success: bool
    message: str
    url: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None


@router.post("/upload-attachment", response_model=AttachmentUploadResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    public: Optional[str] = Form("true"),
    _: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload a file attachment for social media posts.

    This endpoint handles file uploads for social media attachments, storing them in S3
    and returning a URL that can be used in post creation endpoints.

    Parameters:
    - file: File to upload (image, audio, or video)
    - public: Whether the file should be publicly accessible (default: true)

    Returns:
    - success: Whether the upload was successful
    - url: Public URL of the uploaded file
    - filename: Original filename
    - size: File size in bytes
    - mime_type: MIME type of the uploaded file
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        if file.size == 0:
            raise HTTPException(status_code=400, detail="File cannot be empty")

        # Validate file type (allow images, audio, and video)
        allowed_mime_types = [
            # Images
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
            # Audio
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/flac',
            # Video
            'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime', 'video/x-msvideo'
        ]

        if file.content_type not in allowed_mime_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed. Supported types: images, audio, and video files"
            )

        # Convert public parameter to boolean
        is_public = public.lower() in ('true', '1', 'yes') if public else True

        logger.info(f"Uploading attachment: {file.filename}, size: {file.size}, type: {file.content_type}")

        # Upload to S3 synchronously
        file_content = await file.read()
        result = await s3_upload_service.process_s3_upload_direct(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type,
            public=is_public
        )

        logger.info(f"Successfully uploaded attachment: {file.filename} -> {result.get('file_url', 'unknown')}")

        return AttachmentUploadResponse(
            success=True,
            message="File uploaded successfully",
            url=result.get('file_url'),  # S3 service returns 'file_url', not 'url'
            filename=result.get('file_name', file.filename),
            size=result.get('file_size', file.size),
            mime_type=result.get('mime_type', file.content_type)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload attachment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


# Initialize Unified AI service
unified_ai = UnifiedAIService()


class GenerateContentRequest(BaseModel):
    """Request model for AI-generated social media content."""
    job_id: str = Field(..., description="ID of the completed job to generate content for")
    user_instructions: Optional[str] = Field(None, description="Optional user instructions for content generation")
    content_style: Optional[str] = Field("engaging", description="Style of content: engaging, professional, casual, viral, educational")
    platform: Optional[str] = Field("general", description="Target platform: general, twitter, instagram, linkedin, tiktok")
    max_length: Optional[int] = Field(None, description="Maximum length of generated content")


class GeneratedContentResponse(BaseModel):
    """Response model for AI-generated content."""
    success: bool
    content: str
    tags: List[str] = []
    metadata: Optional[dict] = None


@router.post("/generate-content", response_model=GeneratedContentResponse)
async def generate_social_media_content(
    request: GenerateContentRequest,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate AI-powered social media content for a completed job.

    This endpoint uses the original content context (script, topic, etc.) from the job
    to generate engaging social media post content using AI.
    """
    try:
        # Get the job information
        job_info = await job_queue.get_job_info(request.job_id)
        if not job_info:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if job is completed
        status_value = job_info.status.value if isinstance(job_info.status, JobStatus) else job_info.status
        if status_value != "completed":
            raise HTTPException(status_code=400, detail="Job must be completed to generate content")

        # Extract content context from job result
        context_data = {}
        if isinstance(job_info.result, dict):
            result_dict = job_info.result

            # Extract various context fields
            context_data = {
                "script": result_dict.get("script_generated") or result_dict.get("script") or result_dict.get("generated_script"),
                "topic": result_dict.get("topic_used") or result_dict.get("topic"),
                "title": result_dict.get("title"),
                "description": result_dict.get("description"),
                "scenes": result_dict.get("scenes"),
                "tags": result_dict.get("tags"),
                "content_type": "unknown",
                "has_video": bool(result_dict.get("final_video_url") or result_dict.get("video_url")),
                "has_image": bool(result_dict.get("image_url")),
                "has_audio": bool(result_dict.get("audio_url")),
            }

            # Determine content type
            if context_data["has_video"]:
                context_data["content_type"] = "video"
            elif context_data["has_image"]:
                context_data["content_type"] = "image"
            elif context_data["has_audio"]:
                context_data["content_type"] = "audio"

        # Build AI prompt based on context and user instructions
        prompt = _build_generation_prompt(
            context_data=context_data,
            job_operation=getattr(job_info, 'job_type', 'content creation'),
            user_instructions=request.user_instructions,
            content_style=request.content_style,
            platform=request.platform,
            max_length=request.max_length
        )

        logger.info(f"Generating social media content for job {request.job_id}")

        # Use Unified AI service to generate content with tags
        messages = [
            {
                "role": "system",
                "content": "You are an expert social media content creator. Generate engaging, compelling social media posts that capture attention and drive engagement. Always include relevant hashtags in the content and suggest additional tags."
            },
            {
                "role": "user",
                "content": f"{prompt}\n\nIMPORTANT: After the post content, on a new line, add 'TAGS: ' followed by 3-5 relevant tags (without # symbol) separated by commas."
            }
        ]

        # Generate content using unified AI with automatic provider selection
        response = await unified_ai.create_chat_completion(
            messages=messages,
            provider="auto",  # Automatically selects best available provider
            temperature=0.8,
            max_tokens=request.max_length or 600  # Increased for tags
        )

        # Extract generated content
        generated_text = response.get("content", "")
        if not generated_text:
            raise ValueError("No content generated from AI")

        # Parse content and tags
        content, extracted_tags = _parse_content_and_tags(generated_text)

        logger.info(f"Successfully generated content for job {request.job_id} using {response.get('provider', 'unknown')}, extracted {len(extracted_tags)} tags")

        return GeneratedContentResponse(
            success=True,
            content=content.strip(),
            tags=extracted_tags,
            metadata={
                "job_id": request.job_id,
                "provider": response.get("provider", "auto"),
                "model": response.get("model", "unknown"),
                "content_type": context_data.get("content_type"),
                "platform": request.platform,
                "style": request.content_style
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


def _parse_content_and_tags(generated_text: str) -> tuple[str, list[str]]:
    """
    Parse the AI-generated text to extract content and tags.

    The AI is instructed to include 'TAGS: tag1, tag2, tag3' on a new line.
    This function also extracts hashtags from the content as fallback.

    Args:
        generated_text: Raw text from AI

    Returns:
        Tuple of (content, tags_list)
    """
    import re

    tags = []
    content = generated_text

    # Try to extract explicitly provided tags (TAGS: format)
    tags_match = re.search(r'TAGS:\s*([^\n]+)', generated_text, re.IGNORECASE)
    if tags_match:
        # Remove the TAGS line from content
        content = re.sub(r'\n*TAGS:\s*[^\n]+\n*', '\n', generated_text, flags=re.IGNORECASE).strip()

        # Extract tags
        tags_text = tags_match.group(1)
        tags = [tag.strip().replace('#', '') for tag in tags_text.split(',') if tag.strip()]

    # Also extract hashtags from content as additional tags
    hashtag_pattern = r'#(\w+)'
    hashtags = re.findall(hashtag_pattern, content)

    # Combine explicit tags and hashtags, removing duplicates while preserving order
    all_tags = tags + hashtags
    seen = set()
    unique_tags = []
    for tag in all_tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)

    return content, unique_tags[:10]  # Limit to 10 tags


def _build_generation_prompt(
    context_data: dict,
    job_operation: str,
    user_instructions: Optional[str],
    content_style: str,
    platform: str,
    max_length: Optional[int]
) -> str:
    """Build the AI prompt for content generation with all available context."""

    # Platform-specific guidelines
    platform_guidelines = {
        "twitter": "Keep it concise (under 280 characters), use relevant hashtags, make it conversational.",
        "instagram": "Make it visual and engaging, use 3-5 hashtags, include a call-to-action.",
        "linkedin": "Professional tone, add value, share insights, keep it business-focused.",
        "tiktok": "Fun and energetic, use trending sounds/hashtags, create curiosity.",
        "general": "Engaging and shareable across platforms, use 2-3 relevant hashtags."
    }

    # Style guidelines
    style_guidelines = {
        "engaging": "Create content that hooks attention immediately and encourages interaction.",
        "professional": "Maintain a polished, authoritative tone suitable for business contexts.",
        "casual": "Use a friendly, conversational tone that feels approachable.",
        "viral": "Make it shareable, surprising, or emotionally resonant to maximize reach.",
        "educational": "Inform and teach while keeping it digestible and interesting."
    }

    # Build context section
    context_parts = []

    if context_data.get("topic"):
        context_parts.append(f"Topic: {context_data['topic']}")

    if context_data.get("title"):
        context_parts.append(f"Title: {context_data['title']}")

    if context_data.get("script"):
        # Truncate script if too long
        script = context_data["script"]
        if len(script) > 500:
            script = script[:500] + "..."
        context_parts.append(f"Script/Content:\n{script}")

    if context_data.get("description"):
        context_parts.append(f"Description: {context_data['description']}")

    # Add content type
    content_type = context_data.get("content_type", "content")
    context_parts.append(f"Media Type: {content_type}")

    # Build the complete prompt
    prompt_parts = [
        f"Generate a {content_style} social media post for {platform}.",
        "",
        "Context about the content:",
        *context_parts,
        "",
        f"Style: {style_guidelines.get(content_style, style_guidelines['engaging'])}",
        f"Platform: {platform_guidelines.get(platform, platform_guidelines['general'])}",
    ]

    if max_length:
        prompt_parts.append(f"Maximum length: {max_length} characters")

    if user_instructions:
        prompt_parts.append(f"\nUser instructions: {user_instructions}")

    prompt_parts.extend([
        "",
        "Generate the social media post now. Only return the post content, no explanations or meta-commentary."
    ])

    return "\n".join(prompt_parts)
