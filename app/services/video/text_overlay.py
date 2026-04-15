"""
Clean and robust text overlay service for videos using FFmpeg.
This service provides reliable text overlay functionality with proper positioning,
styling, and error handling.
"""

import os
import logging
import tempfile
import subprocess
import asyncio
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.utils.media import download_media_file
from app.services.s3.s3 import s3_service

logger = logging.getLogger(__name__)

@dataclass
class TextOverlayOptions:
    """Text overlay configuration options."""
    text: str
    font_size: int = 48
    font_color: str = "white"
    position: str = "bottom-center"
    y_offset: int = 50
    box_color: Optional[str] = None
    box_opacity: float = 0.8
    box_padding: int = 10
    duration: float = 5.0
    start_time: float = 0.0
    line_spacing: int = 8
    auto_wrap: bool = True
    max_chars_per_line: int = 25

class TextOverlayService:
    """Clean and reliable text overlay service."""
    
    def __init__(self):
        self.font_paths = self._get_font_paths()
        logger.info("Text overlay service initialized")
    
    def _get_font_paths(self) -> Dict[str, str]:
        """Get available font paths with fallbacks."""
        base_font_dir = os.path.join(os.path.dirname(__file__), "../../../static/fonts")
        
        # Define font fallbacks in order of preference
        font_candidates = [
            # Local fonts
            os.path.join(base_font_dir, "DejaVuSans-Bold.ttf"),
            os.path.join(base_font_dir, "DejaVuSans.ttf"),
            os.path.join(base_font_dir, "Arial.ttf"),
            # System fonts (Linux)
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            # System fonts (macOS)
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            # System fonts (Windows)
            "/Windows/Fonts/arial.ttf",
            "/Windows/Fonts/calibri.ttf"
        ]
        
        # Find first available font
        for font_path in font_candidates:
            if os.path.exists(font_path):
                logger.info(f"Using font: {font_path}")
                return {"default": font_path}
        
        # If no fonts found, log error but continue (FFmpeg will use default)
        logger.warning("No font files found, FFmpeg will use system default")
        return {"default": ""}
    
    def _escape_text_for_ffmpeg(self, text: str) -> str:
        """Properly escape text for FFmpeg drawtext filter."""
        # Handle the most problematic characters for FFmpeg
        escape_map = {
            ':': r'\:',
            "'": r"\'", 
            '"': r'\"',
            '\\': r'\\\\',
            '[': r'\[',
            ']': r'\]',
            '%': r'\%',
            '=': r'\=',
            ';': r'\;',
            ',': r'\,'
        }
        
        escaped = text
        for char, replacement in escape_map.items():
            escaped = escaped.replace(char, replacement)
        
        return escaped
    
    def _wrap_text(self, text: str, max_chars: int) -> str:
        """Wrap text to specified character width."""
        if not text or max_chars <= 0:
            return text
            
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            # Check if adding this word would exceed the limit
            if current_length + len(word) + len(current_line) > max_chars and current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\\n'.join(lines)  # Use \\n for FFmpeg
    
    def _get_position_coordinates(self, position: str, y_offset: int) -> str:
        """Get FFmpeg position coordinates."""
        positions = {
            'top-left': f'x=30:y={y_offset}',
            'top-center': f'x=(w-text_w)/2:y={y_offset}',
            'top-right': f'x=w-text_w-30:y={y_offset}',
            'center-left': 'x=30:y=(h-text_h)/2',
            'center': 'x=(w-text_w)/2:y=(h-text_h)/2',
            'center-right': 'x=w-text_w-30:y=(h-text_h)/2',
            'bottom-left': f'x=30:y=h-text_h-{y_offset}',
            'bottom-center': f'x=(w-text_w)/2:y=h-text_h-{y_offset}',
            'bottom-right': f'x=w-text_w-30:y=h-text_h-{y_offset}'
        }
        
        return positions.get(position, f'x=(w-text_w)/2:y=h-text_h-{y_offset}')
    
    def _build_drawtext_filter(self, options: TextOverlayOptions) -> str:
        """Build the FFmpeg drawtext filter string."""
        # Process and escape text
        text = options.text
        if options.auto_wrap:
            text = self._wrap_text(text, options.max_chars_per_line)
        escaped_text = self._escape_text_for_ffmpeg(text)
        
        # Get position coordinates
        position_coords = self._get_position_coordinates(options.position, options.y_offset)
        
        # Build base filter parts
        filter_parts = [
            f"text='{escaped_text}'",
            f"fontsize={options.font_size}",
            f"fontcolor={options.font_color}",
            position_coords,
            f"line_spacing={options.line_spacing}"
        ]
        
        # Add font if available
        if self.font_paths["default"]:
            filter_parts.append(f"fontfile='{self.font_paths['default']}'")
        
        # Add background box if specified
        if options.box_color:
            filter_parts.extend([
                f"box=1",
                f"boxcolor={options.box_color}@{options.box_opacity}",
                f"boxborderw={options.box_padding}"
            ])
        
        # Add timing
        if options.duration > 0:
            end_time = options.start_time + options.duration
            filter_parts.append(f"enable='between(t,{options.start_time},{end_time})'")
        
        return "drawtext=" + ":".join(filter_parts)
    
    async def create_text_overlay(self, video_url: str, options: TextOverlayOptions) -> Dict[str, Any]:
        """
        Create a video with text overlay.
        
        Args:
            video_url: URL of the input video
            options: Text overlay options
            
        Returns:
            Dictionary with result information
        """
        try:
            logger.info(f"Creating text overlay for video: {video_url}")
            
            # Download input video
            input_file = await download_media_file(video_url)
            if not input_file or not os.path.exists(input_file):
                raise Exception("Failed to download input video")
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
                output_file = temp_output.name
            
            try:
                # Build FFmpeg command
                drawtext_filter = self._build_drawtext_filter(options)
                
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-vf', drawtext_filter,
                    '-c:a', 'copy',  # Copy audio without re-encoding
                    '-c:v', 'libx264',  # Use H.264 for video
                    '-preset', 'medium',  # Balance speed and quality
                    '-crf', '23',  # Good quality
                    '-movflags', '+faststart',  # Web optimization
                    '-y',  # Overwrite output
                    output_file
                ]
                
                logger.info(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
                
                # Run FFmpeg in a thread pool to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                )
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg error: {result.stderr}")
                    raise Exception(f"FFmpeg processing failed: {result.stderr}")
                
                # Verify output file was created and has content
                if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                    raise Exception("Output video file was not created or is empty")
                
                # Upload to S3
                file_size = os.path.getsize(output_file)
                s3_key = f"text-overlay-videos/{os.path.basename(output_file)}"
                
                upload_result = await s3_service.upload_file(
                    output_file,
                    s3_key,
                    content_type="video/mp4"
                )
                
                if not upload_result.get("success"):
                    raise Exception("Failed to upload processed video to S3")
                
                s3_url = upload_result["url"]
                logger.info(f"Text overlay video uploaded to S3: {s3_url}")
                
                return {
                    "success": True,
                    "video_url": s3_url,
                    "file_size": file_size,
                    "message": "Text overlay added successfully",
                    "overlay_options": {
                        "text": options.text,
                        "position": options.position,
                        "font_size": options.font_size,
                        "font_color": options.font_color
                    }
                }
                
            finally:
                # Cleanup temporary files
                for temp_file in [input_file, output_file]:
                    try:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Text overlay creation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create text overlay"
            }
    
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get available text overlay presets."""
        return {
            "title": {
                "name": "Title",
                "description": "Large title text at the top",
                "options": {
                    "font_size": 60,
                    "font_color": "white",
                    "position": "top-center",
                    "y_offset": 80,
                    "box_color": "black",
                    "box_opacity": 0.8,
                    "box_padding": 15,
                    "duration": 5,
                    "auto_wrap": True,
                    "max_chars_per_line": 30
                }
            },
            "subtitle": {
                "name": "Subtitle",
                "description": "Subtitle text at the bottom",
                "options": {
                    "font_size": 42,
                    "font_color": "white",
                    "position": "bottom-center",
                    "y_offset": 100,
                    "box_color": "black",
                    "box_opacity": 0.8,
                    "box_padding": 12,
                    "duration": 10,
                    "auto_wrap": True,
                    "max_chars_per_line": 35
                }
            },
            "watermark": {
                "name": "Watermark",
                "description": "Small watermark text",
                "options": {
                    "font_size": 28,
                    "font_color": "white",
                    "position": "bottom-right",
                    "y_offset": 40,
                    "box_color": "black",
                    "box_opacity": 0.6,
                    "box_padding": 8,
                    "duration": 999999,
                    "auto_wrap": False,
                    "max_chars_per_line": 25
                }
            },
            "alert": {
                "name": "Alert",
                "description": "Alert/notification style",
                "options": {
                    "font_size": 56,
                    "font_color": "white",
                    "position": "center",
                    "y_offset": 0,
                    "box_color": "red",
                    "box_opacity": 0.9,
                    "box_padding": 20,
                    "duration": 4,
                    "auto_wrap": True,
                    "max_chars_per_line": 20
                }
            },
            "caption": {
                "name": "Caption",
                "description": "Clean caption with white background",
                "options": {
                    "font_size": 48,
                    "font_color": "black",
                    "position": "bottom-center",
                    "y_offset": 120,
                    "box_color": "white",
                    "box_opacity": 0.85,
                    "box_padding": 15,
                    "duration": 6,
                    "auto_wrap": True,
                    "max_chars_per_line": 25
                }
            }
        }

# Create singleton instance
text_overlay_service = TextOverlayService()