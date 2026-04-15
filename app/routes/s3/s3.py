"""
Routes for S3 file uploads.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request
from app.models import S3UploadRequest, JobResponse
from typing import Dict, Any, Optional
from app.services.s3.s3_service import s3_upload_service
from app.services.job_queue import job_queue
from app.utils.auth import get_current_user
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Storage & Jobs"])


@router.post("")
async def upload_file(
    request: Request,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    file_name: Optional[str] = Form(None),
    public: Optional[str] = Form("true"),
    sync: bool = Form(False),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Upload a file to S3 from either a file upload or URL.
    
    Parameters:
    - file: File to upload (multipart form data)
    - url: URL to download and upload to S3
    - file_name: Custom filename (optional)
    - public: Whether the file should be publicly accessible (default: True)
    - sync: If True, return result immediately. If False (default), create async job.
    
    Note: Provide either 'file' or 'url', not both.
    """
    try:
        # Check if this is a JSON request
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            # Handle JSON request
            body = await request.json()
            json_request = S3UploadRequest(**body)
            url = str(json_request.file_url)
            file_name = json_request.file_name
            sync = json_request.sync
            public_bool = True  # Default for JSON requests
            file = None
        else:
            # Handle form data request
            public_bool = public.lower() in ('true', '1', 'yes') if public else True
        
        logger.info(f"S3 upload request: file={file is not None}, url={url}, file_name={file_name}, public={public_bool}, sync={sync}")
        
        # Validate that exactly one input method is provided
        if not file and not url:
            logger.error("No file or URL provided")
            raise HTTPException(
                status_code=400, 
                detail="Either 'file' or 'url' parameter must be provided"
            )
        
        if file and url:
            logger.error("Both file and URL provided")
            raise HTTPException(
                status_code=400, 
                detail="Cannot provide both 'file' and 'url' parameters. Choose one."
            )
            
        # Additional file validation
        if file:
            if not file.filename:
                logger.error("File provided but filename is empty")
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file must have a filename"
                )
            if file.size == 0:
                logger.error("File provided but size is 0")
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file cannot be empty"
                )
        
        # Handle sync vs async processing
        if sync:
            # Process upload synchronously - call processing methods directly
            try:
                if file:
                    # Handle file upload - read file content and process directly
                    logger.info(f"Processing synchronous file upload: {file.filename}, size: {file.size}")
                    file_content = await file.read()
                    result = await s3_upload_service.process_s3_upload_direct(
                        file_content=file_content,
                        file_name=file_name or file.filename or "uploaded_file",
                        content_type=file.content_type or "application/octet-stream",
                        public=public_bool
                    )
                else:
                    # Handle URL upload
                    if url is None:
                        raise HTTPException(status_code=400, detail="URL is required for URL uploads")
                        
                    logger.info(f"Processing synchronous URL upload: {url}")
                    params = {
                        "url": url,
                        "file_name": file_name,
                        "public": public_bool,
                    }
                    result = await s3_upload_service.process_url_upload(params)
                
                logger.info("Completed synchronous S3 upload")
                return {
                    "job_id": None,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                logger.error(f"Error in synchronous S3 upload: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Upload failed: {str(e)}"
                )
        else:
            # Create async job (existing logic)
            job_id = str(uuid.uuid4())
            
            if file:
                # Handle file upload
                logger.info(f"Processing file upload: {file.filename}, size: {file.size}")
                result = await s3_upload_service.upload_file(
                    job_id=job_id,
                    file=file,
                    file_name=file_name,
                    public=public_bool,
                )
            else:
                # Handle URL upload
                if url is None:
                    raise HTTPException(status_code=400, detail="URL is required for URL uploads")
                    
                logger.info(f"Processing URL upload: {url}")
                result = await s3_upload_service.upload_from_url(
                    job_id=job_id,
                    url=url,
                    file_name=file_name,
                    public=public_bool,
                )
            
            logger.info(f"S3 upload job created successfully: {result}")
            return JobResponse(job_id=result["job_id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create S3 upload job: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
