"""
Service for handling media downloads using yt-dlp with fallback to direct HTTP download.
"""
from app.services.job_queue import job_queue
from app.models import JobType
from app.services.s3.s3 import s3_service
from app.utils.download import download_file
import logging
import os
import yt_dlp
import tempfile
import requests
import aiohttp
import uuid
from urllib.parse import urlparse, unquote
from pathlib import Path

logger = logging.getLogger(__name__)

class DownloadService:
    """
    Service for handling media downloads with universal file support.

    This service can download:
    - Media files from video platforms (YouTube, Vimeo, etc.) using yt-dlp
    - Direct file downloads (PDFs, images, documents, etc.) using HTTP
    - Files with authentication via cookies
    """

    def _is_likely_media_platform(self, url: str) -> bool:
        """
        Check if URL is likely from a media platform that yt-dlp can handle.
        """
        media_domains = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com',
            'twitch.tv', 'twitter.com', 'x.com', 'instagram.com',
            'facebook.com', 'tiktok.com', 'soundcloud.com', 'spotify.com'
        ]

        parsed = urlparse(url.lower())
        domain = parsed.netloc.lower()

        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        return any(media_domain in domain for media_domain in media_domains)

    def _get_file_extension_from_url(self, url: str) -> str:
        """
        Extract file extension from URL.
        """
        parsed = urlparse(url)
        path = unquote(parsed.path)
        return Path(path).suffix or ""

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by replacing spaces and special characters with underscores.
        This creates clean URLs without URL encoding.
        """
        import re
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        # Replace multiple consecutive underscores with single underscore
        filename = re.sub(r'_+', '_', filename)
        # Remove or replace other problematic characters
        # Keep only alphanumeric, underscores, hyphens, and dots
        filename = re.sub(r'[^\w\-\.]', '_', filename, flags=re.UNICODE)
        # Remove consecutive underscores again after character replacement
        filename = re.sub(r'_+', '_', filename)
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        return filename

    def _generate_filename(self, url: str, custom_name: str = None) -> str:
        """
        Generate appropriate filename for download.
        """
        if custom_name:
            return self._sanitize_filename(custom_name)

        # Extract filename from URL
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = Path(path).name

        if filename and '.' in filename:
            return self._sanitize_filename(filename)

        # Generate fallback filename
        extension = self._get_file_extension_from_url(url) or ""
        return f"download_{uuid.uuid4().hex[:8]}{extension}"

    async def download_media(self, job_id: str, url: str, file_name: str, cookies_url: str) -> dict:
        """
        Download media from a URL.
        """
        try:
            params = {"url": url, "file_name": file_name, "cookies_url": cookies_url}

            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.MEDIA_DOWNLOAD,
                process_func=self.process_media_download,
                data=params,
            )

            return {"job_id": job_id}
        except Exception as e:
            logger.error(f"Error creating media download job: {e}")
            raise

    async def process_media_download(self, job_id: str, params: dict) -> dict:
        """
        Process the media download with fallback support.

        First tries yt-dlp for media platforms, then falls back to direct HTTP download.

        Args:
            job_id: The ID of the job being processed
            params: Dictionary containing download parameters
        """
        url = params["url"]
        file_name = params.get("file_name")
        cookies_url = params.get("cookies_url")
        format_param = params.get("format", "best")

        logger.info(f"Starting download for URL: {url}")

        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)

        # Try yt-dlp first if it's likely a media platform
        if self._is_likely_media_platform(url):
            logger.info("Attempting download with yt-dlp (media platform detected)")
            try:
                return await self._download_with_ytdlp(url, file_name, cookies_url, format_param)
            except Exception as e:
                logger.warning(f"yt-dlp download failed: {e}. Falling back to direct download.")

        # Fall back to direct HTTP download
        logger.info("Attempting direct HTTP download")
        return await self._download_direct(url, file_name, cookies_url)

    async def _download_with_ytdlp(self, url: str, file_name: str, cookies_url: str, format_param: str) -> dict:
        """
        Download using yt-dlp for media platforms.
        """
        cookies_file_path = None
        try:
            # Configure yt-dlp options with enhanced features
            filename = file_name or '%(title)s.%(ext)s'
            ydl_opts = {
                "outtmpl": f"temp/{filename}",
                "quiet": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
                "extractor_retries": 3,
                "retries": 3,
                "fragment_retries": 3,
                "skip_unavailable_fragments": True,
                # Enhanced features from no-code-architects-toolkit
                "writesubtitles": False,  # Will be controlled by parameters
                "writeautomaticsub": False,
                "subtitleslangs": ["en", "auto"],
                "subtitlesformat": "srt",
                "writethumbnail": False,  # Will be controlled by parameters
                "postprocessors": [],
                "embed_metadata": True,
            }

            # Handle format parameter
            if format_param and format_param != "best":
                if format_param == "mp3":
                    ydl_opts["format"] = "bestaudio/best"
                    ydl_opts["postprocessors"] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                elif format_param == "mp4":
                    ydl_opts["format"] = "best[ext=mp4]/best"
                else:
                    ydl_opts["format"] = format_param
            else:
                # Default format selection for server environments
                ydl_opts["format"] = "best[height<=1080][ext=mp4]/best[height<=720][ext=mp4]/best[ext=mp4]/best"

            # Handle cookies
            if cookies_url:
                logger.info(f"Downloading cookies from {cookies_url}")
                response = requests.get(cookies_url)
                response.raise_for_status()

                cookies_file_path = tempfile.NamedTemporaryFile(delete=False).name
                with open(cookies_file_path, "w") as f:
                    f.write(response.text)
                ydl_opts["cookiefile"] = cookies_file_path
                logger.info(f"Using cookies from {cookies_file_path}")
            else:
                # Try auto-extract from Playwright profile
                try:
                    from app.utils.youtube_cookies import get_cookies_for_ytdlp
                    auto_path = await get_cookies_for_ytdlp()
                    if auto_path and os.path.exists(auto_path):
                        ydl_opts["cookiefile"] = auto_path
                        logger.info(f"Using auto-extracted cookies from {auto_path}")
                except Exception as e:
                    logger.debug(f"Auto cookie extraction not available: {e}")

            # Download with yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            # Upload to S3 with sanitized filename and path prefix
            sanitized_filename = self._sanitize_filename(os.path.basename(file_path))
            s3_key = f"downloads/{sanitized_filename}"
            file_url = await s3_service.upload_file(
                file_path=file_path,
                object_name=s3_key,
            )

            return {
                "file_url": file_url,
                "path": file_path,
                "title": info.get("title", "Downloaded Media"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "upload_date": info.get("upload_date"),
                "download_method": "yt-dlp"
            }

        finally:
            if cookies_file_path and os.path.exists(cookies_file_path):
                os.remove(cookies_file_path)
                logger.info(f"Removed temporary cookies file: {cookies_file_path}")

    async def _download_direct(self, url: str, file_name: str, cookies_url: str) -> dict:
        """
        Download file directly via HTTP.
        """
        try:
            # Generate filename
            filename = self._generate_filename(url, file_name)
            file_path = os.path.join("temp", filename)

            # Prepare headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # Handle cookies if provided
            cookies = None
            if cookies_url:
                logger.info(f"Downloading cookies from {cookies_url}")
                try:
                    response = requests.get(cookies_url)
                    response.raise_for_status()
                    # Parse cookies (assuming simple format)
                    cookies = {}
                    for line in response.text.strip().split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            cookies[key.strip()] = value.strip()
                except Exception as e:
                    logger.warning(f"Failed to load cookies: {e}")

            # Download file
            async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

                    # Get content info
                    content_length = response.headers.get('content-length')
                    content_type = response.headers.get('content-type', 'application/octet-stream')

                    logger.info(f"Downloading {content_length or 'unknown size'} bytes of {content_type}")

                    # Save file
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

            # Upload to S3 with sanitized filename and path prefix
            sanitized_filename = self._sanitize_filename(os.path.basename(file_path))
            s3_key = f"downloads/{sanitized_filename}"
            file_url = await s3_service.upload_file(
                file_path=file_path,
                object_name=s3_key,
            )

            # Get file info
            file_size = os.path.getsize(file_path)

            return {
                "file_url": file_url,
                "path": file_path,
                "title": os.path.splitext(filename)[0],
                "file_size": file_size,
                "content_type": content_type,
                "download_method": "direct"
            }

        except Exception as e:
            logger.error(f"Direct download failed: {e}")
            raise

    async def process_enhanced_media_download(self, job_id: str, params: dict) -> dict:
        """
        Process enhanced media download with subtitle and thumbnail extraction.

        Args:
            job_id: The ID of the job being processed
            params: Dictionary containing download parameters including:
                - url: URL to download
                - format: Format selector
                - file_name: Custom filename
                - cookies_url: URL to cookies file
                - extract_subtitles: Boolean to extract subtitles
                - subtitle_languages: List of subtitle languages
                - subtitle_formats: List of subtitle formats
                - extract_thumbnail: Boolean to extract thumbnail
                - embed_metadata: Boolean to embed metadata
        """
        url = params["url"]
        format_param = params.get("format", "best")
        file_name = params.get("file_name")
        cookies_url = params.get("cookies_url")
        extract_subtitles = params.get("extract_subtitles", False)
        subtitle_languages = params.get("subtitle_languages", ["en", "auto"])
        subtitle_formats = params.get("subtitle_formats", ["srt", "vtt"])
        extract_thumbnail = params.get("extract_thumbnail", False)
        embed_metadata = params.get("embed_metadata", True)

        logger.info(f"Starting enhanced download for URL: {url}")

        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)

        cookies_file_path = None
        cookies_is_temp = False  # Track if cookies file should be cleaned up
        downloaded_files = []

        try:
            # Handle cookies
            if cookies_url:
                logger.info(f"Downloading cookies from {cookies_url}")
                response = requests.get(cookies_url)
                response.raise_for_status()

                cookies_file_path = tempfile.NamedTemporaryFile(delete=False).name
                cookies_is_temp = True
                with open(cookies_file_path, "w") as f:
                    f.write(response.text)
                logger.info(f"Using cookies from {cookies_file_path}")
            else:
                # Try auto-extract from Playwright profile (shared file, don't delete)
                try:
                    from app.utils.youtube_cookies import get_cookies_for_ytdlp
                    auto_path = await get_cookies_for_ytdlp()
                    if auto_path and os.path.exists(auto_path):
                        cookies_file_path = auto_path
                        logger.info(f"Using auto-extracted cookies from {auto_path}")
                except Exception as e:
                    logger.debug(f"Auto cookie extraction not available: {e}")

            # Configure yt-dlp options with enhanced features
            filename = file_name or '%(title)s.%(ext)s'
            ydl_opts = {
                "outtmpl": f"temp/{filename}",
                "quiet": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
                "extractor_retries": 3,
                "retries": 3,
                "fragment_retries": 3,
                "skip_unavailable_fragments": True,
                "writesubtitles": extract_subtitles,
                "writeautomaticsub": extract_subtitles,
                "subtitleslangs": subtitle_languages,
                "subtitlesformat": subtitle_formats[0] if subtitle_formats else "srt",
                "writethumbnail": extract_thumbnail,
                "postprocessors": [],
                "embed_metadata": embed_metadata,
            }

            # Add cookies file if available
            if cookies_file_path:
                ydl_opts["cookiefile"] = cookies_file_path

            # Handle format parameter
            if format_param and format_param != "best":
                if format_param == "mp3":
                    ydl_opts["format"] = "bestaudio/best"
                    ydl_opts["postprocessors"].append({
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    })
                elif format_param == "mp4":
                    ydl_opts["format"] = "best[ext=mp4]/best"
                elif format_param.endswith("p"):
                    # Quality selector like "720p", "480p"
                    height = format_param[:-1]
                    ydl_opts["format"] = f"best[height<={height}]/best"
                else:
                    ydl_opts["format"] = format_param
            else:
                ydl_opts["format"] = "best[height<=1080][ext=mp4]/best[height<=720][ext=mp4]/best[ext=mp4]/best"

            # Add subtitle format conversion postprocessors
            if extract_subtitles and len(subtitle_formats) > 1:
                for subtitle_format in subtitle_formats[1:]:
                    ydl_opts["postprocessors"].append({
                        'key': 'FFmpegSubtitlesConvertor',
                        'format': subtitle_format,
                    })

            # Add thumbnail conversion postprocessor
            if extract_thumbnail:
                ydl_opts["postprocessors"].append({
                    'key': 'FFmpegThumbnailsConvertor',
                    'format': 'jpg',
                })

            # Download with yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                main_file_path = ydl.prepare_filename(info)
                downloaded_files.append(main_file_path)

                # Collect additional files (subtitles, thumbnails)
                temp_dir = os.path.dirname(main_file_path)
                base_name = os.path.splitext(os.path.basename(main_file_path))[0]

                for file in os.listdir(temp_dir):
                    if file.startswith(base_name) and file != os.path.basename(main_file_path):
                        full_path = os.path.join(temp_dir, file)
                        if os.path.isfile(full_path):
                            downloaded_files.append(full_path)

            # Upload all files to S3
            uploaded_files = []
            for file_path in downloaded_files:
                if os.path.exists(file_path):
                    sanitized_filename = self._sanitize_filename(os.path.basename(file_path))
                    s3_key = f"downloads/{sanitized_filename}"
                    file_url = await s3_service.upload_file(
                        file_path=file_path,
                        object_name=s3_key,
                    )

                    # Determine file type
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.srt', '.vtt', '.ass']:
                        file_type = 'subtitle'
                    elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        file_type = 'thumbnail'
                    else:
                        file_type = 'media'

                    uploaded_files.append({
                        "url": file_url,
                        "path": s3_key,
                        "type": file_type,
                        "filename": sanitized_filename
                    })

            # Find main media file URL
            main_media_url = None
            thumbnail_url = None
            subtitle_urls = []

            for file_info in uploaded_files:
                if file_info["type"] == "media":
                    main_media_url = file_info["url"]
                elif file_info["type"] == "thumbnail":
                    thumbnail_url = file_info["url"]
                elif file_info["type"] == "subtitle":
                    subtitle_urls.append(file_info["url"])

            return {
                "success": True,
                "media_url": main_media_url,
                "thumbnail_url": thumbnail_url,
                "subtitle_urls": subtitle_urls,
                "title": info.get("title", "Downloaded Media"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "upload_date": info.get("upload_date"),
                "download_method": "enhanced-yt-dlp",
                "extracted_subtitles": len(subtitle_urls) > 0,
                "extracted_thumbnail": thumbnail_url is not None,
                "total_files": len(uploaded_files)
            }

        except Exception as e:
            logger.error(f"Enhanced download failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "download_method": "enhanced-yt-dlp"
            }

        finally:
            # Clean up cookies file (only if it's a temp file, not the shared auto-extracted one)
            if cookies_is_temp and cookies_file_path and os.path.exists(cookies_file_path):
                os.remove(cookies_file_path)
                logger.info(f"Removed temporary cookies file: {cookies_file_path}")

            # Clean up downloaded files
            for file_path in downloaded_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Failed to clean up file {file_path}: {e}")

download_service = DownloadService()
