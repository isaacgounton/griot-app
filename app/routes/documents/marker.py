"""
Marker Document Processing Routes

High-quality document conversion using Marker library.
Supports PDF, DOCX, images, and more with advanced features.
"""

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request, status
from typing import Optional, Dict, Any
import logging

from app.models import (
    JobResponse, JobType,
    MarkerConversionResult, MarkerSupportedFormatsResponse
)
from app.services.job_queue import job_queue
from app.services.documents.marker_service import marker_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/marker", tags=["Content Tools"])

@router.post("/")
async def convert_document_with_marker(
    request: Request,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    output_format: str = Form("markdown"),
    force_ocr: bool = Form(False),
    preserve_images: bool = Form(True),
    use_llm: bool = Form(False),
    paginate_output: bool = Form(False),
    llm_service: Optional[str] = Form(None),
    sync: bool = Form(False),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Convert documents using Marker. Supports PDF, DOCX, PPTX, images, HTML, EPUB and more."""
    if not file and not url:
        raise HTTPException(status_code=400, detail="Either file or URL must be provided")
    
    if file and url:
        raise HTTPException(status_code=400, detail="Provide either file or URL, not both")
    
    # Validate output format
    supported_formats = ["markdown", "json", "html", "chunks"]
    if output_format not in supported_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid output format. Supported: {supported_formats}"
        )
    
    # Validate LLM service if provided
    if llm_service and llm_service not in ["openai", "gemini"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid LLM service. Supported: openai, gemini"
        )
    
    # Initialize variables
    file_path = None
    original_filename = "document"
    
    try:
        # Create wrapper function for job queue
        async def marker_conversion_wrapper(job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
            return await marker_service.convert_document(data)
        
        # Handle file upload
        
        if file:
            # Validate file type
            allowed_extensions = {
                '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
                '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff',
                '.html', '.htm', '.epub', '.txt'
            }
            
            file_ext = os.path.splitext(file.filename or "")[1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
                )
            
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                content = await file.read()
                temp_file.write(content)
                file_path = temp_file.name
                original_filename = file.filename or "document"
        
        elif url:
            # For URL processing, we'll need to download the file first
            import aiohttp
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Failed to download file from URL: HTTP {response.status}"
                            )
                        
                        # Determine file extension from URL or content type
                        content_type = response.headers.get('content-type', '')
                        file_ext = '.pdf'  # default
                        
                        if 'pdf' in content_type:
                            file_ext = '.pdf'
                        elif 'word' in content_type or 'document' in content_type:
                            file_ext = '.docx'
                        elif 'image' in content_type:
                            if 'png' in content_type:
                                file_ext = '.png'
                            elif 'jpeg' in content_type or 'jpg' in content_type:
                                file_ext = '.jpg'
                        
                        # Save downloaded file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                            content = await response.read()
                            temp_file.write(content)
                            file_path = temp_file.name
                            original_filename = url.split('/')[-1] or "document"
                            
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download file from URL: {str(e)}"
                )
        
        # Prepare job data
        job_data = {
            "file_path": file_path,
            "output_format": output_format,
            "force_ocr": force_ocr,
            "preserve_images": preserve_images,
            "use_llm": use_llm,
            "paginate_output": paginate_output,
            "llm_service": llm_service,
            "original_filename": original_filename
        }
        
        # Handle sync vs async processing
        if sync:
            # Process conversion synchronously
            try:
                result = await marker_service.convert_document(job_data)
                logger.info(f"Completed synchronous Marker conversion for file: {original_filename}")
                return MarkerConversionResult(**result)
            except Exception as e:
                logger.error(f"Error in synchronous Marker conversion: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Conversion failed: {str(e)}"
                )
        else:
            # Create async job (existing logic)
            # Generate job ID
            import uuid
            job_id = str(uuid.uuid4())
            
            # Add job to queue
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.MARKER_DOCUMENT_CONVERSION,
                process_func=marker_conversion_wrapper,
                data=job_data
            )
            
            logger.info(f"Marker conversion job created: {job_id} for file: {original_filename}")
            return JobResponse(job_id=job_id)
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up temp file if it was created
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass

        logger.error(f"Failed to create Marker conversion job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create conversion job: {str(e)}")


@router.get("/formats", response_model=MarkerSupportedFormatsResponse)
async def get_supported_formats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get supported input/output formats and Marker capabilities."""
    try:
        formats_info = await marker_service.get_supported_formats()
        return MarkerSupportedFormatsResponse(**formats_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get supported formats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported formats: {str(e)}")

