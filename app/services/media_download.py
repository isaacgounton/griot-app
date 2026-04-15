"""
Advanced media download service using yt-dlp with comprehensive platform support.
Supports YouTube, Vimeo, social media platforms, and advanced features like cookies,
subtitle extraction, thumbnail conversion, and format selection.
"""
import os
import uuid
import asyncio
import tempfile
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import aiofiles
import aiohttp

from app.utils.media import download_media_file
from app.services.s3 import s3_service
from app.utils.logging import get_logger

logger = get_logger(module="media_download", component="service")

class MediaType(str, Enum):
    """Supported media types."""
    VIDEO = "video"
    AUDIO = "audio"
    PLAYLIST = "playlist"
    SUBTITLE = "subtitle"
    THUMBNAIL = "thumbnail"

class VideoQuality(str, Enum):
    """Video quality options."""
    HIGHEST = "highest"
    HIGH = "720p"
    MEDIUM = "480p"
    LOW = "360p"
    LOWEST = "lowest"
    CUSTOM = "custom"

class AudioQuality(str, Enum):
    """Audio quality options."""
    HIGHEST = "highest"
    HIGH = "192"
    MEDIUM = "128"
    LOW = "96"
    LOWEST = "64"

class SubtitleFormat(str, Enum):
    """Supported subtitle formats."""
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"
    JSON3 = "json3"

@dataclass
class DownloadOptions:
    """Download options for media extraction."""
    # Basic options
    media_type: MediaType = MediaType.VIDEO
    quality: VideoQuality = VideoQuality.HIGHEST
    audio_quality: AudioQuality = AudioQuality.HIGHEST

    # Format selection
    video_format: Optional[str] = None  # e.g., "mp4", "webm", "avi"
    audio_format: Optional[str] = None  # e.g., "mp3", "wav", "aac"
    codec: Optional[str] = None  # e.g., "h264", "vp9", "av1"

    # Subtitle options
    extract_subtitles: bool = False
    subtitle_languages: List[str] = field(default_factory=lambda: ["en", "auto"])
    subtitle_formats: List[SubtitleFormat] = field(default_factory=lambda: [SubtitleFormat.SRT, SubtitleFormat.VTT])

    # Thumbnail options
    extract_thumbnail: bool = False
    thumbnail_format: str = "jpg"
    thumbnail_size: Optional[str] = None  # e.g., "1280x720"

    # Advanced options
    cookies_file: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    rate_limit: Optional[str] = None  # e.g., "50M"
    retry_times: int = 3
    timeout: int = 300  # seconds

    # Output options
    output_filename: Optional[str] = None
    embed_metadata: bool = True
    embed_thumbnail: bool = False
    embed_subtitles: bool = False

@dataclass
class MediaInfo:
    """Media information extracted from URL."""
    id: str
    title: str
    description: Optional[str] = None
    uploader: Optional[str] = None
    duration: Optional[float] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    thumbnail: Optional[str] = None
    webpage_url: Optional[str] = None
    formats: List[Dict[str, Any]] = field(default_factory=list)
    subtitles: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    chapters: Optional[List[Dict[str, Any]]] = None

@dataclass
class DownloadResult:
    """Result of media download operation."""
    success: bool
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subtitle_urls: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

