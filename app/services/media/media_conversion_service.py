"""
Service for handling universal media conversions using FFmpeg.
"""
import os
import subprocess
import tempfile
import mimetypes
import shlex
import re
import asyncio
import requests
import uuid
import base64
from urllib.parse import urlparse
import ipaddress
from typing import Dict, Any, Optional, List, Tuple, Union

from app.services.job_queue import job_queue
from app.models import JobType
from app.services.s3.s3 import s3_service
from loguru import logger

# Comprehensive format support (all FFmpeg-supported formats)
SUPPORTED_FORMATS = {
    "audio": {
        "mp3": {"codec": "libmp3lame", "description": "MP3 Audio"},
        "wav": {"codec": "pcm_s16le", "description": "WAV Audio"},
        "flac": {"codec": "flac", "description": "FLAC Lossless Audio"},
        "aac": {"codec": "aac", "description": "AAC Audio"},
        "ogg": {"codec": "libvorbis", "description": "Ogg Vorbis"},
        "oga": {"codec": "libvorbis", "description": "Ogg Audio"},
        "opus": {"codec": "libopus", "description": "Opus Audio"},
        "m4a": {"codec": "aac", "description": "M4A Audio"},
        "wma": {"codec": "wmav2", "description": "Windows Media Audio"},
        "ac3": {"codec": "ac3", "description": "AC3 Audio"},
        "amr": {"codec": "amrnb", "description": "AMR Narrowband"},
        "au": {"codec": "pcm_s16be", "description": "Au Audio"},
        "aiff": {"codec": "pcm_s16be", "description": "AIFF Audio"},
        "dts": {"codec": "dca", "description": "DTS Audio"},
        "mp2": {"codec": "mp2", "description": "MP2 Audio"},
        "ape": {"codec": "ape", "description": "Monkey's Audio"},
        "ra": {"codec": "real_144", "description": "RealAudio"},
        "tta": {"codec": "tta", "description": "TTA Lossless Audio"},
        "wv": {"codec": "wavpack", "description": "WavPack Audio"},
    },
    "video": {
        "mp4": {"codec": "libx264", "description": "MP4 Video (H.264)"},
        "mp4_h265": {"codec": "libx265", "description": "MP4 Video (H.265/HEVC)"},
        "mp4_av1": {"codec": "libaom-av1", "description": "MP4 Video (AV1)"},
        "avi": {"codec": "libx264", "description": "AVI Video"},
        "mov": {"codec": "libx264", "description": "QuickTime Video"},
        "mkv": {"codec": "libx264", "description": "Matroska Video (H.264)"},
        "mkv_h265": {"codec": "libx265", "description": "Matroska Video (H.265/HEVC)"},
        "mkv_av1": {"codec": "libaom-av1", "description": "Matroska Video (AV1)"},
        "webm": {"codec": "libvpx-vp9", "description": "WebM Video (VP9)"},
        "webm_vp8": {"codec": "libvpx", "description": "WebM Video (VP8)"},
        "webm_av1": {"codec": "libaom-av1", "description": "WebM Video (AV1)"},
        "flv": {"codec": "libx264", "description": "Flash Video"},
        "wmv": {"codec": "wmv2", "description": "Windows Media Video"},
        "3gp": {"codec": "libx264", "description": "3GP Video"},
        "ogv": {"codec": "libtheora", "description": "Ogg Video"},
        "m4v": {"codec": "libx264", "description": "M4V Video"},
        "ts": {"codec": "libx264", "description": "MPEG Transport Stream"},
        "mts": {"codec": "libx264", "description": "AVCHD Video"},
        "mpg": {"codec": "mpeg2video", "description": "MPEG-1/2 Video"},
        "mpeg": {"codec": "mpeg2video", "description": "MPEG Video"},
        "vob": {"codec": "mpeg2video", "description": "DVD Video"},
        "asf": {"codec": "wmv2", "description": "Advanced Systems Format"},
        "rm": {"codec": "rv20", "description": "RealMedia Video"},
        "divx": {"codec": "libx264", "description": "DivX Video"},
        "xvid": {"codec": "libx264", "description": "Xvid Video"},
    },
    "image": {
        "jpg": {"description": "JPEG Image"},
        "jpeg": {"description": "JPEG Image"},
        "png": {"description": "PNG Image"},
        "webp": {"description": "WebP Image"},
        "bmp": {"description": "Bitmap Image"},
        "tiff": {"description": "TIFF Image"},
        "gif": {"description": "GIF Image"},
        "ico": {"description": "Icon Image"},
        "svg": {"description": "SVG Vector Image"},
        "avif": {"description": "AVIF Image"},
        "heif": {"description": "HEIF Image"},
        "jxl": {"description": "JPEG XL Image"},
    }
}

