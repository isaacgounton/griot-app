"""
Advanced speaker detection utility for YouTube Shorts generation.

This module provides sophisticated speaker detection capabilities using:
- DNN-based face detection with OpenCV
- Voice Activity Detection (VAD) using webrtcvad
- Audio-visual correlation for active speaker identification
- Frame-by-frame speaker tracking with lip distance analysis
"""
import cv2
import numpy as np
import logging
import webrtcvad
import wave
import contextlib
import collections
from typing import List, Tuple, Dict, Optional, Any
import os

# Configure logging
logger = logging.getLogger(__name__)

class SpeakerDetection:
    """Advanced speaker detection using audio-visual correlation."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize speaker detection with DNN models.
        
        Args:
            model_path: Path to model files directory
        """
        # Use relative path from the project root - works in both Docker and local environments
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, "..", "..", "..")
            model_path = os.path.join(project_root, "app", "models", "yt_shorts")
        self.model_path = os.path.abspath(model_path)
        
        # Load DNN face detection model (graceful failure)
        self.face_net = self._load_dnn_model()
        
        # Load Haar cascade as fallback (graceful failure)
        self.face_cascade = self._load_haar_cascade()
        
        # VAD configuration (graceful failure)
        self.vad = self._load_vad()
        
        # Speaker tracking variables
        self.speakers = {}  # Store speaker information
        self.speaker_id_counter = 0
        self.confidence_threshold = 0.7
        
        # Check if we have any working face detection
        self.has_face_detection = self.face_net is not None or self.face_cascade is not None
        self.has_vad = self.vad is not None
        
        if self.has_face_detection:
            logger.info("Speaker detection initialized with face detection")
        else:
            logger.warning("Speaker detection initialized without face detection - some features may be limited")
        
        if self.has_vad:
            logger.info("Voice Activity Detection (VAD) available")
        else:
            logger.warning("Voice Activity Detection (VAD) not available - using basic audio analysis")
    
    def _load_dnn_model(self) -> Optional[cv2.dnn.Net]:
        """Load DNN face detection model."""
        try:
            prototxt_path = os.path.join(self.model_path, 'deploy.prototxt')
            model_path = os.path.join(self.model_path, 'res10_300x300_ssd_iter_140000_fp16.caffemodel')
            
            if not os.path.exists(prototxt_path) or not os.path.exists(model_path):
                logger.warning("DNN model files not found - face detection will use fallback methods")
                return None
            
            net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            logger.info("DNN face detection model loaded successfully")
            return net
            
        except Exception as e:
            logger.warning(f"Failed to load DNN model: {e} - face detection will use fallback methods")
            return None
    
    def _load_haar_cascade(self) -> Optional[cv2.CascadeClassifier]:
        """Load Haar cascade face detection model."""
        try:
            haar_path = os.path.join(self.model_path, 'haarcascade_frontalface_default.xml')
            
            if not os.path.exists(haar_path):
                logger.warning("Haar cascade model file not found - face detection will be limited")
                return None
            
            cascade = cv2.CascadeClassifier(haar_path)
            if cascade.empty():
                logger.warning("Failed to load Haar cascade model - face detection will be limited")
                return None
            
            logger.info("Haar cascade face detection model loaded successfully")
            return cascade
            
        except Exception as e:
            logger.warning(f"Failed to load Haar cascade model: {e} - face detection will be limited")
            return None
    
    def _load_vad(self) -> Optional[webrtcvad.Vad]:
        """Load Voice Activity Detection."""
        try:
            vad = webrtcvad.Vad(3)  # Aggressiveness level 3 (most aggressive)
            logger.info("Voice Activity Detection (VAD) loaded successfully")
            return vad
            
        except Exception as e:
            logger.warning(f"Failed to load VAD: {e} - using basic audio analysis")
            return None
    
    def detect_faces_dnn(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect faces using DNN model.
        
        Args:
            frame: Input video frame
            
        Returns:
            List of face bounding boxes with confidence scores: [(x, y, w, h, confidence), ...]
        """
        if self.face_net is None:
            return []
            
        try:
            h, w = frame.shape[:2]
            
            # Create blob from frame
            blob = cv2.dnn.blobFromImage(
                frame, 1.0, (300, 300), [104, 117, 123], False, False
            )
            
            # Set input to the network
            self.face_net.setInput(blob)
            
            # Run forward pass
            detections = self.face_net.forward()
            
            faces = []
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                if confidence > self.confidence_threshold:
                    # Get bounding box coordinates
                    x1 = int(detections[0, 0, i, 3] * w)
                    y1 = int(detections[0, 0, i, 4] * h)
                    x2 = int(detections[0, 0, i, 5] * w)
                    y2 = int(detections[0, 0, i, 6] * h)
                    
                    # Convert to (x, y, w, h) format
                    x, y = x1, y1
                    w_box, h_box = x2 - x1, y2 - y1
                    
                    faces.append((x, y, w_box, h_box, confidence))
            
            return faces
            
        except Exception as e:
            logger.error(f"DNN face detection failed: {e}")
            return []
    
    def detect_faces_haar(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using Haar cascade as fallback.
        
        Args:
            frame: Input video frame
            
        Returns:
            List of face bounding boxes: [(x, y, w, h), ...]
        """
        if self.face_cascade is None:
            return []
            
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            # Convert numpy array to list of tuples
            return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
            
        except Exception as e:
            logger.error(f"Haar face detection failed: {e}")
            return []
    
    def detect_voice_activity(self, audio_data: bytes, sample_rate: int = 16000) -> bool:
        """
        Detect voice activity in audio segment.
        
        Args:
            audio_data: Audio data as bytes
            sample_rate: Audio sample rate
            
        Returns:
            True if voice activity detected
        """
        try:
            # VAD works with specific sample rates
            if sample_rate not in [8000, 16000, 32000, 48000]:
                logger.warning(f"Unsupported sample rate: {sample_rate}. Using 16000.")
                sample_rate = 16000
            
            # VAD requires 10ms, 20ms, or 30ms frames
            frame_duration = 30  # 30ms frames
            frame_length = int(sample_rate * frame_duration / 1000)
            
            # Process audio in chunks
            is_speech = False
            for i in range(0, len(audio_data), frame_length * 2):  # 2 bytes per sample
                frame = audio_data[i:i + frame_length * 2]
                
                if len(frame) < frame_length * 2:
                    break
                
                try:
                    if self.vad is not None and self.vad.is_speech(frame, sample_rate):
                        is_speech = True
                        break
                except:
                    continue
            
            return is_speech
            
        except Exception as e:
            logger.error(f"Voice activity detection failed: {e}")
            return False
    
    def calculate_lip_distance(self, face_region: np.ndarray) -> float:
        """
        Calculate lip distance to detect mouth movement.
        
        Args:
            face_region: Cropped face region
            
        Returns:
            Lip distance score (higher = more movement)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Focus on lower half of face (mouth region)
            h, w = gray.shape
            mouth_region = blurred[int(h*0.6):h, int(w*0.2):int(w*0.8)]
            
            # Calculate gradient to detect mouth opening
            grad_x = cv2.Sobel(mouth_region, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(mouth_region, cv2.CV_64F, 0, 1, ksize=3)
            
            # Calculate gradient magnitude
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Return mean magnitude as lip distance score
            return float(np.mean(magnitude))
            
        except Exception as e:
            logger.error(f"Lip distance calculation failed: {e}")
            return 0.0
    
    def track_speakers(self, frame: np.ndarray, audio_data: Optional[bytes] = None,
                      sample_rate: int = 16000) -> List[Dict[str, Any]]:
        """
        Track speakers in frame using audio-visual correlation.
        
        Args:
            frame: Current video frame
            audio_data: Corresponding audio data
            sample_rate: Audio sample rate
            
        Returns:
            List of speaker information dictionaries
        """
        try:
            # Detect faces using DNN
            faces = self.detect_faces_dnn(frame)
            
            # Fallback to Haar cascade if DNN fails
            if not faces:
                haar_faces = self.detect_faces_haar(frame)
                faces = [(x, y, w, h, 0.8) for x, y, w, h in haar_faces]
            
            # Detect voice activity
            voice_active = False
            if audio_data:
                voice_active = self.detect_voice_activity(audio_data, sample_rate)
            
            # Process each detected face
            speaker_info = []
            for i, (x, y, w, h, confidence) in enumerate(faces):
                # Extract face region
                face_region = frame[y:y+h, x:x+w]
                
                # Calculate lip movement
                lip_distance = self.calculate_lip_distance(face_region)
                
                # Determine if this person is likely speaking
                is_speaking = voice_active and lip_distance > 10.0  # Threshold for lip movement
                
                # Create speaker info
                speaker_data = {
                    'id': i,
                    'bbox': (x, y, w, h),
                    'confidence': confidence,
                    'lip_distance': lip_distance,
                    'is_speaking': is_speaking,
                    'voice_active': voice_active,
                    'center': (x + w//2, y + h//2)
                }
                
                speaker_info.append(speaker_data)
            
            return speaker_info
            
        except Exception as e:
            logger.error(f"Speaker tracking failed: {e}")
            return []
    
    def get_active_speaker(self, speaker_info: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Identify the most likely active speaker.
        
        Args:
            speaker_info: List of speaker information
            
        Returns:
            Active speaker data or None
        """
        try:
            # Filter speaking candidates
            speaking_candidates = [s for s in speaker_info if s['is_speaking']]
            
            if not speaking_candidates:
                # If no clear speaker, return face with highest confidence
                if speaker_info:
                    return max(speaker_info, key=lambda x: x['confidence'])
                return None
            
            # Return speaker with highest lip movement
            return max(speaking_candidates, key=lambda x: x['lip_distance'])
            
        except Exception as e:
            logger.error(f"Active speaker identification failed: {e}")
            return None
    
    def get_optimal_crop_center(self, speaker_info: List[Dict[str, Any]], 
                               frame_width: int, frame_height: int) -> Tuple[int, int]:
        """
        Calculate optimal crop center based on active speaker.
        
        Args:
            speaker_info: List of speaker information
            frame_width: Frame width
            frame_height: Frame height
            
        Returns:
            Optimal crop center coordinates (x, y)
        """
        try:
            active_speaker = self.get_active_speaker(speaker_info)
            
            if active_speaker:
                # Center on active speaker
                return active_speaker['center']
            else:
                # Default to frame center
                return (frame_width // 2, frame_height // 2)
                
        except Exception as e:
            logger.error(f"Optimal crop center calculation failed: {e}")
            return (frame_width // 2, frame_height // 2)

# Global instance
speaker_detector = SpeakerDetection()