class YTDLPService:
    """Advanced media download service using yt-dlp."""

    def __init__(self):
        """Initialize the yt-dlp service."""
        self.temp_dir = tempfile.gettempdir()

    async def _get_media_info(self, url: str, options: DownloadOptions) -> MediaInfo:
        """Extract media information without downloading."""
        try:
            logger.info(f"🔍 Extracting media info from: {url}")

            # Build yt-dlp command for info extraction
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-warnings",
                url
            ]

            # Add cookies if provided
            if options.cookies_file:
                cmd.extend(["--cookies", options.cookies_file])

            # Add custom headers
            if options.custom_headers:
                for key, value in options.custom_headers.items():
                    cmd.extend(["--add-header", f"{key}:{value}"])

            # Add user agent
            if options.user_agent:
                cmd.extend(["--user-agent", options.user_agent])

            # Add proxy
            if options.proxy:
                cmd.extend(["--proxy", options.proxy])

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"❌ Failed to extract media info: {error_msg}")
                raise Exception(f"Media info extraction failed: {error_msg}")

            # Parse JSON response
            info_json = json.loads(stdout.decode())

            return MediaInfo(
                id=info_json.get('id', ''),
                title=info_json.get('title', 'Unknown'),
                description=info_json.get('description'),
                uploader=info_json.get('uploader'),
                duration=info_json.get('duration'),
                upload_date=info_json.get('upload_date'),
                view_count=info_json.get('view_count'),
                like_count=info_json.get('like_count'),
                thumbnail=info_json.get('thumbnail'),
                webpage_url=info_json.get('webpage_url'),
                formats=info_json.get('formats', []),
                subtitles=info_json.get('subtitles', {}),
                chapters=info_json.get('chapters')
            )

        except Exception as e:
            logger.error(f"❌ Error extracting media info: {e}")
            raise

    def _build_format_selector(self, options: DownloadOptions) -> str:
        """Build yt-dlp format selector string."""
        if options.quality == VideoQuality.HIGHEST:
            if options.media_type == MediaType.AUDIO:
                return "bestaudio"
            else:
                return "best[ext=mp4]/best"

        elif options.quality == VideoQuality.HIGH:
            if options.media_type == MediaType.AUDIO:
                return f"bestaudio[abr<={options.audio_quality.value}]/bestaudio"
            else:
                return f"best[height<=720][ext=mp4]/best[height<=720]"

        elif options.quality == VideoQuality.MEDIUM:
            if options.media_type == MediaType.AUDIO:
                return f"bestaudio[abr<={options.audio_quality.value}]/bestaudio"
            else:
                return f"best[height<=480][ext=mp4]/best[height<=480]"

        elif options.quality == VideoQuality.LOW:
            if options.media_type == MediaType.AUDIO:
                return f"bestaudio[abr<={options.audio_quality.value}]/bestaudio"
            else:
                return f"best[height<=360][ext=mp4]/best[height<=360]"

        else:
            return "worst"

    async def _download_media(self, url: str, options: DownloadOptions, job_id: str) -> Tuple[str, str]:
        """Download media file and return local path and extension."""
        try:
            logger.info(f"⬇️ Downloading media from: {url}")

            # Generate output filename
            if options.output_filename:
                base_name = options.output_filename
            else:
                base_name = f"{job_id}_media"

            output_template = os.path.join(self.temp_dir, f"{base_name}.%(ext)s")

            # Build yt-dlp command
            cmd = [
                "yt-dlp",
                "--no-warnings",
                "--progress",
                "--newline",
                "--retries", str(options.retry_times),
                "--timeout", str(options.timeout),
                "--output", output_template
            ]

            # Add format selector
            format_selector = self._build_format_selector(options)
            cmd.extend(["--format", format_selector])

            # Add cookies if provided
            if options.cookies_file:
                cmd.extend(["--cookies", options.cookies_file])

            # Add custom headers
            for key, value in options.custom_headers.items():
                cmd.extend(["--add-header", f"{key}:{value}"])

            # Add user agent
            if options.user_agent:
                cmd.extend(["--user-agent", options.user_agent])

            # Add proxy
            if options.proxy:
                cmd.extend(["--proxy", options.proxy])

            # Add rate limit
            if options.rate_limit:
                cmd.extend(["--limit-rate", options.rate_limit])

            # Add embedding options
            if options.embed_metadata:
                cmd.append("--embed-metadata")

            if options.embed_thumbnail:
                cmd.append("--embed-thumbnail")

            if options.embed_subtitles:
                cmd.append("--embed-subs")

            # Add format conversion
            postprocessors = []

            if options.media_type == MediaType.AUDIO and options.audio_format:
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': options.audio_format,
                    'preferredquality': options.audio_quality.value
                })

            if options.video_format and options.media_type != MediaType.AUDIO:
                postprocessors.append({
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': options.video_format
                })

            if postprocessors:
                cmd.extend(["--postprocessor-args", json.dumps(postprocessors)])

            # Add the URL
            cmd.append(url)

            # Execute download
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"❌ Download failed: {error_msg}")
                raise Exception(f"Download failed: {error_msg}")

            # Find the downloaded file
            downloaded_files = []
            for file in os.listdir(self.temp_dir):
                if file.startswith(base_name):
                    full_path = os.path.join(self.temp_dir, file)
                    if os.path.isfile(full_path):
                        downloaded_files.append(full_path)

            if not downloaded_files:
                raise Exception("No downloaded file found")

            # Return the main media file (usually the largest)
            main_file = max(downloaded_files, key=lambda f: os.path.getsize(f))
            extension = os.path.splitext(main_file)[1].lstrip('.')

            logger.info(f"✅ Media downloaded to: {main_file}")
            return main_file, extension

        except Exception as e:
            logger.error(f"❌ Error downloading media: {e}")
            raise

    async def _download_subtitles(self, url: str, options: DownloadOptions, job_id: str) -> List[Tuple[str, str]]:
        """Download subtitle files."""
        if not options.extract_subtitles:
            return []

        try:
            logger.info(f"📄 Downloading subtitles for: {url}")

            subtitle_files = []

            for lang in options.subtitle_languages:
                for format_type in options.subtitle_formats:
                    try:
                        # Generate output filename
                        subtitle_filename = f"{job_id}_subtitles_{lang}.{format_type.value}"
                        subtitle_path = os.path.join(self.temp_dir, subtitle_filename)

                        # Build yt-dlp command for subtitles
                        cmd = [
                            "yt-dlp",
                            "--write-subs",
                            "--write-auto-subs",
                            "--sub-langs", lang,
                            "--sub-format", format_type.value,
                            "--convert-subs", format_type.value,
                            "--output", os.path.join(self.temp_dir, f"{job_id}_subtitles.%(ext)s"),
                            "--skip-download",
                            url
                        ]

                        # Add cookies if provided
                        if options.cookies_file:
                            cmd.extend(["--cookies", options.cookies_file])

                        # Execute subtitle download
                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )

                        await process.communicate()

                        # Find downloaded subtitle file
                        for file in os.listdir(self.temp_dir):
                            if file.startswith(f"{job_id}_subtitles") and file.endswith(f".{format_type.value}"):
                                full_path = os.path.join(self.temp_dir, file)
                                subtitle_files.append((full_path, format_type.value))
                                break

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to download subtitle {lang} in {format_type.value}: {e}")
                        continue

            logger.info(f"✅ Downloaded {len(subtitle_files)} subtitle files")
            return subtitle_files

        except Exception as e:
            logger.error(f"❌ Error downloading subtitles: {e}")
            return []

    async def _download_thumbnail(self, url: str, options: DownloadOptions, job_id: str) -> Optional[str]:
        """Download thumbnail image."""
        if not options.extract_thumbnail:
            return None

        try:
            logger.info(f"🖼️ Downloading thumbnail for: {url}")

            # First get media info to find thumbnail URL
            media_info = await self._get_media_info(url, options)

            if not media_info.thumbnail:
                logger.warning("⚠️ No thumbnail found")
                return None

            # Download thumbnail using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(media_info.thumbnail) as response:
                    if response.status == 200:
                        thumbnail_filename = f"{job_id}_thumbnail.{options.thumbnail_format}"
                        thumbnail_path = os.path.join(self.temp_dir, thumbnail_filename)

                        content = await response.read()
                        async with aiofiles.open(thumbnail_path, 'wb') as f:
                            await f.write(content)

                        logger.info(f"✅ Thumbnail downloaded to: {thumbnail_path}")
                        return thumbnail_path
                    else:
                        logger.error(f"❌ Failed to download thumbnail: HTTP {response.status}")
                        return None

        except Exception as e:
            logger.error(f"❌ Error downloading thumbnail: {e}")
            return None

    async def download_media(self, url: str, options: DownloadOptions) -> DownloadResult:
        """Download media with comprehensive options."""
        import time
        start_time = time.time()

        job_id = str(uuid.uuid4())
        media_file = None
        thumbnail_file = None
        subtitle_files = []

        try:
            logger.info(f"🚀 Starting advanced media download: {url}")

            # Download main media
            media_file, media_extension = await self._download_media(url, options, job_id)

            # Download subtitles if requested
            subtitle_files = await self._download_subtitles(url, options, job_id)

            # Download thumbnail if requested
            thumbnail_file = await self._download_thumbnail(url, options, job_id)

            # Upload main media to S3
            media_s3_key = f"media/downloads/{job_id}.{media_extension}"
            media_s3_url = await s3_service.upload_file(media_file, media_s3_key)

            # Upload thumbnail to S3
            thumbnail_s3_url = None
            if thumbnail_file:
                thumbnail_extension = os.path.splitext(thumbnail_file)[1].lstrip('.')
                thumbnail_s3_key = f"media/thumbnails/{job_id}.{thumbnail_extension}"
                thumbnail_s3_url = await s3_service.upload_file(thumbnail_file, thumbnail_s3_key)

            # Upload subtitles to S3
            subtitle_s3_urls = []
            for subtitle_file, subtitle_format in subtitle_files:
                subtitle_s3_key = f"media/subtitles/{job_id}_{subtitle_format}.{subtitle_format}"
                subtitle_s3_url = await s3_service.upload_file(subtitle_file, subtitle_s3_key)
                subtitle_s3_urls.append(subtitle_s3_url)

            # Get media info for metadata
            try:
                media_info = await self._get_media_info(url, options)
                metadata = {
                    "job_id": job_id,
                    "url": url,
                    "media_type": options.media_type.value,
                    "title": media_info.title,
                    "description": media_info.description,
                    "uploader": media_info.uploader,
                    "duration": media_info.duration,
                    "upload_date": media_info.upload_date,
                    "view_count": media_info.view_count,
                    "quality": options.quality.value,
                    "format": media_extension,
                    "has_subtitles": len(subtitle_s3_urls) > 0,
                    "has_thumbnail": thumbnail_s3_url is not None
                }
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract metadata: {e}")
                metadata = {
                    "job_id": job_id,
                    "url": url,
                    "media_type": options.media_type.value,
                    "quality": options.quality.value,
                    "format": media_extension,
                    "has_subtitles": len(subtitle_s3_urls) > 0,
                    "has_thumbnail": thumbnail_s3_url is not None
                }

            execution_time = time.time() - start_time

            logger.info(f"✅ Media download completed in {execution_time:.2f}s")

            return DownloadResult(
                success=True,
                media_url=media_s3_url,
                thumbnail_url=thumbnail_s3_url,
                subtitle_urls=subtitle_s3_urls,
                metadata=metadata,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Media download failed: {str(e)}"
            logger.error(f"❌ {error_msg}")

            return DownloadResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )

        finally:
            # Clean up temporary files
            for file_path in [media_file, thumbnail_file] + [f[0] for f in subtitle_files]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to clean up file {file_path}: {e}")

    async def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms."""
        try:
            cmd = ["yt-dlp", "--list-extractors"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Extract platform names from output
                lines = stdout.decode().split('\n')
                platforms = [line.strip() for line in lines if line.strip() and not line.startswith(' ')]
                return platforms
            else:
                logger.warning("Failed to get supported platforms list")
                return []

        except Exception as e:
            logger.error(f"Error getting supported platforms: {e}")
            return []

# Global service instance
ytdlp_service = YTDLPService()

# Job queue wrapper function
async def process_media_download_job(_job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a media download job through the job queue."""
    try:
        # Extract parameters
        url = data.get("url")
        if not url:
            raise ValueError("URL is required")

        # Build download options
        options = DownloadOptions(
            media_type=MediaType(data.get("media_type", "video")),
            quality=VideoQuality(data.get("quality", "highest")),
            audio_quality=AudioQuality(data.get("audio_quality", "highest")),
            video_format=data.get("video_format"),
            audio_format=data.get("audio_format"),
            codec=data.get("codec"),
            extract_subtitles=data.get("extract_subtitles", False),
            subtitle_languages=data.get("subtitle_languages", ["en", "auto"]),
            subtitle_formats=[SubtitleFormat(fmt) for fmt in data.get("subtitle_formats", ["srt", "vtt"])],
            extract_thumbnail=data.get("extract_thumbnail", False),
            thumbnail_format=data.get("thumbnail_format", "jpg"),
            thumbnail_size=data.get("thumbnail_size"),
            cookies_file=data.get("cookies_file"),
            custom_headers=data.get("custom_headers", {}),
            user_agent=data.get("user_agent"),
            proxy=data.get("proxy"),
            rate_limit=data.get("rate_limit"),
            retry_times=data.get("retry_times", 3),
            timeout=data.get("timeout", 300),
            output_filename=data.get("output_filename"),
            embed_metadata=data.get("embed_metadata", True),
            embed_thumbnail=data.get("embed_thumbnail", False),
            embed_subtitles=data.get("embed_subtitles", False)
        )

        # Process download
        result = await ytdlp_service.download_media(url, options)

        if result.success:
            return {
                "success": True,
                "media_url": result.media_url,
                "thumbnail_url": result.thumbnail_url,
                "subtitle_urls": result.subtitle_urls,
                "metadata": result.metadata,
                "execution_time": result.execution_time
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "execution_time": result.execution_time
            }

    except Exception as e:
        logger.error(f"❌ Media download job processing failed: {e}")
        return {
            "success": False,
            "error": f"Job processing failed: {str(e)}"
        }