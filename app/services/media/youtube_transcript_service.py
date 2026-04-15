"""
Service for generating YouTube transcripts.
"""
import logging
from typing import List, Optional, Dict, Any
import json
from app.services.job_queue import job_queue
from app.models import JobType
from app.services.s3.s3 import s3_service
import os
import uuid

# Configure logging first
logger = logging.getLogger(__name__)

# Optional dependency - YouTube transcript functionality
try:
    from youtube_transcript_api._api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
    from youtube_transcript_api.formatters import JSONFormatter
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    logger.warning("youtube_transcript_api not available. YouTube transcript features will be disabled.")
    YouTubeTranscriptApi = None  # type: ignore
    NoTranscriptFound = None  # type: ignore
    TranscriptsDisabled = None  # type: ignore
    VideoUnavailable = None  # type: ignore
    JSONFormatter = None  # type: ignore
    YOUTUBE_TRANSCRIPT_AVAILABLE = False

class YouTubeTranscriptService:
    """
    Service for generating YouTube transcripts.
    """

    async def generate_transcript(
        self,
        job_id: str,
        video_url: str,
        languages: Optional[List[str]],
        translate_to: Optional[str],
        format: Optional[str],
    ) -> dict:
        """
        Generate a transcript for a YouTube video.
        """
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            raise RuntimeError("YouTube transcript functionality is not available. Please install youtube_transcript_api.")
            
        try:
            video_id = self._extract_video_id(video_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL provided.")

            params = {
                "video_id": video_id,
                "languages": languages,
                "translate_to": translate_to,
                "format": format,
            }

            # Create wrapper function to match job queue signature
            async def process_wrapper(_job_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
                return await self.process_transcript_generation(data)
            
            await job_queue.add_job(
                job_id=job_id,
                job_type=JobType.YOUTUBE_TRANSCRIPT,
                process_func=process_wrapper,
                data=params,
            )

            return {"job_id": job_id}
        except Exception as e:
            logger.error(f"Error creating YouTube transcript job: {e}")
            raise

    async def process_transcript_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the YouTube transcript generation.
        """
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            raise RuntimeError("YouTube transcript functionality is not available. Please install youtube_transcript_api.")

        # Extract video_id from video_url if not directly provided
        if "video_id" in params:
            video_id = params["video_id"]
        elif "video_url" in params:
            video_id = self._extract_video_id(params["video_url"])
            if not video_id:
                raise ValueError(f"Could not extract video ID from URL: {params['video_url']}. Supported formats: https://www.youtube.com/watch?v=VIDEO_ID, https://youtu.be/VIDEO_ID, https://www.youtube.com/embed/VIDEO_ID, https://www.youtube.com/v/VIDEO_ID, https://www.youtube.com/shorts/VIDEO_ID, https://www.youtube.com/live/VIDEO_ID")
        else:
            raise ValueError("Either video_id or video_url must be provided")

        languages = params.get("languages", ["en"])
        translate_to = params.get("translate_to")
        output_format = params.get("format", "json")

        try:
            if YouTubeTranscriptApi is None:
                raise RuntimeError("YouTubeTranscriptApi is not available")

            # Try to get cookies for authenticated YouTube access
            cookies_path = None
            try:
                from app.utils.youtube_cookies import get_cookies_sync
                auto_path = get_cookies_sync()
                if auto_path and os.path.exists(auto_path):
                    cookies_path = auto_path
                    logger.info(f"Using auto-extracted cookies for transcript: {auto_path}")
            except Exception as e:
                logger.debug(f"Auto cookie extraction not available for transcripts: {e}")

            transcript_list = YouTubeTranscriptApi.list_transcripts(
                video_id, cookies=cookies_path
            )
            transcript = transcript_list.find_transcript(languages)

            if translate_to:
                if not transcript.is_translatable:
                    raise ValueError("Selected transcript cannot be translated.")
                transcript = transcript.translate(translate_to)

            fetched_transcript = transcript.fetch()

            # Format the transcript
            if output_format == "json":
                if JSONFormatter is None:
                    # Fallback to basic JSON formatting
                    formatted_transcript = json.dumps(fetched_transcript, indent=2, ensure_ascii=False)
                else:
                    formatter = JSONFormatter()
                    formatted_transcript = formatter.format_transcript(fetched_transcript)
            else:
                # Default to JSON if format is not supported or specified
                if JSONFormatter is None:
                    formatted_transcript = json.dumps(fetched_transcript, indent=2, ensure_ascii=False)
                else:
                    formatter = JSONFormatter()
                    formatted_transcript = formatter.format_transcript(fetched_transcript)
                logger.warning(f"Unsupported format '{output_format}'. Defaulting to JSON.")

            # Save to a temporary file
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            transcript_filename = f"transcript_{uuid.uuid4()}.json"
            transcript_path = os.path.join(temp_dir, transcript_filename)

            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(formatted_transcript)

            # Upload to S3
            s3_key = f"transcripts/{transcript_filename}"
            transcript_url = await s3_service.upload_file(transcript_path, s3_key)

            # Clean up temporary file
            os.remove(transcript_path)

            return {"transcript_url": transcript_url, "transcript": formatted_transcript}

        except Exception as ex:
            # Handle YouTube API specific exceptions if available
            if NoTranscriptFound and isinstance(ex, NoTranscriptFound):
                raise ValueError(f"No transcript found for video ID: {video_id} in languages: {languages}")
            elif TranscriptsDisabled and isinstance(ex, TranscriptsDisabled):
                raise ValueError(f"Transcripts are disabled for video ID: {video_id}")
            elif VideoUnavailable and isinstance(ex, VideoUnavailable):
                raise ValueError(f"Video with ID: {video_id} is unavailable.")
            else:
                # Log and re-raise the original exception if it's not a recognized YouTube API exception
                logger.error(f"Error processing YouTube transcript: {ex}")
                raise

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various forms of YouTube URLs.
        Supports additional formats like youtu.be short links, embed URLs, and more.
        """
        from urllib.parse import urlparse, parse_qs, unquote

        if not url or not isinstance(url, str):
            return None

        # Clean the URL
        url = url.strip()

        # Handle youtu.be short links
        if url.startswith('youtu.be/'):
            video_id = url.split('youtu.be/')[1].split('?')[0].split('&')[0]
            return video_id if len(video_id) == 11 else None

        # Handle full youtu.be URLs
        if 'youtu.be' in url:
            parsed_url = urlparse(url)
            if parsed_url.hostname == 'youtu.be':
                video_id = parsed_url.path[1:].split('?')[0].split('&')[0]
                return video_id if len(video_id) == 11 else None

        # Handle youtube.com URLs
        if 'youtube.com' in url:
            parsed_url = urlparse(url)

            if parsed_url.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
                path = parsed_url.path

                # Standard watch URL
                if path == '/watch':
                    return parse_qs(parsed_url.query).get('v', [None])[0]

                # Embed URL
                elif path.startswith('/embed/'):
                    video_id = path.split('/')[2]
                    return video_id if len(video_id) == 11 else None

                # Short URL format
                elif path.startswith('/v/'):
                    video_id = path.split('/')[2]
                    return video_id if len(video_id) == 11 else None

                # Live stream URL
                elif path.startswith('/live/'):
                    video_id = path.split('/')[2]
                    return video_id if len(video_id) == 11 else None

                # YouTube shorts
                elif path.startswith('/shorts/'):
                    video_id = path.split('/')[2]
                    return video_id if len(video_id) == 11 else None

        # Handle direct video IDs (11 characters)
        if len(url) == 11 and url.replace('_', '').replace('-', '').isalnum():
            return url

        # Handle URLs with video ID as query parameter in other domains
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params and query_params['v'][0]:
                video_id = query_params['v'][0]
                if len(video_id) == 11:
                    return video_id
        except:
            pass

        return None

youtube_transcript_service = YouTubeTranscriptService()
