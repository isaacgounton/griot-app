"""
Dynamic face cropping utility for YouTube Shorts generation.

This module provides advanced face cropping capabilities with:
- Dynamic face-following crop with real-time tracking
- Speaker-aware cropping using speaker detection data
- Smooth face-centered framing with center-of-mass tracking
- Intelligent boundary handling to prevent crop overflow
- Audio-video synchronization for combined output
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict, Optional, Any

# MoviePy imports with compatibility
try:
    from moviepy import VideoFileClip
except ImportError:
    from moviepy.editor import VideoFileClip

import os

from .speaker_detection import speaker_detector

# Configure logging
logger = logging.getLogger(__name__)

class DynamicFaceCrop:
    """Dynamic face cropping with speaker awareness and smooth tracking."""
    
    def __init__(self):
        """Initialize dynamic face cropping."""
        self.tracking_history = []  # Store tracking history for smoothing
        self.smooth_factor = 0.3  # Smoothing factor for crop center movement
        self.max_history = 30  # Maximum frames to keep in history
        
        # Crop settings
        self.aspect_ratio = 9 / 16  # Vertical aspect ratio for shorts
        self.min_crop_size = 300  # Minimum crop size
        self.boundary_buffer = 50  # Buffer from frame edges
        
        logger.info("Dynamic face crop initialized")
    
    def calculate_crop_dimensions(self, frame_width: int, frame_height: int) -> Tuple[int, int]:
        """
        Calculate optimal crop dimensions for vertical video.
        
        Args:
            frame_width: Original frame width
            frame_height: Original frame height
            
        Returns:
            Crop dimensions (width, height)
        """
        try:
            # Calculate crop dimensions based on aspect ratio
            crop_height = frame_height
            crop_width = int(crop_height * self.aspect_ratio)
            
            # Ensure crop doesn't exceed frame width
            if crop_width > frame_width:
                crop_width = frame_width
                crop_height = int(crop_width / self.aspect_ratio)
            
            # Apply minimum size constraints
            crop_width = max(crop_width, self.min_crop_size)
            crop_height = max(crop_height, int(self.min_crop_size / self.aspect_ratio))
            
            return crop_width, crop_height
            
        except Exception as e:
            logger.error(f"Crop dimension calculation failed: {e}")
            return self.min_crop_size, int(self.min_crop_size / self.aspect_ratio)
    
    def smooth_crop_center(self, new_center: Tuple[int, int], 
                          frame_index: int) -> Tuple[int, int]:
        """
        Apply smoothing to crop center to prevent jittery movement.
        
        Args:
            new_center: New crop center coordinates
            frame_index: Current frame index
            
        Returns:
            Smoothed crop center coordinates
        """
        try:
            # Add to tracking history
            self.tracking_history.append({
                'frame': frame_index,
                'center': new_center
            })
            
            # Keep only recent history
            if len(self.tracking_history) > self.max_history:
                self.tracking_history.pop(0)
            
            # If this is the first frame, use new center directly
            if len(self.tracking_history) == 1:
                return new_center
            
            # Calculate weighted average with recent positions
            total_weight = 0
            weighted_x = 0
            weighted_y = 0
            
            for i, track in enumerate(self.tracking_history):
                # Give more weight to recent positions
                weight = (i + 1) / len(self.tracking_history)
                total_weight += weight
                weighted_x += track['center'][0] * weight
                weighted_y += track['center'][1] * weight
            
            # Apply smoothing factor
            prev_center = self.tracking_history[-2]['center']
            smooth_x = int(prev_center[0] * (1 - self.smooth_factor) + 
                          (weighted_x / total_weight) * self.smooth_factor)
            smooth_y = int(prev_center[1] * (1 - self.smooth_factor) + 
                          (weighted_y / total_weight) * self.smooth_factor)
            
            return (smooth_x, smooth_y)
            
        except Exception as e:
            logger.error(f"Crop center smoothing failed: {e}")
            return new_center
    
    def validate_crop_bounds(self, center_x: int, center_y: int,
                           crop_width: int, crop_height: int,
                           frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """
        Validate and adjust crop bounds to stay within frame boundaries.
        
        Args:
            center_x: Crop center X coordinate
            center_y: Crop center Y coordinate
            crop_width: Crop width
            crop_height: Crop height
            frame_width: Original frame width
            frame_height: Original frame height
            
        Returns:
            Validated crop bounds (x, y, width, height)
        """
        try:
            # Calculate initial crop bounds
            x1 = center_x - crop_width // 2
            y1 = center_y - crop_height // 2
            x2 = x1 + crop_width
            y2 = y1 + crop_height
            
            # Adjust horizontal bounds
            if x1 < self.boundary_buffer:
                x1 = self.boundary_buffer
                x2 = x1 + crop_width
            elif x2 > frame_width - self.boundary_buffer:
                x2 = frame_width - self.boundary_buffer
                x1 = x2 - crop_width
            
            # Adjust vertical bounds
            if y1 < self.boundary_buffer:
                y1 = self.boundary_buffer
                y2 = y1 + crop_height
            elif y2 > frame_height - self.boundary_buffer:
                y2 = frame_height - self.boundary_buffer
                y1 = y2 - crop_height
            
            # Final validation
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame_width, x2)
            y2 = min(frame_height, y2)
            
            # Recalculate dimensions
            final_width = x2 - x1
            final_height = y2 - y1
            
            return (x1, y1, final_width, final_height)
            
        except Exception as e:
            logger.error(f"Crop bounds validation failed: {e}")
            return (0, 0, min(crop_width, frame_width), min(crop_height, frame_height))
    
    def crop_frame_with_speaker_awareness(self, frame: np.ndarray, 
                                        audio_data: bytes = None,
                                        frame_index: int = 0,
                                        sample_rate: int = 16000) -> np.ndarray:
        """
        Crop frame with speaker awareness and dynamic tracking.
        
        Args:
            frame: Input video frame
            audio_data: Corresponding audio data
            frame_index: Current frame index
            sample_rate: Audio sample rate
            
        Returns:
            Cropped frame
        """
        try:
            frame_height, frame_width = frame.shape[:2]
            
            # Calculate crop dimensions
            crop_width, crop_height = self.calculate_crop_dimensions(frame_width, frame_height)
            
            # Track speakers in current frame
            speaker_info = speaker_detector.track_speakers(frame, audio_data, sample_rate)
            
            # Get optimal crop center based on active speaker
            optimal_center = speaker_detector.get_optimal_crop_center(
                speaker_info, frame_width, frame_height
            )
            
            # Apply smoothing to crop center
            smooth_center = self.smooth_crop_center(optimal_center, frame_index)
            
            # Validate crop bounds
            x, y, final_width, final_height = self.validate_crop_bounds(
                smooth_center[0], smooth_center[1], crop_width, crop_height,
                frame_width, frame_height
            )
            
            # Crop the frame
            cropped_frame = frame[y:y+final_height, x:x+final_width]
            
            # Resize to ensure consistent dimensions
            target_height = int(crop_width / self.aspect_ratio)
            if cropped_frame.shape[0] != target_height or cropped_frame.shape[1] != crop_width:
                cropped_frame = cv2.resize(cropped_frame, (crop_width, target_height))
            
            return cropped_frame
            
        except Exception as e:
            logger.error(f"Speaker-aware frame cropping failed: {e}")
            # Return center crop as fallback
            return self._center_crop_fallback(frame)
    
    def _center_crop_fallback(self, frame: np.ndarray) -> np.ndarray:
        """
        Fallback to simple center crop if advanced cropping fails.
        
        Args:
            frame: Input video frame
            
        Returns:
            Center-cropped frame
        """
        try:
            frame_height, frame_width = frame.shape[:2]
            crop_width, crop_height = self.calculate_crop_dimensions(frame_width, frame_height)
            
            # Center crop
            center_x = frame_width // 2
            center_y = frame_height // 2
            
            x1 = center_x - crop_width // 2
            y1 = center_y - crop_height // 2
            x2 = x1 + crop_width
            y2 = y1 + crop_height
            
            # Ensure bounds are within frame
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame_width, x2)
            y2 = min(frame_height, y2)
            
            return frame[y1:y2, x1:x2]
            
        except Exception as e:
            logger.error(f"Center crop fallback failed: {e}")
            return frame
    
    def process_video_with_dynamic_crop(self, video_path: str, output_path: str,
                                      audio_path: str = None) -> bool:
        """
        Process entire video with dynamic face cropping.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            audio_path: Optional audio path for VAD
            
        Returns:
            True if successful
        """
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {video_path}")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate crop dimensions for first frame
            ret, first_frame = cap.read()
            if not ret:
                raise RuntimeError("Cannot read first frame")
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
            
            frame_height, frame_width = first_frame.shape[:2]
            crop_width, crop_height = self.calculate_crop_dimensions(frame_width, frame_height)
            
            # Set up video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (crop_width, crop_height))
            
            # Load audio data if provided
            audio_data = None
            if audio_path and os.path.exists(audio_path):
                try:
                    import wave
                    with wave.open(audio_path, 'rb') as wav_file:
                        audio_data = wav_file.readframes(wav_file.getnframes())
                except:
                    logger.warning("Failed to load audio data for VAD")
            
            # Process frames
            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Get corresponding audio segment
                frame_audio = None
                if audio_data:
                    # Calculate audio segment for this frame
                    samples_per_frame = 16000 // fps  # Assuming 16kHz audio
                    start_sample = int(frame_index * samples_per_frame)
                    end_sample = int((frame_index + 1) * samples_per_frame)
                    frame_audio = audio_data[start_sample*2:end_sample*2]  # 2 bytes per sample
                
                # Crop frame with speaker awareness
                cropped_frame = self.crop_frame_with_speaker_awareness(
                    frame, frame_audio, frame_index
                )
                
                # Write frame
                out.write(cropped_frame)
                
                frame_index += 1
                
                # Progress logging
                if frame_index % 100 == 0:
                    logger.info(f"Processed {frame_index}/{total_frames} frames")
            
            # Cleanup
            cap.release()
            out.release()
            
            logger.info(f"Dynamic crop processing completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Dynamic crop processing failed: {e}")
            return False
    
    def combine_cropped_video_with_audio(self, cropped_video_path: str,
                                       original_audio_path: str,
                                       output_path: str) -> bool:
        """
        Combine cropped video with original audio.
        
        Args:
            cropped_video_path: Path to cropped video
            original_audio_path: Path to original audio
            output_path: Final output path
            
        Returns:
            True if successful
        """
        try:
            # Load video and audio clips
            video_clip = VideoFileClip(cropped_video_path)
            
            if os.path.exists(original_audio_path):
                audio_clip = VideoFileClip(original_audio_path).audio
                final_clip = video_clip.set_audio(audio_clip)
            else:
                final_clip = video_clip
            
            # Write final video
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                fps=video_clip.fps,
                preset='medium',
                bitrate='3000k'
            )
            
            # Cleanup
            video_clip.close()
            if 'audio_clip' in locals():
                audio_clip.close()
            final_clip.close()
            
            logger.info(f"Audio-video combination completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Audio-video combination failed: {e}")
            return False
    
    def reset_tracking(self):
        """Reset tracking history for new video."""
        self.tracking_history = []
        logger.info("Tracking history reset")

# Global instance
face_cropper = DynamicFaceCrop()