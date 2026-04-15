import os
import re
import tempfile
import logging
from typing import Dict, Any, List, Tuple, Optional
import aiohttp
import asyncio
from app.services.speaches.stt_client import transcribe_audio
from app.utils.logging import get_logger

logger = get_logger(module="enhanced_caption_timing", component="ai_services")


class EnhancedCaptionTiming:
    """Enhanced caption timing service using Speaches sidecar for precise word-level timing."""

    # Map legacy model size names to Speaches model identifiers
    MODEL_SIZE_MAP = {
        "tiny": "Systran/faster-whisper-tiny",
        "base": "Systran/faster-whisper-base",
        "small": "Systran/faster-whisper-small",
        "medium": "Systran/faster-whisper-medium",
        "large": "Systran/faster-whisper-large-v3",
    }

    def __init__(self):
        pass
    
    async def _download_audio_file(self, audio_url: str) -> str:
        """Download audio file from URL to temp location."""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        with open(temp_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        logger.info(f"Downloaded audio file to: {temp_path}")
                        return temp_path
                    else:
                        raise ValueError(f"Failed to download audio: HTTP {response.status}")
            
        except Exception as e:
            logger.error(f"Error downloading audio file: {e}")
            raise ValueError(f"Audio download failed: {str(e)}")
    
    def _clean_word(self, word: str) -> str:
        """Clean word by removing unwanted punctuation."""
        return re.sub(r'[^\w\s\-_"\'\']', '', word)
    
    def _split_words_by_size(self, words: List[str], max_caption_size: int) -> List[str]:
        """Split words into caption-sized chunks."""
        half_caption_size = max_caption_size // 2
        captions = []
        
        words_copy = words.copy()
        while words_copy:
            caption = words_copy[0]
            words_copy = words_copy[1:]
            
            while words_copy and len(caption + ' ' + words_copy[0]) <= max_caption_size:
                caption += ' ' + words_copy[0]
                words_copy = words_copy[1:]
                if len(caption) >= half_caption_size and words_copy:
                    break
            
            captions.append(caption)
        
        return captions
    
    def _get_timestamp_mapping(self, whisper_analysis: Dict) -> Dict[Tuple[int, int], float]:
        """Create mapping from text positions to timestamps."""
        index = 0
        location_to_timestamp = {}
        
        for segment in whisper_analysis.get('segments', []):
            for word in segment.get('words', []):
                word_text = word.get('text', '')
                new_index = index + len(word_text) + 1
                end_time = word.get('end', 0)
                location_to_timestamp[(index, new_index)] = end_time
                index = new_index
        
        return location_to_timestamp
    
    def _interpolate_time_from_dict(self, word_position: int, timestamp_dict: Dict) -> Optional[float]:
        """Interpolate timestamp for a word position."""
        for key, value in timestamp_dict.items():
            if key[0] <= word_position <= key[1]:
                return value
        return None
    
    def _generate_captions_with_time(self, segments: List, max_caption_size: int = 15, 
                                   consider_punctuation: bool = False) -> List[Tuple[Tuple[float, float], str]]:
        """Generate timed captions from transcription segments."""
        caption_pairs = []
        
        for segment in segments:
            # Extract text from segment
            text = segment.text.strip()
            start_time = segment.start
            end_time = segment.end
            
            if not text:
                continue
                
            # Split long segments into smaller captions
            if consider_punctuation:
                sentences = re.split(r'(?<=[.!?]) +', text)
                sub_captions = []
                for sentence in sentences:
                    sub_captions.extend(self._split_words_by_size(sentence.split(), max_caption_size))
            else:
                words = text.split()
                sub_captions = self._split_words_by_size(words, max_caption_size)
            
            # Distribute timing across sub-captions
            if len(sub_captions) > 1:
                duration = end_time - start_time
                caption_duration = duration / len(sub_captions)
                
                for i, caption in enumerate(sub_captions):
                    if isinstance(caption, list):
                        caption_text = ' '.join(caption)
                    else:
                        caption_text = caption
                        
                    caption_start = start_time + (i * caption_duration)
                    caption_end = start_time + ((i + 1) * caption_duration)
                    
                    if caption_text.strip():
                        caption_pairs.append(((caption_start, caption_end), caption_text.strip()))
            else:
                # Single caption for this segment
                caption_text = ' '.join(sub_captions[0]) if isinstance(sub_captions[0], list) else sub_captions[0]
                if caption_text.strip():
                    caption_pairs.append(((start_time, end_time), caption_text.strip()))
        
        return caption_pairs
    
    def _create_srt_content(self, caption_pairs: List[Tuple[Tuple[float, float], str]]) -> str:
        """Create SRT content from caption pairs."""
        srt_content = ""
        
        for i, ((start_time, end_time), text) in enumerate(caption_pairs, 1):
            start_srt = self._seconds_to_srt_time(start_time)
            end_srt = self._seconds_to_srt_time(end_time)
            
            srt_content += f"{i}\n"
            srt_content += f"{start_srt} --> {end_srt}\n"
            srt_content += f"{text}\n\n"
        
        return srt_content
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def generate_enhanced_captions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced timed captions using whisper-timestamped.
        
        Args:
            params: Dictionary containing:
                - audio_url: URL to audio file
                - model_size: Whisper model size ('base', 'small', 'medium', 'large')
                - max_words_per_line: Maximum words per caption line
                - consider_punctuation: Whether to split on sentence boundaries
                - language: Language hint for Whisper
        
        Returns:
            Dictionary containing timed captions and metadata
        """
        audio_url = params.get('audio_url')
        model_size = params.get('model_size', 'base')
        max_words_per_line = params.get('max_words_per_line', 10)
        consider_punctuation = params.get('consider_punctuation', False)
        language = params.get('language')
        
        if not audio_url:
            raise ValueError("Audio URL is required for enhanced caption timing")
        
        temp_audio_path = None
        
        try:
            # Download audio file
            temp_audio_path = await self._download_audio_file(audio_url)

            # Resolve model identifier for Speaches sidecar
            speaches_model = self.MODEL_SIZE_MAP.get(model_size, f"Systran/faster-whisper-{model_size}")

            # Transcribe with timestamps via Speaches sidecar
            logger.info("Starting Speaches sidecar transcription")

            segments, info = await transcribe_audio(
                file_path=temp_audio_path,
                model=speaches_model,
                language=language,
                word_timestamps=True,
            )
            
            logger.info("Whisper transcription completed")
            
            # Generate timed captions
            caption_pairs = self._generate_captions_with_time(
                segments, 
                max_words_per_line, 
                consider_punctuation
            )
            
            # Create SRT content
            srt_content = self._create_srt_content(caption_pairs)
            
            # Extract word-level timing from segments
            word_timestamps = []
            for segment in segments:
                # Estimate word timings from segment timing when word-level
                # timestamps are not available from the transcription
                words = segment.text.strip().split()
                if words:
                    segment_duration = segment.end - segment.start
                    words_per_second = len(words) / segment_duration if segment_duration > 0 else 1
                    
                    for i, word in enumerate(words):
                        word_start = segment.start + (i / words_per_second)
                        word_end = segment.start + ((i + 1) / words_per_second)
                        word_timestamps.append({
                            'word': word.strip(),
                            'start': word_start,
                            'end': word_end,
                            'confidence': 1.0  # Default confidence
                        })
            
            # Extract segments info
            segment_info = []
            for segment in segments:
                segment_info.append({
                    'text': segment.text.strip(),
                    'start': segment.start,
                    'end': segment.end
                })
            
            # Extract full text from all segments
            full_text = ' '.join(segment.text.strip() for segment in segments)
            
            # Calculate total duration from segments
            total_duration = max(segment.end for segment in segments) if segments else 0
            
            return {
                'text': full_text,
                'srt_content': srt_content,
                'caption_pairs': caption_pairs,
                'word_timestamps': word_timestamps,
                'segments': segment_info,
                'model_used': model_size,
                'total_duration': total_duration,
                'language_detected': info.language if hasattr(info, 'language') else 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Enhanced caption timing failed: {e}")
            raise ValueError(f"Caption timing failed: {str(e)}")
        
        finally:
            # Cleanup temp file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                    logger.debug(f"Cleaned up temp audio file: {temp_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")


# Create singleton instance
enhanced_caption_timing = EnhancedCaptionTiming()