# Quality presets
QUALITY_PRESETS = {
    "low": {"audio_bitrate": "64k", "video_bitrate": "500k", "crf": "28"},
    "medium": {"audio_bitrate": "128k", "video_bitrate": "1000k", "crf": "23"},
    "high": {"audio_bitrate": "192k", "video_bitrate": "2000k", "crf": "18"},
    "lossless": {"audio_bitrate": "320k", "video_bitrate": "5000k", "crf": "0"},
}

def sanitize_custom_options(custom_options: str) -> list:
    """
    Sanitize custom FFmpeg options to prevent command injection.
    """
    if not custom_options:
        return []
    
    ALLOWED_OPTIONS = {
        '-c:v', '-codec:v', '-vcodec', '-b:v', '-crf', '-preset', '-tune', '-profile:v',
        '-pix_fmt', '-r', '-s', '-aspect', '-vf', '-filter:v',
        '-c:a', '-codec:a', '-acodec', '-b:a', '-ar', '-ac', '-af', '-filter:a',
        '-t', '-ss', '-to', '-f', '-y', '-n', '-threads', '-metadata',
        '-q:v', '-q:a', '-qscale:v', '-qscale:a'
    }
    
    try:
        options = shlex.split(custom_options)
        sanitized = []
        
        i = 0
        while i < len(options):
            option = options[i]
            
            if option in ALLOWED_OPTIONS:
                sanitized.append(option)
                if i + 1 < len(options):
                    arg = options[i + 1]
                    if re.match(r'^[a-zA-Z0-9_:=,.+\-]+$', arg):
                        sanitized.append(arg)
                        i += 1
                    else:
                        logger.warning(f"Unsafe argument for {option}: {arg}")
                        break
            else:
                logger.warning(f"Disallowed FFmpeg option: {option}")
                break
            i += 1
        
        return sanitized
        
    except (ValueError, Exception) as e:
        logger.error(f"Failed to parse custom options: {e}")
        return []

def validate_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF attacks.
    """
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in ['http', 'https']:
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            pass
            
        internal_hosts = {
            'localhost', '127.0.0.1', '0.0.0.0',
            'metadata.google.internal', 'instance-data',
            'metadata.aws.amazon.com'
        }
        if hostname.lower() in internal_hosts:
            return False
            
        return True
        
    except Exception:
        return False

def detect_media_type(content_type: str, filename: str) -> str:
    """Detect if file is audio, video, or image"""
    if content_type.startswith('audio/'):
        return 'audio'
    elif content_type.startswith('video/'):
        return 'video'
    elif content_type.startswith('image/'):
        return 'image'
    else:
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        for media_type, formats in SUPPORTED_FORMATS.items():
            if ext in formats:
                return media_type
    return 'unknown'

def validate_conversion(input_type: str, output_format: str) -> bool:
    """Validate if conversion is possible"""
    if output_format in SUPPORTED_FORMATS.get(input_type, {}):
        return True
    
    valid_cross_conversions = {
        ('video', 'audio'): True,
        ('image', 'video'): True,
        ('video', 'image'): True,
    }
    
    for output_type, formats in SUPPORTED_FORMATS.items():
        if output_format in formats:
            return valid_cross_conversions.get((input_type, output_type), False)
    
    return False

def download_file_from_url(url: str, local_path: str) -> str:
    """Download file from URL to local path"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return local_path
    except Exception as e:
        raise RuntimeError(f"Failed to download file from URL: {str(e)}")

