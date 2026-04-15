"""
Routes for media conversions.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from app.models import JobResponse, MediaConversionRequest, JobType
from app.services.media.media_conversion_service import SUPPORTED_FORMATS, QUALITY_PRESETS, detect_media_type
from app.services.media.media_conversion_service import media_conversion_service
from app.services.job_queue import job_queue
from app.utils.auth import get_current_user
import uuid
import logging
import base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversions", tags=["Media"])


@router.get("/formats")
async def get_supported_formats():
    """List all supported conversion formats, codecs, and quality presets."""
    # Create a flat list of all formats for easy reference
    all_formats = []
    for media_type, formats in SUPPORTED_FORMATS.items():
        for format_name, format_info in formats.items():
            all_formats.append({
                "format": format_name,
                "media_type": media_type,
                "codec": format_info.get("codec", "unknown"),
                "description": format_info.get("description", "")
            })
    
    return {
        "object": "formats",
        "supported_formats": SUPPORTED_FORMATS,
        "quality_presets": {
            preset: info for preset, info in QUALITY_PRESETS.items()
        },
        "total_formats": sum(len(formats) for formats in SUPPORTED_FORMATS.values()),
        "format_list": all_formats,
        "media_types": list(SUPPORTED_FORMATS.keys())
    }


@router.post("/")
async def convert_media(
    request: Request,
    file: UploadFile | None = File(None),
    url: str | None = Form(None), 
    output_format: str | None = Form(None),
    quality: str = Form("medium"),
    custom_options: str | None = Form(None),
    sync: bool = Form(False),
    _: dict[str, Any] = Depends(get_current_user),  # API key validation (not used in function)
):
    """Convert media between formats using FFmpeg. Accepts file uploads, URLs, or base64-encoded JSON data."""
    try:
        # Initialize variables
        json_file_data = None
        # Check if this is a JSON request for URL-based conversion
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            # Handle JSON request for URL-based or file-based conversion
            body = await request.json()
            json_request = MediaConversionRequest(**body)
            
            # Check if either URL or file data is provided
            if not json_request.input_url and not json_request.file_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either 'input_url' or 'file_data' parameter is required for JSON requests"
                )
            
            if json_request.input_url and json_request.file_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide either 'input_url' or 'file_data', not both"
                )
                
            url = str(json_request.input_url) if json_request.input_url else None
            output_format = json_request.output_format
            quality = json_request.quality or "medium"
            custom_options = json_request.custom_options
            sync = json_request.sync
            
            # Handle file data if provided
            if json_request.file_data:
                # Additional validation for file size (limit to 100MB)
                file_size = len(json_request.file_data) * 3 // 4  # Approximate decoded size
                if file_size > 100 * 1024 * 1024:  # 100MB limit
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File size too large. Maximum allowed size is 100MB."
                    )
                
                # Decode base64 file data
                file_content = base64.b64decode(json_request.file_data)
                
                # Store file data for later processing
                json_file_data = {
                    'content': file_content,
                    'filename': json_request.filename or 'uploaded_file',
                    'content_type': json_request.content_type or 'application/octet-stream'
                }
                file = None  # Set to None since we're handling it differently
            else:
                json_file_data = None
                file = None
        else:
            # Handle form data request
            if not file and not url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either 'file' or 'url' parameter is required"
                )
            
            if file and url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide either 'file' or 'url', not both"
                )
            
            if not output_format:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="output_format parameter is required"
                )
        
        # Validate output format
        all_formats = set()
        for format_list in SUPPORTED_FORMATS.values():
            all_formats.update(format_list)
        
        if output_format.lower() not in all_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported output format '{output_format}'. Use /formats endpoint to see supported formats."
            )
        
        # Validate quality preset
        if quality not in QUALITY_PRESETS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid quality preset '{quality}'. Supported presets: {', '.join(QUALITY_PRESETS.keys())}"
            )

        # Handle sync vs async processing
        if sync:
            # Process conversion synchronously
            try:
                if file or (json_file_data is not None):
                    # Handle both regular file uploads and JSON file data
                    if file:
                        # For regular file uploads
                        file_content = await file.read()
                        filename = file.filename
                        content_type = file.content_type
                    elif json_file_data is not None:
                        # For JSON file data
                        file_content = json_file_data['content']
                        filename = json_file_data['filename']
                        content_type = json_file_data['content_type']
                    else:
                        # This should never happen, but for type safety
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal error: no file data available"
                        )
                    
                    file_data = base64.b64encode(file_content).decode('utf-8')
                    
                    # Detect media type from file
                    input_type = detect_media_type(content_type or '', filename or '')
                    if input_type == "unknown":
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot determine media type from uploaded file. Please ensure the file has a proper extension and content type."
                        )
                    
                    job_data = {
                        "input_type": input_type,
                        "file_data": file_data,
                        "filename": filename,
                        "content_type": content_type,
                        "output_format": output_format.lower(),
                        "quality": quality,
                        "custom_options": custom_options
                    }
                else:
                    # For URL-based conversions - type will be detected in service
                    job_data = {
                        "input_type": "url", 
                        "input_url": url,
                        "output_format": output_format.lower(),
                        "quality": quality,
                        "custom_options": custom_options
                    }
                
                # Process conversion immediately
                result = await media_conversion_service.process_conversion(job_data)
                
                logger.info(f"Completed synchronous media conversion for format: {output_format} (input: {'file' if file or json_file_data else 'url'})")
                
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": result
                }
                
            except Exception as e:
                logger.error(f"Error in synchronous media conversion: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Conversion failed: {str(e)}"
                )
        else:
            # Create async job (existing logic)
            job_id = str(uuid.uuid4())
            
            # Handle file upload or URL
            if file or (json_file_data is not None):
                # Handle both regular file uploads and JSON file data
                if file:
                    # For regular file uploads
                    file_content = await file.read()
                    filename = file.filename
                    content_type = file.content_type
                elif json_file_data is not None:
                    # For JSON file data
                    file_content = json_file_data['content']
                    filename = json_file_data['filename']
                    content_type = json_file_data['content_type']
                else:
                    # This should never happen, but for type safety
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Internal error: no file data available"
                    )
                
                file_data = base64.b64encode(file_content).decode('utf-8')
                
                # Detect media type from file
                input_type = detect_media_type(content_type or '', filename or '')
                if input_type == "unknown":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot determine media type from uploaded file. Please ensure the file has a proper extension and content type."
                    )
                
                job_data = {
                    "input_type": input_type,
                    "file_data": file_data,
                    "filename": filename,
                    "content_type": content_type,
                    "output_format": output_format.lower(),
                    "quality": quality,
                    "custom_options": custom_options
                }
            else:
                # For URL-based conversions - type will be detected in service
                job_data = {
                    "input_type": "url", 
                    "input_url": url,
                    "output_format": output_format.lower(),
                    "quality": quality,
                    "custom_options": custom_options
                }
            
            # Create a wrapper function for URL-based processing
            async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await media_conversion_service.process_conversion(data)
            
            # Queue the job using consistent pattern (no binary data in job_data)
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.MEDIA_CONVERSION,
                process_func=process_wrapper,
                data=job_data  # No binary data stored here
            )
            
            logger.info(f"Created media conversion job {job_id} for format: {output_format} (input: {'file' if file else 'url'})")
            
            return JobResponse(
                job_id=job_id
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating media conversion job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create media conversion job"
        )
