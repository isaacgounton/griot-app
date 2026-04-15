"""
Routes for document to Markdown conversion using Microsoft MarkItDown.

This module provides endpoints for converting various document formats 
(PDF, Word, Excel, PowerPoint, etc.) to Markdown format.
"""
import os
import uuid
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status
from fastapi.responses import JSONResponse

from app.utils.auth import get_current_user
from app.services.documents.markitdown_service import markitdown_service
from app.services.job_queue import job_queue
from app.models import (
    JobResponse, JobType,
    DocumentToMarkdownRequest, DocumentToMarkdownResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Content Tools"])


@router.get("/formats")
async def get_supported_formats():
    """Get supported document formats and conversion capabilities for MarkItDown."""
    return markitdown_service.get_supported_formats()


async def process_markdown_wrapper(job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrapper function for document to Markdown conversion job processing."""
    return await markitdown_service.process_document_to_markdown(data)


@router.post("/")
async def convert_document_to_markdown(
    file: UploadFile = File(None, description="Document file to convert (PDF, Word, Excel, etc.) - either file OR url required"),
    url: str = Form(None, description="URL of document file to convert - either file OR url required"),
    include_metadata: bool = Form(True, description="Whether to include document metadata in output"),
    preserve_formatting: bool = Form(True, description="Whether to preserve document formatting like tables and lists"),
    cookies_url: str = Form(None, description="URL to download cookies file for YouTube/restricted content access"),
    sync: bool = Form(False, description="If True, return response immediately. If False (default), create async job"),
    _: Dict[str, Any] = Depends(get_current_user),  # API key validation
):
    """
    Convert documents to Markdown format using Microsoft MarkItDown.

    Supports PDF, Word, Excel, PowerPoint, HTML, images (OCR), audio, and video files.
    Use sync=true for immediate results or async mode (default) with job tracking.
    """
    try:
        # Check if MarkItDown service is available
        if not markitdown_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MarkItDown service is not available. Please install 'markitdown[all]' package."
            )
        
        # Validate input parameters
        if not file and not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either file or url parameter must be provided"
            )
        
        if file and url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either file or url, not both"
            )
        
        # Create job
        job_id = str(uuid.uuid4())
        job_data = {
            "include_metadata": include_metadata,
            "preserve_formatting": preserve_formatting,
            "output_options": {},  # Future extension point
            "cookies_url": cookies_url
        }
        
        if file:
            # Handle file upload
            if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit for documents
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds 50MB limit"
                )
            
            # Validate file type by extension
            if file.filename:
                allowed_extensions = {
                    # Document formats
                    '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
                    # Text formats
                    '.txt', '.md', '.html', '.htm',
                    # Image formats (with OCR)
                    '.jpg', '.jpeg', '.png', '.gif',
                    # Audio formats (with transcription)
                    '.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg',
                    # Video formats (with transcription)
                    '.mp4', '.avi', '.mov', '.mkv', '.webm'
                }
                file_ext = os.path.splitext(file.filename.lower())[1]
                if file_ext not in allowed_extensions:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported file type '{file_ext}'. Use /formats endpoint to see supported formats."
                    )
            
            # Process file immediately instead of storing binary data in job params
            file_content = await file.read()
            job_data["input_filename"] = file.filename or "uploaded_document"
            
            # Create wrapper that processes binary data directly
            async def process_markdown_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await markitdown_service.process_document_with_file_data(
                    file_content=file_content,
                    params=data
                )
        else:
            # Handle URL input
            job_data["file_url"] = url
            job_data["input_filename"] = os.path.basename(url) or "document_from_url"
            
            # Create wrapper for URL-based processing
            async def process_markdown_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await markitdown_service.process_document_to_markdown(data)
        
        # Handle sync vs async processing
        if sync:
            # Process conversion synchronously
            try:
                if file:
                    # Handle file upload for sync processing
                    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit for sync processing
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="File size exceeds 10MB limit for synchronous processing. Use async processing for larger files."
                        )
                    
                    file_content = await file.read()
                    job_data["file_content"] = file_content
                    job_data["input_filename"] = file.filename or "uploaded_document"
                    
                    # Process synchronously
                    result = await markitdown_service.process_document_with_file_data(file_content, job_data)
                else:
                    # Handle URL for sync processing
                    result = await markitdown_service.process_document_to_markdown(job_data)
                
                logger.info(f"Synchronous document conversion completed for: {job_data.get('input_filename', 'unknown')}")
                
                return DocumentToMarkdownResult(**result)
                
            except Exception as e:
                logger.error(f"Synchronous document conversion failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document conversion failed: {str(e)}"
                )
        else:
            # Queue the job using consistent pattern (no binary data in job_data)
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.DOCUMENT_TO_MARKDOWN,
                process_func=process_markdown_wrapper,
                data=job_data  # No binary data stored here
            )
            
            logger.info(f"Created document to Markdown conversion job {job_id} for: {job_data.get('input_filename', 'unknown')}")
            
            return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating document conversion job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document conversion job"
        )