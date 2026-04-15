"""
Service for handling S3 file uploads.
"""
from typing import Any
from fastapi import UploadFile
from app.services.job_queue import job_queue
from app.models import JobType
import logging
import aiohttp
import tempfile
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class S3UploadService:
    """
    Service for handling S3 file uploads.
    """

    async def upload_file(
        self,
        job_id: str,
        file: UploadFile,
        file_name: str | None = None,
        public: bool = True,
    ) -> dict[str, Any]:
        """
        Upload a file to S3.
        """
        try:
            # Process file immediately instead of storing binary data in job params
            file_content = await file.read()
            
            # Create a wrapper function that processes the upload directly
            async def process_wrapper(_job_id: str, data: dict) -> dict:
                # Process the binary data directly without storing it in job params
                return await self.process_s3_upload_direct(
                    file_content=file_content,
                    file_name=file_name or file.filename or "uploaded_file",
                    content_type=file.content_type or "application/octet-stream",
                    public=public
                )
            
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.S3_UPLOAD,
                process_func=process_wrapper,
                data={},  # No binary data in job params
            )

            return {"job_id": job_id}
        except Exception as e:
            logger.error(f"Error creating S3 upload job: {e}")
            raise

    async def upload_from_url(
        self,
        job_id: str,
        url: str,
        file_name: str | None = None,
        public: bool = True,
    ) -> dict[str, Any]:
        """
        Upload a file from URL to S3.
        """
        try:
            params = {
                "url": url,
                "file_name": file_name,
                "public": public,
            }

            # Create a wrapper function that matches the expected signature
            async def process_wrapper(_job_id: str, data: dict) -> dict:
                return await self.process_url_upload(data)
            
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.S3_UPLOAD,
                process_func=process_wrapper,
                data=params,
            )

            return {"job_id": job_id}
        except Exception as e:
            logger.error(f"Error creating S3 URL upload job: {e}")
            raise

    async def process_s3_upload_direct(
        self, 
        file_content: bytes, 
        file_name: str, 
        content_type: str, 
        public: bool
    ) -> dict[str, Any]:
        """
        Process S3 upload directly with binary data (not stored in job params).
        """
        from app.services.s3.s3 import s3_service  # Import here to avoid circular import
        
        try:
            # Sanitize filename to replace spaces with underscores
            import re
            sanitized_name = file_name.replace(' ', '_')
            sanitized_name = re.sub(r'_+', '_', sanitized_name)  # Replace multiple underscores with single
            sanitized_name = re.sub(r'[^\w\-\.]', '_', sanitized_name, flags=re.UNICODE)  # Remove special chars
            sanitized_name = re.sub(r'_+', '_', sanitized_name)  # Clean up again
            sanitized_name = sanitized_name.strip('_')  # Remove leading/trailing underscores
            
            # Improve MIME type detection for file uploads
            import mimetypes
            if not content_type or content_type == "application/octet-stream":
                # Try to guess content type from filename
                guessed_type, _ = mimetypes.guess_type(file_name)
                if guessed_type:
                    content_type = guessed_type
                    logger.info(f"Detected content type from filename: {content_type}")

            # Write the file content to a temporary file
            temp_file_path = None
            try:
                # Create a temporary file for local processing
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    temp_file.write(file_content)

                # Upload the file to S3 with /upload prefix for organization and sanitized filename
                s3_key = f"upload/{sanitized_name}"
                
                # Upload the file to S3 and get metadata using the custom filename
                # Always pass the custom filename as object_name to ensure it's used
                upload_result = await s3_service.upload_file_with_metadata(
                    file_path=temp_file_path,
                    object_name=s3_key,  # Include upload prefix
                    content_type=content_type,
                    public=public,
                )
            finally:
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")

            # Add file size in human-readable format
            file_size_bytes = upload_result.get("file_size", 0)
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            
            return {
                "file_url": upload_result["file_url"],
                "file_name": upload_result["file_name"],
                "file_extension": upload_result["file_extension"],
                "mime_type": upload_result["mime_type"],
                "file_size": file_size_bytes,
                "file_size_mb": f"{file_size_mb} MB"
            }
        except Exception as e:
            logger.error(f"Error processing S3 upload: {e}")
            raise

    async def process_s3_upload(self, params: dict) -> dict[str, Any]:
        """
        Process the S3 upload.
        """
        from app.services.s3.s3 import s3_service  # Import here to avoid circular import
        
        try:
            file_name = params["file_name"]
            file_content = params["file_content"]
            content_type = params["content_type"]
            public = params.get("public", True)

            # Improve MIME type detection for file uploads
            import mimetypes
            if not content_type or content_type == "application/octet-stream":
                # Try to guess content type from filename
                guessed_type, _ = mimetypes.guess_type(file_name)
                if guessed_type:
                    content_type = guessed_type
                    logger.info(f"Detected content type from filename: {content_type}")

            # Write the file content to a temporary file
            temp_file_path = None
            try:
                # Create a temporary file for local processing
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    temp_file.write(file_content)

                # Upload the file to S3 and get metadata using the custom filename
                # Always pass the custom filename as object_name to ensure it's used
                upload_result = await s3_service.upload_file_with_metadata(
                    file_path=temp_file_path,
                    object_name=file_name,  # This ensures custom filename is used
                    content_type=content_type,
                    public=public,
                )
            finally:
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")

            # Add file size in human-readable format
            file_size_bytes = upload_result.get("file_size", 0)
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            
            return {
                "file_url": upload_result["file_url"],
                "file_name": upload_result["file_name"],
                "file_extension": upload_result["file_extension"],
                "mime_type": upload_result["mime_type"],
                "file_size": file_size_bytes,
                "file_size_mb": f"{file_size_mb} MB"
            }
        except Exception as e:
            logger.error(f"Error processing S3 upload: {e}")
            raise

    async def process_url_upload(self, params: dict) -> dict[str, Any]:
        """
        Process the URL-based S3 upload.
        """
        from app.services.s3.s3 import s3_service  # Import here to avoid circular import
        
        temp_file_path = None
        try:
            url = params["url"]
            file_name = params.get("file_name")
            public = params.get("public", True)
            
            # If no file name provided, extract from URL
            if not file_name:
                parsed_url = urlparse(url)
                file_name = os.path.basename(parsed_url.path)
                if not file_name or file_name == '/':
                    file_name = "downloaded_file"
            
            # Sanitize filename to replace spaces with underscores
            import re
            sanitized_name = file_name.replace(' ', '_')
            sanitized_name = re.sub(r'_+', '_', sanitized_name)  # Replace multiple underscores with single
            sanitized_name = re.sub(r'[^\w\-\.]', '_', sanitized_name, flags=re.UNICODE)  # Remove special chars
            sanitized_name = re.sub(r'_+', '_', sanitized_name)  # Clean up again
            sanitized_name = sanitized_name.strip('_')  # Remove leading/trailing underscores
            
            # Download file from URL
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    # Get content type from response headers
                    content_type = response.headers.get('content-type', 'application/octet-stream')
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{sanitized_name}") as temp_file:
                        temp_file_path = temp_file.name
                        
                        # Write content to temp file
                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)
            
            # Upload the file to S3 with /upload prefix and sanitized filename
            s3_key = f"upload/{sanitized_name}"
            
            # Upload the file to S3 and get metadata
            upload_result = await s3_service.upload_file_with_metadata(
                file_path=temp_file_path,
                object_name=s3_key,
                content_type=content_type,
                public=public,
            )

            # Add file size in human-readable format
            file_size_bytes = upload_result.get("file_size", 0)
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            
            return {
                "file_url": upload_result["file_url"],
                "file_name": upload_result["file_name"],
                "file_extension": upload_result["file_extension"],
                "mime_type": upload_result["mime_type"],
                "file_size": file_size_bytes,
                "file_size_mb": f"{file_size_mb} MB"
            }
            
        except Exception as e:
            logger.error(f"Error processing URL upload: {e}")
            raise
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")

s3_upload_service = S3UploadService()
