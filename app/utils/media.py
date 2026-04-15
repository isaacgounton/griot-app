"""
Utilities for media file operations.
"""
import os
import json
import logging
import tempfile
import subprocess
import requests
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Tuple

from app.utils.youtube import is_youtube_url

# Configure logging
logger = logging.getLogger(__name__)

# Define supported file extensions
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.webm', '.mov', '.avi', '.mkv']
SUPPORTED_FORMATS = SUPPORTED_AUDIO_FORMATS + SUPPORTED_VIDEO_FORMATS

async def download_media_file(media_url: str, temp_dir: str = "temp") -> Tuple[str, str]:
    """
    Download media file from URL.
    
    Args:
        media_url: URL of the media file
        temp_dir: Directory to save temporary files
        
    Returns:
        Tuple of (local file path, file extension)
        
    Raises:
        RuntimeError: If download fails
    """
    from app.services.s3.s3 import s3_service
    # Parse URL to get hostname and path
    parsed_url = urlparse(media_url)
    hostname = parsed_url.netloc
    path = parsed_url.path
    
    # Get file extension
    _, file_extension = os.path.splitext(path)
    file_extension = file_extension.lower()
    
    # If no extension or not recognized, use defaults
    if not file_extension:
        file_extension = ".mp4"  # Default to mp4 if no extension
    
    # Create temporary file
    os.makedirs(temp_dir, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False, dir=temp_dir)
    temp_file.close()
    local_file_path = temp_file.name
    
    logger.info(f"Downloading media from {media_url} to {local_file_path}")
    
    # Check if URL is from our S3-compatible storage
    bucket_name = os.environ.get("S3_BUCKET_NAME", "")
    s3_endpoint = os.environ.get("S3_ENDPOINT_URL", "")
    
    # Check if URL is from our S3 storage (could be AWS S3, DigitalOcean, etc.)
    is_from_our_s3 = False
    if bucket_name or s3_endpoint:
        # Check if hostname matches our bucket name or S3 endpoint
        is_from_our_s3 = (
            (bucket_name and bucket_name in hostname) or 
            (s3_endpoint and urlparse(s3_endpoint).netloc in hostname) or
            # Also check for MinIO-style URLs that might have the bucket name in the subdomain
            'minio' in hostname.lower()
        )
    
    try:
        if is_from_our_s3:
            # Extract object key from path
            object_path = path.lstrip('/')
            
            # For DigitalOcean Spaces URLs, extract bucket from hostname and use full path as object key
            # URL format: https://bucketname.nyc3.digitaloceanspaces.com/folder/file.ext
            if 'digitaloceanspaces.com' in hostname:
                # Extract bucket from hostname (first part before first dot)
                url_bucket_name = hostname.split('.')[0]
                object_key = object_path  # Use full path as object key (preserves folder structure)
                logger.info(f"Detected DigitalOcean Spaces URL: bucket={url_bucket_name}, object={object_key}")
            else:
                # For other S3-compatible services, split path to get bucket and object
                path_parts = object_path.split('/', 1)
                if len(path_parts) == 2:
                    url_bucket_name, object_key = path_parts
                    logger.info(f"Detected S3 URL with bucket in path: bucket={url_bucket_name}, object={object_key}")
                else:
                    # Fallback: use default bucket and full path as object key
                    url_bucket_name = None
                    object_key = object_path
                    logger.info(f"Using default bucket with object key: {object_key}")
                
            try:
                # Use the bucket name from the URL, not from environment variable
                local_file_path = await s3_service.download_file(object_key, local_file_path, bucket_name=url_bucket_name)
            except Exception as s3_error:
                if "403" in str(s3_error) or "Forbidden" in str(s3_error) or "404" in str(s3_error) or "Not Found" in str(s3_error):
                    logger.warning(f"S3 download failed with {s3_error}, trying HTTP download as fallback")
                    # Fallback to HTTP download if we get permission denied or file not found
                    # Check if this is a MinIO server and disable SSL verification if needed
                    verify_ssl = True
                    if 'minio' in hostname.lower():
                        verify_ssl = False
                        logger.info(f"Detected MinIO server, disabling SSL verification for {media_url}")

                    response = requests.get(media_url, timeout=30, verify=verify_ssl)
                    response.raise_for_status()

                    with open(local_file_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Successfully downloaded media via HTTP fallback: {local_file_path}")
                else:
                    raise

            logger.info(f"Successfully downloaded media from S3: {local_file_path}")
        elif is_youtube_url(media_url):
            # Use yt-dlp for YouTube URLs
            logger.info(f"Detected YouTube URL, using yt-dlp: {media_url}")
            download_with_ytdlp(media_url, local_file_path)
        else:
            # Use direct HTTP download for external URLs (like Cloudinary)
            logger.info(f"Detected external URL, using direct HTTP download: {media_url}")
            
            # Check if this is a MinIO server and disable SSL verification if needed
            verify_ssl = True
            if 'minio' in hostname.lower():
                verify_ssl = False
                logger.info(f"Detected MinIO server, disabling SSL verification for {media_url}")
            
            response = requests.get(media_url, timeout=30, verify=verify_ssl)
            response.raise_for_status()
            
            with open(local_file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded media via HTTP: {local_file_path}")
            
        logger.info(f"Media downloaded successfully to {local_file_path}")
        return local_file_path, file_extension
    except Exception as e:
        # Clean up temporary file if download failed
        if os.path.exists(local_file_path):
            os.unlink(local_file_path)
        logger.error(f"Failed to download media from {media_url}: {e}")
        raise RuntimeError(f"Failed to download media: {e}")

def download_with_ytdlp(url: str, output_path: str):
    """
    Download media using yt-dlp.
    
    Args:
        url: URL to download from
        output_path: Path to save the downloaded file
        
    Raises:
        RuntimeError: If download fails
    """
    try:
        # For videos, use best video with audio
        format_option = "bestaudio/best"
        if output_path.lower().endswith(tuple(SUPPORTED_VIDEO_FORMATS)):
            format_option = "bestvideo+bestaudio/best"
            
        # Run yt-dlp with appropriate options
        cmd = [
            "yt-dlp",
            "-o", output_path,
            "--no-playlist",
            "--quiet",
            "--format", format_option,
            url
        ]
        
        logger.info(f"Running yt-dlp command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Download successful, file size: {file_size} bytes")
        else:
            logger.error("Download failed: Output file does not exist")
            raise RuntimeError("Download completed but file doesn't exist")
    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp failed: {e.stderr.decode() if e.stderr else str(e)}")
        raise RuntimeError(f"yt-dlp failed: {e.stderr.decode() if e.stderr else str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise 

async def download_subtitle_file(subtitle_url: str, temp_dir: str = "temp") -> str:
    """
    Download a subtitle file from a URL.
    
    Args:
        subtitle_url: URL of the subtitle file to download
        temp_dir: Directory to save temporary files
        
    Returns:
        Local path to the downloaded subtitle file
        
    Raises:
        RuntimeError: If download fails or format is unsupported
    """
    from app.services.s3.s3 import s3_service
    # Parse URL to get hostname and path
    parsed_url = urlparse(subtitle_url)
    hostname = parsed_url.netloc
    path = parsed_url.path
    file_extension = os.path.splitext(path)[1].lower()
    
    # Validate subtitle format
    if file_extension not in [".srt", ".ass", ".vtt"]:
        raise RuntimeError(f"Unsupported subtitle format: {file_extension}")
    
    # Create temporary file
    os.makedirs(temp_dir, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, 
        suffix=file_extension,
        dir=temp_dir
    )
    temp_file_path = temp_file.name
    temp_file.close()
    
    logger.info(f"Downloading subtitle file from URL: {subtitle_url}")
    
    # Check if URL is from our S3-compatible storage
    bucket_name = os.environ.get("S3_BUCKET_NAME", "")
    s3_endpoint = os.environ.get("S3_ENDPOINT_URL", "")
    
    # Check if URL is from our S3 storage
    is_from_our_s3 = False
    if bucket_name or s3_endpoint:
        is_from_our_s3 = (
            (bucket_name and bucket_name in hostname) or 
            (s3_endpoint and urlparse(s3_endpoint).netloc in hostname) or
            # Also check for MinIO-style URLs that might have the bucket name in the subdomain
            'minio' in hostname.lower()
        )
    
    try:
        if is_from_our_s3:
            # Extract object key from path - this is the full path including folder prefixes
            object_key = path.lstrip('/')
            logger.info(f"Detected S3 URL, downloading subtitle: {object_key}")
            
            # Use environment bucket name and full path as object key (including folder prefixes like transcriptions/)
            temp_file_path = await s3_service.download_file(object_key, temp_file_path)
            logger.info(f"Successfully downloaded subtitle from S3: {temp_file_path}")
        else:
            # Use regular HTTP download for non-S3 URLs
            import requests
            response = requests.get(subtitle_url, timeout=30)
            response.raise_for_status()
            
            with open(temp_file_path, 'wb') as f:
                f.write(response.content)
        
        logger.info(f"Subtitle file downloaded successfully to {temp_file_path}")
        return temp_file_path
    except Exception as e:
        # Clean up temporary file if download failed
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        logger.error(f"Failed to download subtitle file from {subtitle_url}: {e}")
        raise RuntimeError(f"Failed to download subtitle file: {str(e)}")


async def get_media_info(file_path: str) -> Dict[str, Any]:
    """
    Get media information using FFprobe.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Dictionary containing media information
        
    Raises:
        RuntimeError: If FFprobe fails or file doesn't exist
    """
    if not os.path.exists(file_path):
        raise RuntimeError(f"File does not exist: {file_path}")
    
    try:
        # Use FFprobe to get media information
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        
        logger.info(f"Getting media info for: {file_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        media_info = json.loads(result.stdout)
        
        # Extract useful information
        info = {}
        
        # Format information
        if "format" in media_info:
            format_info = media_info["format"]
            info.update({
                "duration": float(format_info.get("duration", 0)),
                "bit_rate": int(format_info.get("bit_rate", 0)),
                "size": int(format_info.get("size", 0)),
                "format_name": format_info.get("format_name", ""),
                "format_long_name": format_info.get("format_long_name", "")
            })
        
        # Stream information
        if "streams" in media_info:
            streams = media_info["streams"]
            video_streams = [s for s in streams if s.get("codec_type") == "video"]
            audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
            
            if video_streams:
                video_stream = video_streams[0]  # Use first video stream
                info.update({
                    "width": int(video_stream.get("width", 0)),
                    "height": int(video_stream.get("height", 0)),
                    "codec_name": video_stream.get("codec_name", ""),
                    "codec_long_name": video_stream.get("codec_long_name", ""),
                    "frame_rate": video_stream.get("r_frame_rate", ""),
                    "pixel_format": video_stream.get("pix_fmt", "")
                })
            
            if audio_streams:
                audio_stream = audio_streams[0]  # Use first audio stream
                info.update({
                    "audio_codec": audio_stream.get("codec_name", ""),
                    "audio_codec_long_name": audio_stream.get("codec_long_name", ""),
                    "sample_rate": int(audio_stream.get("sample_rate", 0)),
                    "channels": int(audio_stream.get("channels", 0)),
                    "channel_layout": audio_stream.get("channel_layout", "")
                })
        
        logger.info(f"Successfully extracted media info: duration={info.get('duration', 0)}s")
        return info

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFprobe failed for {file_path}: {error_msg}")
        raise RuntimeError(f"Failed to get media info: {error_msg}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse FFprobe output: {e}")
        raise RuntimeError(f"Failed to parse media info: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting media info: {e}")
        raise RuntimeError(f"Unexpected error getting media info: {e}")


class MediaUtils:
    """
    Enhanced media utilities based on AI agents MediaUtils.

    Provides comprehensive FFmpeg operations for video and audio processing.
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize MediaUtils.

        Args:
            ffmpeg_path: Path to ffmpeg executable
        """
        self.ffmpeg_path = ffmpeg_path

    async def merge_videos(
        self,
        video_paths: List[str],
        output_path: str,
        background_music_path: Optional[str] = None,
        background_music_volume: float = 0.5,
    ) -> bool:
        """
        Merge multiple video files into one, optionally with background music.

        Args:
            video_paths: List of paths to video files to merge
            output_path: Path for the merged output video
            background_music: Optional path to background music file
            bg_music_volume: Volume level for background music (0.0 to 1.0, default 0.5)

        Returns:
            bool: True if successful, False otherwise
        """
        import time
        from loguru import logger

        if not video_paths:
            logger.error("no video paths provided for merging")
            return False

        start = time.time()
        context_logger = logger.bind(
            number_of_videos=len(video_paths),
            output_path=output_path,
            background_music=bool(background_music_path),
            background_music_volume=background_music_volume,
        )

        try:
            # Get dimensions from the first video
            first_video_info = await get_media_info(video_paths[0])
            if not first_video_info:
                context_logger.error("failed to get video info from first video")
                return False

            target_width = first_video_info.get("width", 1080)
            target_height = first_video_info.get("height", 1920)
            target_dimensions = f"{target_width}:{target_height}"

            context_logger.bind(
                target_width=target_width, target_height=target_height
            ).debug("using dimensions from first video")

            # Base command
            cmd = [self.ffmpeg_path, "-y"]

            # Add input video files
            for video_path in video_paths:
                cmd.extend(["-i", video_path])

            # Add background music if provided
            music_input_index = None
            if background_music_path:
                cmd.extend(["-stream_loop", "-1", "-i", background_music_path])
                music_input_index = len(video_paths)

            # Create filter complex for concatenating videos with re-encoding
            if len(video_paths) == 1:
                # Single video - re-encode to ensure consistency
                # Check if the video has audio
                audio_info = await get_media_info(video_paths[0])
                has_audio = bool(audio_info.get('duration', 0) > 0)

                if background_music_path:
                    if has_audio:
                        cmd.extend([
                            "-filter_complex",
                            f"[0:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30[v];[{music_input_index}:a]volume={background_music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
                            "-map", "[v]", "-map", "[a]",
                        ])
                    else:
                        # No audio in video, just use background music
                        cmd.extend([
                            "-filter_complex",
                            f"[0:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30[v];[{music_input_index}:a]volume={background_music_volume}[a]",
                            "-map", "[v]", "-map", "[a]",
                        ])
                else:
                    if has_audio:
                        cmd.extend([
                            "-filter_complex",
                            f"[0:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30[v]",
                            "-map", "[v]", "-map", "0:a",
                        ])
                    else:
                        # No audio in video and no background music, create silent audio
                        video_info = await get_media_info(video_paths[0])
                        video_duration = video_info.get('duration', 10)  # fallback to 10 seconds
                        cmd.extend([
                            "-filter_complex",
                            f"[0:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30[v];anullsrc=channel_layout=stereo:sample_rate=48000:duration={video_duration}[a]",
                            "-map", "[v]", "-map", "[a]",
                        ])
            else:
                # Multiple videos - normalize and concatenate with re-encoding
                # First, check which videos have audio streams
                videos_with_audio = []
                for i, video_path in enumerate(video_paths):
                    video_info = await get_media_info(video_path)
                    # Check if video has audio by trying to get audio info
                    audio_info = await get_media_info(video_path)
                    has_audio = bool(audio_info.get('duration', 0) > 0)
                    videos_with_audio.append(has_audio)
                    context_logger.bind(video_index=i, has_audio=has_audio).debug("checked audio stream")

                # Create normalized video streams for each input
                normalize_filters = []
                for i in range(len(video_paths)):
                    normalize_filters.append(
                        f"[{i}:v]scale={target_dimensions}:force_original_aspect_ratio=decrease,pad={target_dimensions}:(ow-iw)/2:(oh-ih)/2:black,fps=30,format=yuv420p[v{i}n]"
                    )

                # Create audio streams for videos without audio (silent audio)
                audio_filters = []
                for i in range(len(video_paths)):
                    if not videos_with_audio[i]:
                        # Get video duration for silent audio generation
                        video_info = await get_media_info(video_paths[i])
                        video_duration = video_info.get('duration', 10)  # fallback to 10 seconds
                        audio_filters.append(f"anullsrc=channel_layout=stereo:sample_rate=48000:duration={video_duration}[a{i}n]")
                    else:
                        audio_filters.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}n]")

                # Create the concat filter using normalized streams
                concat_inputs = ""
                for i in range(len(video_paths)):
                    concat_inputs += f"[v{i}n][a{i}n]"

                # Combine all filters
                all_filters = normalize_filters + audio_filters
                filter_complex = (
                    ";".join(all_filters)
                    + f";{concat_inputs}concat=n={len(video_paths)}:v=1:a=1[v][a]"
                )

                if background_music_path:
                    # Mix the concatenated audio with background music
                    filter_complex += f";[{music_input_index}:a]volume={background_music_volume}[bg];[a][bg]amix=inputs=2:duration=first[final_a]"
                    cmd.extend([
                        "-filter_complex", filter_complex,
                        "-map", "[v]", "-map", "[final_a]",
                    ])
                else:
                    cmd.extend([
                        "-filter_complex", filter_complex,
                        "-map", "[v]", "-map", "[a]",
                    ])

            # Video codec settings
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
            ])

            # Audio codec settings
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])

            # Other settings
            cmd.extend(["-pix_fmt", "yuv420p", output_path])

            # Calculate expected duration for progress tracking
            expected_duration = 0
            for video_path in video_paths:
                video_info = await get_media_info(video_path)
                expected_duration += video_info.get("duration", 0)

            success = await self.execute_ffmpeg_command(
                cmd,
                "merge videos",
                expected_duration=expected_duration,
                show_progress=True,
            )

            if success:
                context_logger.bind(execution_time=time.time() - start).debug(
                    "videos merged successfully",
                )
                return True
            else:
                context_logger.error("ffmpeg failed to merge videos")
                return False

        except Exception as e:
            context_logger.bind(error=str(e)).error(
                "error merging videos",
            )
            return False

    async def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get video information such as duration, width, height, codec, fps, etc.

        Args:
            file_path: Path to the video file

        Returns:
            Dictionary containing video information
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                "-select_streams", "v:0",  # Select first video stream
                file_path,
            ]

            success, stdout, stderr = await self.execute_ffprobe_command(
                cmd, "get video info"
            )

            if not success:
                raise Exception(f"ffprobe failed: {stderr}")

            probe_data = json.loads(stdout)

            # Extract format information
            format_info = probe_data.get("format", {})
            streams = probe_data.get("streams", [])

            if not streams:
                raise Exception("No video stream found in file")

            video_stream = streams[0]

            video_info = {
                "duration": float(format_info.get("duration", 0)),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "fps": video_stream.get("avg_frame_rate", "0/1").split("/")[0],
                "aspect_ratio": video_stream.get("display_aspect_ratio", "1:1"),
                "codec": video_stream.get("codec_name"),
            }

            return video_info

        except Exception as e:
            logger.bind(file_path=file_path, error=str(e)).error(
                "error getting video info"
            )
            return {}

    async def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get audio information such as duration, codec, bitrate, sample rate, channels, etc.

        Args:
            file_path: Path to the audio file

        Returns:
            Dictionary containing audio information
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                "-select_streams", "a:0",  # Select first audio stream
                file_path,
            ]

            success, stdout, stderr = await self.execute_ffprobe_command(
                cmd, "get audio info"
            )

            if not success:
                raise Exception(f"ffprobe failed: {stderr}")

            probe_data = json.loads(stdout)

            # Extract format information
            format_info = probe_data.get("format", {})
            streams = probe_data.get("streams", [])

            if not streams:
                raise Exception("No audio stream found in file")

            audio_stream = streams[0]

            audio_info = {
                "duration": float(format_info.get("duration", 0)),
                "channels": audio_stream.get("channels", 0),
                "sample_rate": audio_stream.get("sample_rate", "0"),
                "codec": audio_stream.get("codec_name", ""),
                "bitrate": audio_stream.get("bit_rate", "0"),
            }

            return audio_info

        except Exception as e:
            logger.bind(file_path=file_path, error=str(e)).error(
                "Error getting audio info"
            )
            return {}

    async def extract_frame(
        self,
        video_path: str,
        output_path: str,
        time_seconds: float = 0.0,
    ) -> bool:
        """
        Extract a frame from a video at a specified time.

        Args:
            video_path: Path to the input video file
            output_path: Path for the extracted frame image
            time_seconds: Time in seconds to extract the frame (default: 0.0)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Base command
            cmd = [self.ffmpeg_path, "-y"]

            # Add input video file
            cmd.extend(["-i", video_path])

            # Seek to the specified time and extract one frame
            cmd.extend([
                "-ss", str(time_seconds),  # Seek to time
                "-vframes", "1",  # Extract only one frame
                "-q:v", "2",  # High quality (scale 1-31, lower is better)
                output_path,
            ])

            # Execute the command
            success = await self.execute_ffmpeg_command(
                cmd,
                "extract frame",
                show_progress=False,  # No progress tracking for single frame extraction
            )

            if success:
                logger.bind(video_path=video_path, time_seconds=time_seconds).debug(
                    "frame extracted successfully"
                )
                return True
            else:
                logger.bind(video_path=video_path, time_seconds=time_seconds).error(
                    "failed to extract frame from video"
                )
                return False

        except Exception as e:
            logger.bind(error=str(e)).error("Error extracting frame from video")
            return False

    async def extract_frames(
        self,
        video_path: str,
        output_template: str,
        amount: int = 5,
        length_seconds: float = None,
    ) -> bool:
        """
        Extract multiple frames from a video at evenly spaced intervals.

        Args:
            video_path: Path to the input video file
            output_template: Template for output image files (e.g., "frame-%03d.jpg")
            amount: Number of frames to extract (default: 5)
            length_seconds: Length of the video in seconds (optional, if not provided will be calculated)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get video duration if not provided
            if length_seconds is None:
                video_info = await self.get_video_info(video_path)
                length_seconds = video_info.get("duration", 0)

            if length_seconds <= 0:
                logger.error("invalid video duration for frame extraction")
                return False

            # Calculate frame interval (time between frames)
            # This gives us the correct fps rate to extract exactly 'amount' frames
            # evenly distributed across the video duration
            frame_interval = length_seconds / amount

            # Base command - using the corrected fps calculation
            # fps=1/frame_interval extracts one frame every frame_interval seconds
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", video_path,
                "-vf", f"fps=1/{frame_interval}",
                "-vframes", str(amount),
                "-qscale:v", "2",  # High quality
                output_template,
            ]

            # Execute the command
            success = await self.execute_ffmpeg_command(
                cmd,
                "extract frames",
                expected_duration=length_seconds,
                show_progress=True,
            )

            if success:
                logger.bind(video_path=video_path, amount=amount).debug(
                    "frames extracted successfully"
                )
                return True
            else:
                logger.bind(video_path=video_path, amount=amount).error(
                    "failed to extract frames from video"
                )
                return False

        except Exception as e:
            logger.bind(error=str(e)).error("Error extracting frames from video")
            return False

    def format_time(self, seconds: float) -> str:
        """
        Format seconds into HH:MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    async def execute_ffmpeg_command(
        self,
        cmd: list,
        operation_name: str,
        expected_duration: float = None,
        show_progress: bool = True,
    ) -> bool:
        """
        Execute an FFmpeg command with proper logging and progress tracking.

        Args:
            cmd: The ffmpeg command as a list
            operation_name: Name of the operation for logging
            expected_duration: Expected duration for progress calculation
            show_progress: Whether to show progress information

        Returns:
            bool: True if successful, False otherwise
        """
        import asyncio

        try:
            logger.bind(command=" ".join(cmd), operation=operation_name).debug(
                f"executing ffmpeg command for {operation_name}"
            )

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Process the output line by line as it becomes available
            if show_progress and expected_duration:
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break

                    line_str = line.decode().strip()
                    # Extract time information for progress tracking
                    if "time=" in line_str and "speed=" in line_str:
                        try:
                            # Extract the time information
                            time_str = line_str.split("time=")[1].split(" ")[0]
                            # Convert HH:MM:SS.MS format to seconds
                            h, m, s = time_str.split(":")
                            seconds = float(h) * 3600 + float(m) * 60 + float(s)

                            # Calculate progress percentage
                            progress = min(100, (seconds / expected_duration) * 100)
                            logger.info(
                                f"{operation_name}: {progress:.2f}% complete (Time: {time_str} / Total: {self.format_time(expected_duration)})"
                            )
                        except (ValueError, IndexError):
                            # If parsing fails, continue silently
                            pass

            # Wait for the process to complete and check the return code
            return_code = await process.wait()
            if return_code != 0:
                logger.bind(return_code=return_code, operation=operation_name).error(
                    f"ffmpeg exited with code: {return_code} for {operation_name}"
                )
                return False

            logger.bind(operation=operation_name).debug(
                f"{operation_name} completed successfully"
            )
            return True

        except Exception as e:
            logger.bind(error=str(e), operation=operation_name).error(
                f"error executing ffmpeg command for {operation_name}"
            )
            return False

    async def execute_ffprobe_command(
        self, cmd: list, operation_name: str
    ) -> tuple[bool, str, str]:
        """
        Execute an ffprobe command with proper logging.

        Args:
            cmd: The ffprobe command as a list
            operation_name: Name of the operation for logging

        Returns:
            tuple: (success, stdout, stderr)
        """
        import asyncio

        try:
            logger.bind(command=" ".join(cmd), operation=operation_name).debug(
                f"executing ffprobe command for {operation_name}"
            )

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.bind(stderr=stderr, operation=operation_name).error(
                    f"ffprobe failed for {operation_name}"
                )
                return False, stdout.decode(), stderr.decode()

            logger.bind(operation=operation_name).debug(
                f"{operation_name} completed successfully"
            )
            return True, stdout.decode(), stderr.decode()

        except Exception as e:
            logger.bind(error=str(e), operation=operation_name).error(
                f"error executing ffprobe command for {operation_name}"
            )
            return False, "", str(e)

    @staticmethod
    def is_hex_color(color: str) -> bool:
        """
        Check if the given color string is a valid hex color.

        Args:
            color: Color string to check

        Returns:
            bool: True if it's a hex color, False otherwise
        """
        return all(
            c in "0123456789abcdefABCDEF" for c in color[1:]
        )

    async def colorkey_overlay(
        self,
        input_video_path: str,
        overlay_video_path: str,
        output_video_path: str,
        color: str = "green",
        similarity: float = 0.1,
        blend: float = 0.1,
    ):
        """
        Apply a colorkey overlay to a video using FFmpeg.
        """
        import time

        start = time.time()
        info = await self.get_video_info(input_video_path)
        video_duration = info.get("duration", 0)

        if not video_duration:
            logger.error("failed to get video duration from input video")
            return False

        color = color.lstrip("#")
        if self.is_hex_color(color):
            color = f"0x{color.upper()}"

        context_logger = logger.bind(
            input_video_path=input_video_path,
            overlay_video_path=overlay_video_path,
            output_video_path=output_video_path,
            video_duration=video_duration,
            color=color,
            similarity=similarity,
            blend=blend,
        )
        context_logger.debug("Starting colorkey overlay process")

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", input_video_path,
            "-stream_loop", "-1",
            "-i", overlay_video_path,
            "-filter_complex", f"[1:v]colorkey={color}:{similarity}:{blend}[ckout];[0:v][ckout]overlay=eof_action=repeat[v]",
            "-map", "[v]",
            "-map", "0:a",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "18",
            "-c:a", "copy",
            "-t", f"{video_duration}s",
            output_video_path,
        ]

        try:
            success = await self.execute_ffmpeg_command(
                cmd,
                "add colorkey overlay to video",
                expected_duration=video_duration,
                show_progress=True,
            )

            if success:
                context_logger.bind(execution_time=time.time() - start).debug(
                    "colorkey overlay added successfully",
                )
                return True
            else:
                context_logger.error("ffmpeg failed to create colorkey overlay")
                return False

        except Exception as e:
            context_logger.bind(error=str(e)).error(
                "error adding colorkey overlay to video",
            )
            return False

    async def convert_pcm_to_wav(
        self,
        input_pcm_path: str,
        output_wav_path: str,
        sample_rate: int = 24000,
        channels: int = 1,
        target_sample_rate: int = 44100,
    ) -> bool:
        """
        Convert PCM audio to WAV format.
        """
        import time

        start = time.time()
        context_logger = logger.bind(
            input_pcm_path=input_pcm_path,
            output_wav_path=output_wav_path,
            sample_rate=sample_rate,
            channels=channels,
            target_sample_rate=target_sample_rate,
        )
        context_logger.debug("Starting PCM to WAV conversion")

        cmd = [
            self.ffmpeg_path, "-y",
            "-f", "s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-i", input_pcm_path,
            "-ar", str(target_sample_rate),
            "-ac", "2",  # Convert to stereo
            output_wav_path,
        ]

        try:
            success = await self.execute_ffmpeg_command(
                cmd,
                "convert PCM to WAV",
                show_progress=False,
            )

            if success:
                context_logger.bind(execution_time=time.time() - start).debug(
                    "PCM to WAV conversion successful",
                )
                return True
            else:
                context_logger.error("ffmpeg failed to convert PCM to WAV")
                return False

        except Exception as e:
            context_logger.bind(error=str(e)).error(
                "error converting PCM to WAV",
            )
            return False


# Create media utils instance
media_utils = MediaUtils() 