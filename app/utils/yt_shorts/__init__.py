"""
YouTube Shorts utilities package.

This package provides advanced utilities for YouTube Shorts generation including:
- Speaker detection and tracking
- Dynamic face cropping with smooth transitions
- Enhanced video editing capabilities
"""

from .speaker_detection import speaker_detector
from .face_crop import face_cropper
from .video_editor import video_editor, VideoEditor

__all__ = [
    'speaker_detector',
    'face_cropper', 
    'video_editor',
    'VideoEditor'
]