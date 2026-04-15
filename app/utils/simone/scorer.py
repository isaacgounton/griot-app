from __future__ import annotations

import cv2
import logging
import os
import shutil

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from pytesseract import Output
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract OCR not available - frame scoring will use fallback method")


class Scorer:
    def __init__(self, frames, keywords, path_to_tesseract):
        self.frames = frames
        # Ensure keywords is a list of strings, not a raw string
        if isinstance(keywords, str):
            self.keywords = [k.strip() for k in keywords.replace(",", "\n").split("\n") if k.strip()]
        else:
            self.keywords = keywords
        self.path_to_tesseract = path_to_tesseract
        self.tesseract_available = self._check_tesseract_availability()

    def _check_tesseract_availability(self):
        """Check if Tesseract is available and working"""
        if not TESSERACT_AVAILABLE:
            return False
        
        try:
            # Check if tesseract binary exists
            if not os.path.exists(self.path_to_tesseract):
                # Try to find tesseract in PATH
                tesseract_path = shutil.which('tesseract')
                if tesseract_path:
                    self.path_to_tesseract = tesseract_path
                    logger.info(f"Found tesseract at: {tesseract_path}")
                else:
                    logger.warning(f"Tesseract not found at {self.path_to_tesseract} or in PATH")
                    return False
            
            # Test tesseract with a simple call
            pytesseract.pytesseract.tesseract_cmd = self.path_to_tesseract
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is available and working")
            return True
            
        except Exception as e:
            logger.warning(f"Tesseract OCR not available: {e}")
            return False

    def _extract_text_with_tesseract(self, frame):
        """Extract text using Tesseract OCR"""
        try:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            extracted_text = pytesseract.image_to_string(
                gray_frame,
                config="--psm 6",
                output_type=Output.STRING,
            )
            return extracted_text.strip()
        except Exception as e:
            logger.warning(f"Tesseract text extraction failed: {e}")
            return ""

    def _fallback_frame_scoring(self, frame):
        """Fallback frame scoring when OCR is not available"""
        try:
            # Simple image analysis-based scoring
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Check for text-like regions using edge detection
            edges = cv2.Canny(gray_frame, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Score based on number of potential text regions
            text_regions = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 10000:  # Reasonable size for text
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    if 0.2 < aspect_ratio < 5.0:  # Text-like aspect ratio
                        text_regions += 1
            
            # Normalize score (more text regions = higher score)
            return min(text_regions / 10, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.warning(f"Fallback frame scoring failed: {e}")
            return 0.5  # Default middle score

    def score_frames(self):
        """Score frames based on keyword relevance"""
        scores = []
        
        if not self.tesseract_available:
            logger.info("Using fallback frame scoring (no OCR)")
            # Use fallback scoring when tesseract is not available
            for i, frame in enumerate(self.frames):
                score = self._fallback_frame_scoring(frame)
                # Add some variation based on position (prefer middle frames)
                position_bonus = 1.0 - abs(i - len(self.frames) / 2) / (len(self.frames) / 2) * 0.3
                final_score = score * position_bonus
                scores.append(final_score)
            return scores
        
        # Use OCR-based scoring when tesseract is available
        for frame in self.frames:
            extracted_text = self._extract_text_with_tesseract(frame)
            
            frame_score = 0
            if extracted_text:
                # Score based on keyword matches
                for keyword in self.keywords:
                    if keyword.lower() in extracted_text.lower():
                        frame_score += 1
            else:
                # If OCR fails, use fallback scoring for this frame
                frame_score = self._fallback_frame_scoring(frame) * len(self.keywords)
            
            scores.append(frame_score)
        
        return scores