def process_media_convert_sync(input_path: str, output_format: str, quality: str, custom_options: Optional[str]) -> bytes:
    """
    Process media conversion synchronously for quick tasks.
    """
    output_path = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4()}.{output_format}")
    
    cmd = ['ffmpeg', '-i', input_path]
    
    quality_settings = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['medium'])
    
    if output_format in SUPPORTED_FORMATS.get('audio', {}):
        codec_info = SUPPORTED_FORMATS['audio'][output_format]
        cmd.extend(['-c:a', codec_info['codec']])
        if quality_settings:
            cmd.extend(['-b:a', quality_settings.get('audio_bitrate', '128k')])
    elif output_format in SUPPORTED_FORMATS.get('video', {}):
        codec_info = SUPPORTED_FORMATS['video'][output_format]
        cmd.extend(['-c:v', codec_info['codec']])
        if quality_settings:
            cmd.extend(['-crf', str(quality_settings.get('crf', 23))])
    elif output_format in SUPPORTED_FORMATS.get('image', {}):
        if output_format in ['jpg', 'jpeg']:
            cmd.extend(['-q:v', '2'])
        elif output_format == 'png':
            cmd.extend(['-pix_fmt', 'rgba'])
    
    if custom_options:
        sanitized_options = sanitize_custom_options(custom_options)
        cmd.extend(sanitized_options)
    
    cmd.extend(['-y', output_path])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
        with open(output_path, 'rb') as f:
            return f.read()
            
    except subprocess.TimeoutExpired:
        raise RuntimeError("Conversion timed out - file may be too large for sync processing")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

