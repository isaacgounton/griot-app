import os
import subprocess
import json
import logging
import tempfile
from typing import Dict, Any
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class MediaMetadataService:
    """Service for extracting metadata from media files"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    async def get_metadata(self, media_url: str, job_id: str | None = None) -> Dict[str, Any]:
        """
        Extract metadata from a media file including video/audio properties.
        
        Args:
            media_url: URL of the media file to analyze
            job_id: Optional job identifier for logging
            
        Returns:
            Dictionary containing all available metadata for the media file
        """
        logger.info(f"Starting metadata extraction for {media_url} (job: {job_id})")
        
        # Download the file
        input_filename = await self._download_file(media_url, job_id)
        
        try:
            # Initialize metadata dictionary
            metadata = {}
            
            # Get file size
            filesize = os.path.getsize(input_filename)
            
            # Validate file size makes sense
            if filesize <= 0:
                logger.error(f"Invalid file size: {filesize} bytes for job {job_id}")
                raise Exception(f"Invalid file size: {filesize} bytes - file may be empty or corrupted")
            elif filesize < 1000:  # Less than 1KB
                logger.warning(f"Small file size: {filesize} bytes for job {job_id}")
            
            metadata['filesize'] = filesize
            metadata['filesize_mb'] = round(metadata['filesize'] / (1024 * 1024), 2)
            
            # Run ffprobe to get detailed metadata
            ffprobe_command = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                input_filename
            ]
            
            logger.info(f"Running ffprobe for job {job_id}")
            result = subprocess.run(ffprobe_command, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"ffprobe error for job {job_id}: {result.stderr}")
                raise Exception(f"ffprobe error: {result.stderr}")
                
            probe_data = json.loads(result.stdout)
            
            # Get format information
            if 'format' in probe_data:
                format_data = probe_data['format']
                
                # Get duration if available
                if 'duration' in format_data:
                    duration = float(format_data['duration'])
                    
                    # Validate duration makes sense
                    if duration <= 0:
                        logger.error(f"Invalid duration: {duration}s for job {job_id}")
                        raise Exception(f"Invalid duration: {duration}s - media file may be corrupted")
                    elif duration < 0.1:
                        logger.warning(f"Very short duration: {duration:.3f}s for job {job_id}")
                    
                    metadata['duration'] = duration
                    # Format duration as HH:MM:SS.mm
                    mins, secs = divmod(metadata['duration'], 60)
                    hours, mins = divmod(mins, 60)
                    metadata['duration_formatted'] = f"{int(hours):02d}:{int(mins):02d}:{secs:.2f}"
                
                # Get format/container type
                if 'format_name' in format_data:
                    metadata['format'] = format_data['format_name']
                    
                # Get overall bitrate if available
                if 'bit_rate' in format_data:
                    metadata['overall_bitrate'] = int(format_data['bit_rate'])
                    metadata['overall_bitrate_mbps'] = round(metadata['overall_bitrate'] / 1000000, 2)
            
            # Process streams information
            if 'streams' in probe_data:
                has_video = False
                has_audio = False
                
                for stream in probe_data['streams']:
                    stream_type = stream.get('codec_type')
                    
                    if stream_type == 'video' and not has_video:
                        has_video = True
                        
                        # Basic video properties
                        metadata['video_codec'] = stream.get('codec_name', 'unknown')
                        metadata['video_codec_long'] = stream.get('codec_long_name', 'unknown')
                        
                        # Resolution
                        if 'width' in stream and 'height' in stream:
                            metadata['width'] = stream['width']
                            metadata['height'] = stream['height']
                            metadata['resolution'] = f"{stream['width']}x{stream['height']}"
                        
                        # Frame rate
                        if 'r_frame_rate' in stream:
                            try:
                                num, den = map(int, stream['r_frame_rate'].split('/'))
                                if den != 0:
                                    metadata['fps'] = round(num / den, 2)
                            except (ValueError, ZeroDivisionError):
                                logger.warning(f"Unable to parse frame rate for job {job_id}")
                        
                        # Bitrate
                        if 'bit_rate' in stream:
                            metadata['video_bitrate'] = int(stream['bit_rate'])
                            metadata['video_bitrate_mbps'] = round(metadata['video_bitrate'] / 1000000, 2)
                        
                        # Pixel format
                        if 'pix_fmt' in stream:
                            metadata['pixel_format'] = stream['pix_fmt']
                        
                    elif stream_type == 'audio' and not has_audio:
                        has_audio = True
                        
                        # Basic audio properties
                        metadata['audio_codec'] = stream.get('codec_name', 'unknown')
                        metadata['audio_codec_long'] = stream.get('codec_long_name', 'unknown')
                        
                        # Audio channels
                        if 'channels' in stream:
                            metadata['audio_channels'] = stream['channels']
                        
                        # Sample rate
                        if 'sample_rate' in stream:
                            metadata['audio_sample_rate'] = int(stream['sample_rate'])
                            metadata['audio_sample_rate_khz'] = round(metadata['audio_sample_rate'] / 1000, 1)
                        
                        # Bitrate
                        if 'bit_rate' in stream:
                            metadata['audio_bitrate'] = int(stream['bit_rate'])
                            metadata['audio_bitrate_kbps'] = round(metadata['audio_bitrate'] / 1000, 0)
                
                # Add flags indicating presence of streams
                metadata['has_video'] = has_video
                metadata['has_audio'] = has_audio
            
            logger.info(f"Successfully extracted metadata for job {job_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed for job {job_id}: {str(e)}")
            raise
        finally:
            # Clean up the downloaded file
            if os.path.exists(input_filename):
                os.remove(input_filename)
                logger.info(f"Removed temporary file: {input_filename}")
    
    async def _download_file(self, url: str, job_id: str | None = None) -> str:
        """Download a file from URL to temporary location"""
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or "media_file"
        temp_filename = os.path.join(self.temp_dir, f"{job_id or 'metadata'}_{filename}")
        
        logger.info(f"Downloading {url} to {temp_filename}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(temp_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Download completed: {temp_filename}")
        return temp_filename

# Global service instance
metadata_service = MediaMetadataService()