"""
Routes for AI-powered structured data extraction using Google Langextract.

This module provides endpoints for extracting structured information from unstructured text
using large language models (LLMs) with source grounding and interactive visualization.
"""
import os
import uuid
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.responses import JSONResponse

from app.utils.auth import get_current_user
from app.services.documents.langextract_service import langextract_service
from app.services.job_queue import job_queue
from app.models import (
    JobResponse, JobType,
    LangextractRequest, LangextractResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/langextract", tags=["Content Tools"])


@router.get("/models")
async def get_supported_models():
    """Get supported AI models and extraction capabilities for Langextract."""
    return langextract_service.get_supported_models()


async def process_langextract_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for Langextract data extraction job processing."""
    return await langextract_service.extract_structured_data(data)


@router.post("/", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def extract_structured_data(
    input_text: str = Form(None, description="Direct text input for data extraction (optional)"),
    file: UploadFile = File(None, description="Document file for data extraction (PDF, DOCX, TXT, HTML) - alternative to text/URL"),
    file_url: str = Form(None, description="URL of document file for data extraction - alternative to text/file"),
    extraction_schema: str = Form('{"entities": ["person", "organization", "location"], "relationships": ["works_for", "located_in"]}', 
                                  description="JSON schema defining what to extract"),
    extraction_prompt: str = Form("Extract all people, organizations, and locations from the text. Also identify relationships between entities.",
                                  description="Custom prompt for extraction (used if use_custom_prompt=true)"),
    use_custom_prompt: bool = Form(False, description="Use custom prompt (true) or JSON schema (false)"),
    model: str = Form("gemini", description="AI model to use: 'gemini' (primary) or 'openai' (fallback)"),
    _: Dict[str, Any] = Depends(get_current_user),  # API key validation
):
    """
    Extract structured data from text, file, or URL using AI (Gemini or OpenAI).

    Supports schema-based or prompt-based extraction with source grounding.
    Accepts direct text, file upload, or URL input. Returns a job_id for async polling.
    """
    try:
        # Check if Langextract service is available
        if not langextract_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Langextract service is not available. Please install 'langextract>=1.0.5' package."
            )
        
        # Validate input parameters - at least one input method required
        if not input_text and not file and not file_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one input method must be provided: input_text, file, or file_url"
            )
        
        # Validate only one input method is used
        input_count = sum(bool(x) for x in [input_text, file, file_url])
        if input_count > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide only one input method: input_text, file, or file_url"
            )
        
        # Validate model parameter
        if model not in ["gemini", "openai"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model must be 'gemini' or 'openai'"
            )
        
        # Check API key availability for selected model
        if model == "gemini" and not os.getenv('GEMINI_API_KEY'):
            if not os.getenv('OPENAI_API_KEY'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured"
                )
            else:
                logger.warning("GEMINI_API_KEY not found, will fallback to OpenAI")
                model = "openai"
        elif model == "openai" and not os.getenv('OPENAI_API_KEY'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OPENAI_API_KEY is required for OpenAI model"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        job_data = {
            "input_text": input_text,
            "extraction_schema": extraction_schema,
            "extraction_prompt": extraction_prompt,
            "use_custom_prompt": use_custom_prompt,
            "model": model
        }
        
        if file:
            # Handle file upload
            if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit for text extraction
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds 10MB limit for data extraction"
                )
            
            # Validate file type by extension
            if file.filename:
                allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.html', '.htm'}
                file_ext = os.path.splitext(file.filename.lower())[1]
                if file_ext not in allowed_extensions:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported file type '{file_ext}'. Supported: {', '.join(allowed_extensions)}"
                    )
            
            # Process file immediately to avoid storing binary data in job params
            file_content = await file.read()
            job_data["input_filename"] = file.filename or "uploaded_document"
            
            # Create wrapper that processes binary data directly
            async def process_langextract_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await langextract_service.process_extraction_with_file_data(
                    file_content=file_content,
                    params=data
                )
        elif file_url:
            # Handle URL input
            job_data["file_url"] = file_url
            job_data["input_filename"] = os.path.basename(file_url) or "document_from_url"
            
            # Create wrapper for URL-based processing
            async def process_langextract_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await langextract_service.extract_structured_data(data)
        else:
            # Handle direct text input
            job_data["input_filename"] = "direct_text_input"
            
            # Create wrapper for text processing
            async def process_langextract_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await langextract_service.extract_structured_data(data)
        
        # Queue the job using consistent pattern
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.LANGEXTRACT_DATA_EXTRACTION,
            process_func=process_langextract_wrapper,
            data=job_data
        )
        
        logger.info(f"Created Langextract extraction job {job_id} with model {model} for: {job_data.get('input_filename', 'unknown')}")
        
        return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Langextract extraction job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create data extraction job"
        )


@router.post("/json")
async def extract_structured_data_json(
    request: LangextractRequest,
    _: Dict[str, Any] = Depends(get_current_user)
):
    """
    Extract structured data from text via JSON request body.

    Supports sync mode (immediate result for small texts) and async mode (job-based).
    For file uploads, use the multipart form endpoint instead.
    """
    # Handle sync mode
    if request.sync:
        try:
            # Check if Langextract service is available
            if not langextract_service.is_available():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Langextract service is not available. Please install 'langextract>=1.0.5' package."
                )

            # Validate input
            if not request.input_text and not request.file_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either input_text or file_url is required for synchronous extraction"
                )

            # Check text length for synchronous processing
            if request.input_text and len(request.input_text) > 5000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Text too long for synchronous processing (max 5000 characters). Use async mode."
                )

            # Prepare extraction data
            extraction_data = {
                "input_text": request.input_text,
                "file_url": str(request.file_url) if request.file_url else None,
                "extraction_schema": request.extraction_schema,
                "extraction_prompt": request.extraction_prompt,
                "use_custom_prompt": request.use_custom_prompt,
                "model": request.model,
                "input_filename": "synchronous_extraction"
            }

            # Process synchronously
            result = await langextract_service.extract_structured_data(extraction_data)

            logger.info(f"Synchronous Langextract extraction completed with {result['total_extractions']} extractions")

            return LangextractResult(**result)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Synchronous Langextract extraction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data extraction failed: {str(e)}"
            )

    # Handle async mode (default)
    try:
        # Check if Langextract service is available
        if not langextract_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Langextract service is not available. Please install 'langextract>=1.0.5' package."
            )

        # Validate input
        if not request.input_text and not request.file_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either input_text or file_url is required"
            )

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Prepare extraction data
        extraction_data = {
            "input_text": request.input_text,
            "file_url": str(request.file_url) if request.file_url else None,
            "extraction_schema": request.extraction_schema,
            "extraction_prompt": request.extraction_prompt,
            "use_custom_prompt": request.use_custom_prompt,
            "model": request.model,
            "input_filename": f"async_extraction_{job_id}"
        }

        # Add job to queue
        await job_queue.add_job(
            job_id=job_id,
            job_type=JobType.LANGEXTRACT,
            process_func=process_langextract_wrapper,
            data=extraction_data
        )

        logger.info(f"Created Langextract job {job_id}")

        return JobResponse(job_id=job_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Langextract job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data extraction job: {str(e)}"
        )