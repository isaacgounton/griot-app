"""
Document to Markdown conversion service using Microsoft MarkItDown.

This service provides document conversion capabilities for various file formats
including PDF, Word, Excel, PowerPoint, and more to Markdown format.
"""
import os
import time
import tempfile
import logging
import mimetypes
from typing import Any
from pathlib import Path
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class MarkItDownService:
    """
    Service for converting documents to Markdown using Microsoft MarkItDown.
    
    This service handles document conversion from various formats (PDF, DOCX, PPTX, 
    XLSX, etc.) to Markdown format using the MarkItDown library.
    """
    
    def __init__(self):
        """Initialize the MarkItDown service."""
        self._markitdown = None
        self._initialize_markitdown()
    
    def _initialize_markitdown(self) -> None:
        """Initialize MarkItDown library with error handling."""
        try:
            from markitdown import MarkItDown  # type: ignore
            self._markitdown = MarkItDown()
            logger.info("MarkItDown service initialized successfully")
        except ImportError as e:
            logger.error(f"MarkItDown library not available: {e}")
            logger.error("Install with: pip install 'markitdown[all]'")
            self._markitdown = None
        except Exception as e:
            logger.error(f"Failed to initialize MarkItDown: {e}")
            self._markitdown = None
    
    def is_available(self) -> bool:
        """Check if MarkItDown service is available."""
        return self._markitdown is not None
    
    async def process_document_with_file_data(self, file_content: bytes, params: dict[str, Any]) -> dict[str, Any]:
        """
        Process document to Markdown with binary file data (not stored in job params).
        """
        try:
            # Add the binary file data to params for processing
            params_with_file = params.copy()
            # Create a temporary file directly with the binary data instead of base64 encoding
            import tempfile
            import base64
            
            original_filename = params.get('input_filename', 'document')
            
            # Write binary data directly to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{original_filename}") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Update params to use file path instead of binary data
            params_with_file['temp_file_path'] = temp_file_path
            params_with_file.pop('input_file_data', None)  # Remove if present
            
            # Process using the common processing logic
            return await self._process_document_common(
                temp_file_path=temp_file_path,
                original_filename=original_filename,
                include_metadata=params.get('include_metadata', True),
                preserve_formatting=params.get('preserve_formatting', True),
                output_options=params.get('output_options', {}),
                cookies_url=params.get('cookies_url')
            )
        except Exception as e:
            logger.error(f"Error processing document with file data: {e}")
            raise
    
    async def process_document_to_markdown(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process document to Markdown conversion.
        
        Args:
            job_data: Job data containing document info and conversion options
            
        Returns:
            Dictionary containing conversion results
            
        Raises:
            RuntimeError: If MarkItDown is not available or conversion fails
        """
        if not self.is_available():
            raise RuntimeError(
                "MarkItDown service is not available. "
                "Please install with: pip install 'markitdown[all]'"
            )
        
        start_time = time.time()
        temp_file_path = None
        
        try:
            # Extract parameters
            file_url = job_data.get('file_url')
            file_data = job_data.get('input_file_data')  # base64 encoded
            original_filename = job_data.get('input_filename', 'document')
            include_metadata = job_data.get('include_metadata', True)
            preserve_formatting = job_data.get('preserve_formatting', True)
            output_options = job_data.get('output_options', {})
            cookies_url = job_data.get('cookies_url')
            
            logger.info(f"Starting document conversion: {original_filename}")
            
            # Download or decode file
            if file_url:
                temp_file_path = await self._download_file(file_url, original_filename, cookies_url)
            elif file_data:
                temp_file_path = await self._decode_file_data(file_data, original_filename)
            else:
                raise ValueError("Either file_url or input_file_data must be provided")
            
            # Use common processing logic
            return await self._process_document_common(
                temp_file_path=temp_file_path,
                original_filename=original_filename,
                include_metadata=include_metadata,
                preserve_formatting=preserve_formatting,
                output_options=output_options,
                cookies_url=cookies_url
            )
            
        except Exception as e:
            logger.error(f"Document conversion failed: {e}")
            raise RuntimeError(f"Document conversion failed: {str(e)}")
        
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")
    
    async def _process_document_common(
        self, 
        temp_file_path: str, 
        original_filename: str, 
        include_metadata: bool, 
        preserve_formatting: bool, 
        output_options: dict[str, Any], 
        cookies_url: str | None
    ) -> dict[str, Any]:
        """
        Common document processing logic shared between different input methods.
        """
        start_time = time.time()
        
        try:
            # Detect file type
            file_type = self._detect_file_type(temp_file_path, original_filename)
            logger.info(f"Detected file type: {file_type}")
            
            # Convert document using MarkItDown
            conversion_result = await self._convert_document(
                temp_file_path, 
                output_options, 
                preserve_formatting,
                cookies_url
            )
            
            # Extract content and metadata
            markdown_content = conversion_result.text_content
            document_metadata = getattr(conversion_result, 'metadata', {}) if include_metadata else {}
            
            # Calculate statistics
            word_count = len(markdown_content.split())
            character_count = len(markdown_content)
            processing_time = time.time() - start_time
            
            # Prepare result
            result = {
                "markdown_content": markdown_content,
                "original_filename": original_filename,
                "file_type": file_type,
                "word_count": word_count,
                "character_count": character_count,
                "processing_time": processing_time
            }
            
            if include_metadata and document_metadata:
                result["metadata"] = document_metadata
            
            logger.info(
                f"Document conversion completed: {original_filename} -> "
                f"{word_count} words, {character_count} chars in {processing_time:.2f}s"
            )
            
            return result
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")
    
    async def _download_file(self, file_url: str, filename: str, cookies_url: str | None = None) -> str:
        """Download file from URL to temporary location."""
        # Check if this is a YouTube URL that might need special handling
        youtube_domains = ["youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com"]
        is_youtube_url = any(domain in file_url.lower() for domain in youtube_domains)
        
        if is_youtube_url and cookies_url:
            # For YouTube URLs with cookies, use yt-dlp-like approach
            return await self._download_youtube_file(file_url, filename, cookies_url)
        else:
            # Standard HTTP download for regular files
            return await self._download_regular_file(file_url, filename)
    
    async def _download_regular_file(self, file_url: str, filename: str) -> str:
        """Download regular file from URL to temporary location."""
        # Create temporary file with appropriate extension
        file_ext = Path(filename).suffix or self._guess_extension_from_url(file_url)
        temp_file = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
        temp_file_path = temp_file.name
        temp_file.close()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Failed to download file: HTTP {response.status}")
                    
                    with open(temp_file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            logger.info(f"Downloaded file from {file_url} to {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise RuntimeError(f"Failed to download file: {str(e)}")
    
    async def _download_youtube_file(self, file_url: str, filename: str, cookies_url: str) -> str:
        """Download YouTube video using cookies for server environments."""
        import requests
        
        # Create temporary file for the downloaded content
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file_path = temp_file.name
        temp_file.close()
        
        cookies_file_path = None
        
        try:
            # Download cookies file
            logger.info(f"Downloading cookies from {cookies_url} for YouTube video")
            response = requests.get(cookies_url)
            response.raise_for_status()
            
            cookies_file_path = tempfile.NamedTemporaryFile(delete=False).name
            with open(cookies_file_path, "w") as f:
                f.write(response.text)
            
            # Let MarkItDown handle the YouTube URL with cookies
            # Since MarkItDown internally may use yt-dlp, we'll pass the URL as-is
            # and let it handle the download. We'll create an environment variable
            # or configuration that MarkItDown can use for cookies
            
            # For now, we'll fall back to regular download and let MarkItDown handle it
            # This is because MarkItDown has its own YouTube handling mechanism
            logger.info(f"YouTube URL detected: {file_url}, cookies available")
            
            # Store cookies info for potential use by MarkItDown
            # We'll pass the original URL and let MarkItDown handle YouTube processing
            return file_url  # Return URL instead of downloaded file for YouTube
            
        except Exception as e:
            logger.error(f"Failed to setup YouTube download with cookies: {e}")
            # Fall back to regular download
            return await self._download_regular_file(file_url, filename)
        
        finally:
            # Clean up cookies file
            if cookies_file_path and os.path.exists(cookies_file_path):
                os.remove(cookies_file_path)
                logger.info(f"Removed temporary cookies file: {cookies_file_path}")
    
    async def _decode_file_data(self, file_data: str, filename: str) -> str:
        """Decode base64 file data to temporary file."""
        import base64
        
        # Create temporary file with appropriate extension
        file_ext = Path(filename).suffix
        temp_file = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
        temp_file_path = temp_file.name
        
        try:
            # Decode base64 data
            decoded_data = base64.b64decode(file_data)
            
            # Write to temporary file
            with open(temp_file_path, 'wb') as f:
                f.write(decoded_data)
            
            temp_file.close()
            logger.info(f"Decoded file data to {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            # Clean up on error
            temp_file.close()
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise RuntimeError(f"Failed to decode file data: {str(e)}")
    
    def _detect_file_type(self, file_path: str, filename: str) -> str:
        """Detect file type from file path and filename."""
        # Try to get MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        
        # Map to common file types
        if mime_type:
            if mime_type == 'application/pdf':
                return 'PDF'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/msword']:
                return 'Word Document'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.presentationml.presentation',
                              'application/vnd.ms-powerpoint']:
                return 'PowerPoint Presentation'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                              'application/vnd.ms-excel']:
                return 'Excel Spreadsheet'
            elif mime_type.startswith('text/'):
                return 'Text Document'
            elif mime_type.startswith('image/'):
                return 'Image'
            elif mime_type.startswith('audio/'):
                return 'Audio File'
            elif mime_type.startswith('video/'):
                return 'Video File'
        
        # Fallback to file extension
        ext = Path(filename).suffix.lower()
        ext_map = {
            # Document formats
            '.pdf': 'PDF',
            '.docx': 'Word Document',
            '.doc': 'Word Document',
            '.pptx': 'PowerPoint Presentation',
            '.ppt': 'PowerPoint Presentation',
            '.xlsx': 'Excel Spreadsheet',
            '.xls': 'Excel Spreadsheet',
            # Text formats
            '.txt': 'Text Document',
            '.md': 'Markdown Document',
            '.html': 'HTML Document',
            '.htm': 'HTML Document',
            # Image formats
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.png': 'Image',
            '.gif': 'Image',
            # Audio formats
            '.mp3': 'Audio File',
            '.wav': 'Audio File',
            '.m4a': 'Audio File',
            '.aac': 'Audio File',
            '.flac': 'Audio File',
            '.ogg': 'Audio File',
            # Video formats
            '.mp4': 'Video File',
            '.avi': 'Video File',
            '.mov': 'Video File',
            '.mkv': 'Video File',
            '.webm': 'Video File'
        }
        
        return ext_map.get(ext, f'Unknown ({ext})')
    
    def _guess_extension_from_url(self, url: str) -> str:
        """Guess file extension from URL."""
        try:
            path = Path(url)
            return path.suffix
        except Exception:
            return '.tmp'
    
    def _validate_pdf_file(self, file_path: str) -> bool:
        """
        Validate that a PDF file is not corrupted and has basic PDF structure.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            True if PDF appears valid, False otherwise
            
        Raises:
            RuntimeError: If PDF validation fails with specific error details
        """
        try:
            # Try to read the file and check for basic PDF structure
            with open(file_path, 'rb') as f:
                # Read first few bytes to check PDF header
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    raise RuntimeError(
                        "File does not appear to be a valid PDF. "
                        "PDF files must start with '%PDF-' header."
                    )
                
                # Check file size
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()
                if file_size < 100:  # PDFs should be at least 100 bytes
                    raise RuntimeError(
                        "PDF file is too small to be valid. "
                        f"File size: {file_size} bytes."
                    )
                
                # Try to find %%EOF marker at the end
                f.seek(-1024, 2)  # Check last 1KB
                end_content = f.read()
                if b'%%EOF' not in end_content:
                    logger.warning(f"PDF file {file_path} missing %%EOF marker - may be truncated")
                
                # Try basic PDF parsing to check for /Root object
                f.seek(0)
                content = f.read()
                
                # Look for /Root reference in the PDF
                if b'/Root' not in content:
                    raise RuntimeError(
                        "PDF file is missing the required /Root object. "
                        "This indicates the PDF is corrupted or incomplete."
                    )
                
                # Check for xref table or stream
                if b'xref' not in content and b'/Type/XRef' not in content:
                    logger.warning(f"PDF file {file_path} missing xref table - may have parsing issues")
            
            return True
            
        except RuntimeError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.warning(f"PDF validation encountered an error: {e}")
            # Don't fail validation for unknown errors, let MarkItDown handle it
            return True
    
    async def _convert_document(self, file_path: str, output_options: dict[str, Any], 
                              preserve_formatting: bool, cookies_url: str | None = None) -> Any:
        """Convert document using MarkItDown."""
        cookies_file_path = None
        original_env = None
        
        try:
            # Set up cookies for YouTube processing if provided
            if cookies_url and any(domain in str(file_path).lower() for domain in ["youtube.com", "youtu.be"]):
                import requests
                
                # Download cookies file
                logger.info(f"Setting up cookies for MarkItDown YouTube processing")
                response = requests.get(cookies_url)
                response.raise_for_status()
                
                cookies_file_path = tempfile.NamedTemporaryFile(delete=False).name
                with open(cookies_file_path, "w") as f:
                    f.write(response.text)
                
                # Try to configure MarkItDown with cookies via environment variable
                # This is a best-effort approach since MarkItDown may not support this directly
                original_env = os.environ.get('MARKITDOWN_COOKIES_FILE')
                os.environ['MARKITDOWN_COOKIES_FILE'] = cookies_file_path
                logger.info(f"Set MARKITDOWN_COOKIES_FILE environment variable")
            
            # Check if this is an audio/video file and try alternative processing
            file_type = self._detect_file_type(file_path, os.path.basename(file_path))
            if file_type in ['Audio File', 'Video File']:
                logger.info(f"Attempting audio/video transcription for {file_type}")
                try:
                    return await self._convert_audio_video_with_fallback(file_path)
                except Exception as audio_error:
                    logger.warning(f"Audio/video fallback failed: {audio_error}")
                    # Continue with regular MarkItDown processing
            
            # Validate PDF files before conversion
            if file_type == 'PDF':
                try:
                    self._validate_pdf_file(file_path)
                    logger.info(f"PDF validation passed for {file_path}")
                except RuntimeError as validation_error:
                    logger.error(f"PDF validation failed: {validation_error}")
                    raise RuntimeError(f"PDF validation failed: {str(validation_error)}")
            
            # Run conversion in thread to avoid blocking
            if self._markitdown is not None:
                result = await asyncio.to_thread(
                    self._markitdown.convert,
                    file_path
                )
            else:
                raise RuntimeError("MarkItDown service is not available")
            
            return result
            
        except Exception as e:
            # Handle specific PDF errors with better messages
            error_str = str(e)
            
            # Detect file type for error handling
            file_type = self._detect_file_type(file_path, os.path.basename(file_path))
            
            if "PDFSyntaxError" in error_str or "No /Root object" in error_str:
                logger.error(f"PDF file appears to be corrupted or invalid: {file_path}")
                raise RuntimeError(
                    "PDF file appears to be corrupted or invalid. "
                    "The file may be damaged, incomplete, or not a valid PDF. "
                    "Please check the file and try again with a valid PDF document."
                )
            elif "PdfReadError" in error_str or "PDF read error" in error_str:
                logger.error(f"Unable to read PDF file: {file_path}")
                raise RuntimeError(
                    "Unable to read the PDF file. "
                    "The file may be password-protected, corrupted, or in an unsupported format."
                )
            elif "UnsupportedOperation" in error_str and file_type == 'PDF':
                logger.error(f"PDF operation not supported: {file_path}")
                raise RuntimeError(
                    "PDF conversion failed due to an unsupported operation. "
                    "The PDF may contain features that are not supported by the converter."
                )
            
            logger.error(f"MarkItDown conversion failed for {file_path}: {e}")
            # For audio/video files, try our own transcription as final fallback
            if file_type in ['Audio File', 'Video File']:
                try:
                    logger.info("Attempting custom transcription as final fallback")
                    return await self._convert_audio_video_with_whisper(file_path)
                except Exception as fallback_error:
                    logger.error(f"Custom transcription fallback also failed: {fallback_error}")
            
            raise RuntimeError(f"Document conversion failed: {str(e)}")
        
        finally:
            # Clean up cookies file and environment
            if cookies_file_path and os.path.exists(cookies_file_path):
                os.remove(cookies_file_path)
                logger.info(f"Removed temporary cookies file: {cookies_file_path}")
            
            # Restore original environment
            if original_env is not None:
                os.environ['MARKITDOWN_COOKIES_FILE'] = original_env
            elif 'MARKITDOWN_COOKIES_FILE' in os.environ:
                del os.environ['MARKITDOWN_COOKIES_FILE']
    
    async def _convert_audio_video_with_fallback(self, file_path: str) -> Any:
        """
        Convert audio/video files with our own transcription fallback.
        First tries MarkItDown, then falls back to our custom implementation.
        """
        # Try MarkItDown first but with better error handling
        try:
            loop = asyncio.get_event_loop()
            if self._markitdown is not None:
                # Try to disable MarkItDown's problematic AudioConverter temporarily
                # by using a simpler approach
                result = await loop.run_in_executor(
                    None,
                    self._safe_markitdown_convert,
                    file_path
                )
                return result
            else:
                raise RuntimeError("MarkItDown service is not available")
        except Exception as e:
            logger.warning(f"MarkItDown audio/video conversion failed: {e}")
            # Fall back to our custom implementation
            return await self._convert_audio_video_with_whisper(file_path)
    
    def _safe_markitdown_convert(self, file_path: str) -> Any:
        """
        Safely convert with MarkItDown, handling AudioConverter errors.
        """
        try:
            if self._markitdown is not None:
                return self._markitdown.convert(file_path)
            else:
                raise RuntimeError("MarkItDown service is not available")
        except Exception as e:
            # If it's specifically an AudioConverter error, we'll re-raise
            # so the caller can handle it with fallback
            if "AudioConverter" in str(e) or "UnknownValueError" in str(e):
                raise RuntimeError(f"MarkItDown AudioConverter failed: {str(e)}")
            raise
    
    async def _convert_audio_video_with_whisper(self, file_path: str) -> Any:
        """
        Convert audio/video files using the Speaches sidecar for transcription.
        This is a fallback when MarkItDown's AudioConverter fails.
        """
        try:
            from app.services.speaches.speaches_client import speaches_client

            logger.info(f"Using Speaches sidecar transcription for {file_path}")

            result = await speaches_client.transcribe(
                file_path=file_path,
                model="Systran/faster-whisper-small",
                language=None,
                response_format="verbose_json",
            )

            # Extract the transcribed text
            transcribed_text = result.get("text", "").strip()

            if not transcribed_text:
                transcribed_text = "[No speech detected in the audio/video file]"

            # Create a MarkItDown-compatible result object
            class WhisperTranscriptionResult:
                def __init__(self, text_content: str):
                    self.text_content = text_content
                    self.metadata = {
                        "transcription_method": "speaches_sidecar",
                        "model": "faster-whisper-small",
                        "source": "speaches_client"
                    }

            logger.info(f"Speaches transcription completed, {len(transcribed_text)} characters")
            return WhisperTranscriptionResult(f"# Audio/Video Transcription\n\n{transcribed_text}")

        except Exception as e:
            logger.error(f"Speaches transcription failed: {e}")
            # Create a minimal result indicating the issue
            class TranscriptionFailedResult:
                def __init__(self, message: str):
                    self.text_content = f"# Transcription Error\n\n{message}"
                    self.metadata = {"error": "transcription_failed"}

            return TranscriptionFailedResult(
                f"Audio/video transcription failed: {str(e)}"
            )
    
    def get_supported_formats(self) -> dict[str, Any]:
        """Get list of supported document formats."""
        return {
            "supported_formats": {
                "documents": {
                    "pdf": {"description": "PDF documents"},
                    "docx": {"description": "Microsoft Word documents"},
                    "doc": {"description": "Legacy Microsoft Word documents"},
                    "pptx": {"description": "Microsoft PowerPoint presentations"},
                    "ppt": {"description": "Legacy Microsoft PowerPoint presentations"},
                    "xlsx": {"description": "Microsoft Excel spreadsheets"},
                    "xls": {"description": "Legacy Microsoft Excel spreadsheets"}
                },
                "text": {
                    "txt": {"description": "Plain text files"},
                    "md": {"description": "Markdown files"},
                    "html": {"description": "HTML documents"},
                    "htm": {"description": "HTML documents"}
                },
                "images": {
                    "jpg": {"description": "JPEG images (with OCR)"},
                    "jpeg": {"description": "JPEG images (with OCR)"},
                    "png": {"description": "PNG images (with OCR)"},
                    "gif": {"description": "GIF images (with OCR)"}
                },
                "audio": {
                    "mp3": {"description": "MP3 audio files (with speech transcription)"},
                    "wav": {"description": "WAV audio files (with speech transcription)"},
                    "m4a": {"description": "M4A audio files (with speech transcription)"},
                    "aac": {"description": "AAC audio files (with speech transcription)"},
                    "flac": {"description": "FLAC audio files (with speech transcription)"},
                    "ogg": {"description": "OGG audio files (with speech transcription)"}
                },
                "video": {
                    "mp4": {"description": "MP4 video files (with speech transcription)"},
                    "avi": {"description": "AVI video files (with speech transcription)"},
                    "mov": {"description": "MOV video files (with speech transcription)"},
                    "mkv": {"description": "MKV video files (with speech transcription)"},
                    "webm": {"description": "WebM video files (with speech transcription)"}
                }
            },
            "features": [
                "Text extraction with structure preservation",
                "Table conversion to Markdown format",
                "Header hierarchy preservation",
                "List formatting preservation",
                "Image OCR for text extraction",
                "Audio speech transcription (requires markitdown[audio-transcription])",
                "Video speech transcription (requires markitdown[audio-transcription])",
                "Metadata extraction (when available)"
            ],
            "requirements": "markitdown[all] package (includes audio-transcription dependencies)",
            "available": self.is_available()
        }


# Create service instance
markitdown_service = MarkItDownService()