class MediaConversionService:
    """
    Service for handling universal media conversions.
    """

    async def convert_media(
        self,
        job_id: str,
        input_file_path: Optional[str] = None,
        input_file_data: Optional[bytes] = None,
        input_url: Optional[str] = None,
        output_format: str = "mp4",
        quality: str = "medium",
        custom_options: Optional[str] = None,
    ) -> dict:
        """
        Convert media file.
        """
        try:
            # Determine input type and size
            input_type = "unknown"
            file_size = 0
            if input_file_path:
                input_type = detect_media_type(mimetypes.guess_type(input_file_path)[0] or '', os.path.basename(input_file_path))
                file_size = os.path.getsize(input_file_path)
            elif input_file_data:
                # Need to save to temp file to detect type and size
                temp_input_path = os.path.join(tempfile.gettempdir(), f"input_{uuid.uuid4()}.tmp")
                with open(temp_input_path, "wb") as f:
                    f.write(input_file_data)
                input_type = detect_media_type(mimetypes.guess_type(temp_input_path)[0] or '', os.path.basename(temp_input_path))
                file_size = os.path.getsize(temp_input_path)
                os.remove(temp_input_path) # Clean up temp file
            elif input_url:
                if not validate_url(input_url):
                    raise ValueError("Invalid or unsafe URL provided.")
                try:
                    response = requests.head(input_url, timeout=10)
                    response.raise_for_status()
                    content_type = response.headers.get('content-type', '')
                    filename = input_url.split('/')[-1] if '/' in input_url else 'unknown'
                    input_type = detect_media_type(content_type, filename)
                    file_size = int(response.headers.get('content-length', 0))
                except requests.RequestException as e:
                    raise ValueError(f"Cannot access URL: {str(e)}")

            if input_type == "unknown":
                raise ValueError("Cannot determine media type from input.")

            if not validate_conversion(input_type, output_format):
                raise ValueError(f"Cannot convert {input_type} to {output_format} format.")

            params = {
                "input_file_path": input_file_path,
                "input_file_data": input_file_data,
                "input_url": input_url,
                "output_format": output_format,
                "quality": quality,
                "custom_options": custom_options,
                "input_type": input_type,
                "file_size": file_size,
            }

            # Create wrapper function that matches job queue signature
            async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
                return await self.process_conversion(data)
            
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.MEDIA_CONVERSION,
                process_func=process_wrapper,
                data=params,
            )

            return {"job_id": job_id}
        except Exception as e:
            logger.error(f"Error creating media conversion job: {e}")
            raise

    async def process_conversion_with_file_data(self, file_content: bytes, params: dict) -> dict:
        """
        Process media conversion with binary file data (not stored in job params).
        """
        try:
            # Add the binary file data to params for processing
            params_with_file = params.copy()
            params_with_file["input_file_data"] = file_content
            
            # Process using the existing logic
            return await self.process_conversion(params_with_file)
        except Exception as e:
            logger.error(f"Error processing media conversion with file data: {e}")
            raise

    async def process_conversion(self, params: dict) -> dict:
        """
        Process the media conversion.
        """
        input_file_path = params.get("input_file_path")
        input_file_data = params.get("input_file_data")
        file_data_b64 = params.get("file_data")  # Base64 encoded file data from form
        filename = params.get("filename")
        content_type = params.get("content_type")
        input_url = params.get("input_url")
        input_type = params.get("input_type")
        output_format = params["output_format"]
        quality = params["quality"]
        custom_options = params.get("custom_options")
        
        # Handle base64 encoded file data from multipart form
        if file_data_b64 and not input_file_data:
            try:
                input_file_data = base64.b64decode(file_data_b64)
                if not input_type and (filename or content_type):
                    input_type = detect_media_type(content_type or '', filename or '')
            except Exception as e:
                raise ValueError(f"Failed to decode uploaded file data: {str(e)}")

        temp_input_path = None
        output_data = None
        file_size = params.get("file_size", 0)
        
        try:
            if input_url:
                temp_input_path = os.path.join(tempfile.gettempdir(), f"input_{uuid.uuid4()}.tmp")
                download_file_from_url(input_url, temp_input_path)
                input_file_path = temp_input_path
                # Get file size if not provided
                if not file_size:
                    file_size = os.path.getsize(temp_input_path)
                
                # Detect media type for URL-based conversions
                if input_type == "url":
                    try:
                        response = requests.head(input_url, timeout=10)
                        response.raise_for_status()
                        content_type = response.headers.get('content-type', '')
                        filename = input_url.split('/')[-1] if '/' in input_url else 'unknown'
                        input_type = detect_media_type(content_type, filename)
                        if input_type == "unknown":
                            # Fallback: try to detect from downloaded file
                            input_type = detect_media_type(mimetypes.guess_type(temp_input_path)[0] or '', os.path.basename(temp_input_path))
                    except Exception as e:
                        logger.warning(f"Failed to detect media type from URL headers: {e}")
                        # Fallback: detect from downloaded file
                        input_type = detect_media_type(mimetypes.guess_type(temp_input_path)[0] or '', os.path.basename(temp_input_path))
            elif input_file_data:
                # Create temp file with original extension if available
                file_ext = ''
                if filename:
                    file_ext = os.path.splitext(filename)[1]
                temp_input_path = os.path.join(tempfile.gettempdir(), f"input_{uuid.uuid4()}{file_ext}")
                with open(temp_input_path, "wb") as f:
                    f.write(input_file_data)
                input_file_path = temp_input_path
                file_size = len(input_file_data)
                
                # Detect media type if not provided
                if not input_type:
                    input_type = detect_media_type(content_type or mimetypes.guess_type(temp_input_path)[0] or '', filename or os.path.basename(temp_input_path))

            # Validate that we have an input file path
            if not input_file_path:
                raise ValueError("No input file provided (input_file_path, input_url, or input_file_data required)")
                
            # Validate input type and conversion
            if not input_type or input_type == "unknown":
                raise ValueError("Cannot determine media type from input file")
                
            if not validate_conversion(input_type, output_format):
                raise ValueError(f"Cannot convert {input_type} to {output_format} format")
            
            # All conversions now upload to S3 for consistency
            # Create temporary output file
            output_path = os.path.join(tempfile.gettempdir(), f"output_{uuid.uuid4()}.{output_format}")
            
            try:
                if self._should_process_sync(file_size or 0, input_type, output_format):
                    # Use synchronous processing but still upload to S3
                    output_data = await asyncio.get_event_loop().run_in_executor(
                        None, # Use default thread pool
                        lambda: process_media_convert_sync(input_file_path, output_format, quality, custom_options)
                    )
                    # Write to temporary file then upload to S3
                    with open(output_path, 'wb') as f:
                        f.write(output_data)
                else:
                    # Asynchronous FFmpeg processing
                    cmd = ['ffmpeg', '-i', input_file_path]
                    quality_settings = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['medium'])

                    if output_format in SUPPORTED_FORMATS.get('audio', {}):
                        codec_info = SUPPORTED_FORMATS['audio'][output_format]
                        cmd.extend(['-c:a', codec_info['codec']])
                        if quality_settings:
                            cmd.extend(['-b:a', quality_settings.get('audio_bitrate', '128k')])
                    elif output_format in SUPPORTED_FORMATS.get('video', {}):
                        codec_info = SUPPORTED_FORMATS['video'][output_format]
                        cmd.extend(['-c:v', codec_info['codec']])
                        if quality_settings:
                            cmd.extend(['-crf', str(quality_settings.get('crf', 23))])
                    elif output_format in SUPPORTED_FORMATS.get('image', {}):
                        if output_format in ['jpg', 'jpeg']:
                            cmd.extend(['-q:v', '2'])
                        elif output_format == 'png':
                            cmd.extend(['-pix_fmt', 'rgba'])

                    if custom_options:
                        sanitized_options = sanitize_custom_options(custom_options)
                        cmd.extend(sanitized_options)

                    cmd.extend(['-y', output_path])

                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
                
                # Upload result to S3
                s3_key = f"conversions/{os.path.basename(output_path)}"
                file_url = await s3_service.upload_file(output_path, s3_key)
                return {"file_url": file_url}
                
            finally:
                # Clean up temporary output file
                if os.path.exists(output_path):
                    os.remove(output_path)
            # This block is now handled above in the unified approach

        except Exception as e:
            logger.error(f"Error processing media conversion: {e}")
            raise
        finally:
            if temp_input_path and os.path.exists(temp_input_path):
                os.remove(temp_input_path)

    def _should_process_sync(self, file_size: int, input_type: str, output_format: str) -> bool:
        """
        Determine if conversion should be processed synchronously or asynchronously.
        """
        # Always async for large files (>10MB)
        if file_size and file_size > 10 * 1024 * 1024:
            return False
        
        # Quick conversions that should be processed synchronously
        quick_conversions = [
            ('image', 'webp'), ('image', 'jpeg'), ('image', 'jpg'), ('image', 'png'),
            ('image', 'avif'), ('image', 'gif'), ('image', 'bmp'), ('image', 'tiff'),
            ('audio', 'mp3'), ('audio', 'wav'), ('audio', 'ogg'), ('audio', 'oga'), ('audio', 'aac'),
            ('audio', 'flac'), ('audio', 'opus'), ('audio', 'm4a'),
            ('video', 'mp3'), ('video', 'wav'), ('video', 'aac')
        ]
        
        return (input_type, output_format) in quick_conversions

media_conversion_service = MediaConversionService()
