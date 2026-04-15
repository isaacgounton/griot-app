"""
Service for silence/speech detection in media files.

This service provides advanced silence detection with Voice Activity Detection (VAD)
support for better speech/silence boundary detection. It supports both modern
VAD-based speech detection and legacy FFmpeg silence detection.
"""
import os
import subprocess
import logging
import re
import tempfile
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from app.utils.media import download_media_file

# Configure logging
logger = logging.getLogger(__name__)

# Check for advanced VAD dependencies
try:
    import librosa
    import scipy.signal
    ADVANCED_VAD_AVAILABLE = True
    logger.info("Advanced VAD dependencies available")
except ImportError as e:
    librosa = None  # type: ignore
    scipy = None  # type: ignore
    ADVANCED_VAD_AVAILABLE = False
    logger.warning(f"Advanced VAD dependencies missing: {e}. Only basic FFmpeg detection available.")


class SilenceDetectionService:
    """
    Service for detecting silence and speech segments in media files.
    
    Supports both advanced Voice Activity Detection using librosa and
    legacy FFmpeg-based silence detection.
    """
    
    async def process_silence_job(self, job_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a silence detection job.
        
        Args:
            job_id: The ID of the job
            job_data: The job data containing detection parameters
            
        Returns:
            Dictionary with detection results
        """
        logger.info(f"Processing silence detection job {job_id}")
        
        media_url = job_data["media_url"]
        use_advanced_vad = job_data.get("use_advanced_vad", True)
        volume_threshold = job_data.get("volume_threshold", 40.0)
        
        # Convert Pydantic URL objects to strings
        media_url = str(media_url) if media_url else None
        
        try:
            if use_advanced_vad and ADVANCED_VAD_AVAILABLE:
                # Use enhanced VAD method
                segments = await self._detect_speech_segments_vad(
                    media_url=media_url,
                    volume_threshold=volume_threshold,
                    min_speech_duration=job_data.get("min_speech_duration", 0.5),
                    speech_padding_ms=job_data.get("speech_padding_ms", 50),
                    silence_padding_ms=job_data.get("silence_padding_ms", 450),
                    job_id=job_id
                )
                result_type = "speech_segments"
                method = "advanced_vad"
            else:
                # Use legacy FFmpeg method
                segments = await self._detect_silence_ffmpeg(
                    media_url=media_url,
                    start_time=job_data.get("start"),
                    end_time=job_data.get("end"),
                    noise_threshold=job_data.get("noise", "-30dB"),
                    min_duration=job_data.get("duration", 0.5),
                    mono=job_data.get("mono", True),
                    job_id=job_id
                )
                result_type = "silence_intervals"
                method = "ffmpeg_silencedetect"
            
            result = {
                "type": result_type,
                "method": method,
                "segments": segments,
                "total_segments": len(segments),
                "parameters": {
                    "volume_threshold": volume_threshold,
                    "min_duration": job_data.get("min_speech_duration" if use_advanced_vad else "duration", 0.5),
                    "speech_padding_ms": job_data.get("speech_padding_ms", 50),
                    "silence_padding_ms": job_data.get("silence_padding_ms", 450)
                }
            }
            
            logger.info(f"Job {job_id}: Detection completed - {len(segments)} {result_type} found")
            return result
            
        except Exception as e:
            logger.error(f"Error processing silence detection job {job_id}: {e}")
            raise RuntimeError(f"Failed to detect silence/speech: {str(e)}")
    
    async def process_analyze_job(self, job_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an audio analysis job.
        
        Args:
            job_id: The ID of the job
            job_data: The job data containing analysis parameters
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Processing audio analysis job {job_id}")
        
        media_url = job_data["media_url"]
        
        try:
            if not ADVANCED_VAD_AVAILABLE:
                raise RuntimeError("Audio analysis requires librosa and scipy. Please install these dependencies.")
            
            analysis = await self._analyze_audio_characteristics(
                media_url=media_url,
                job_id=job_id
            )
            
            logger.info(f"Job {job_id}: Audio analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing audio analysis job {job_id}: {e}")
            raise RuntimeError(f"Failed to analyze audio: {str(e)}")
    
    async def _detect_speech_segments_vad(self, media_url: str, volume_threshold: float = 40.0,
                                         min_speech_duration: float = 0.5, speech_padding_ms: int = 50,
                                         silence_padding_ms: int = 450, frame_duration_ms: int = 30,
                                         job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Advanced Voice Activity Detection using librosa and energy-based analysis."""
        logger.info(f"Starting advanced VAD for media URL: {media_url}")
        
        # Download media file
        input_path, _ = await download_media_file(media_url)
        
        try:
            # Load audio with librosa (automatically converts to mono)
            if librosa is None:
                raise RuntimeError("librosa is not available")
            y, sr = librosa.load(input_path, sr=16000, mono=True)
            logger.info(f"Loaded audio: duration={len(y)/sr:.2f}s, sample_rate={sr}Hz")
            
            if len(y) == 0:
                raise ValueError("Audio file is empty or corrupted")
            
            # Calculate frame parameters
            frame_length = int((frame_duration_ms / 1000) * sr)
            hop_length = frame_length // 2
            
            # Compute short-time energy (RMS)
            if librosa is None:
                raise RuntimeError("librosa is not available")
            rms_energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            
            # Convert to time frames
            times = librosa.frames_to_time(np.arange(len(rms_energy)), sr=sr, hop_length=hop_length)
            
            # Convert RMS to decibels
            rms_db = librosa.amplitude_to_db(rms_energy, ref=np.max)
            
            # Calculate dynamic threshold
            min_db = np.percentile(rms_db[rms_db > -100], 5)
            max_db = np.percentile(rms_db, 95)
            db_threshold = min_db + ((max_db - min_db) * volume_threshold) / 100
            
            logger.info(f"Dynamic thresholds - Min: {min_db:.1f}dB, Max: {max_db:.1f}dB, Threshold: {db_threshold:.1f}dB")
            
            # Initial speech detection
            speech_flags = rms_db > db_threshold
            
            # Apply temporal smoothing
            speech_flags = self._apply_temporal_smoothing(speech_flags, int(sr), hop_length, min_speech_duration)
            
            # Extract speech segments
            segments = self._extract_speech_segments(speech_flags, times, min_speech_duration)
            
            # Apply padding
            total_duration = len(y) / sr
            padded_segments = self._apply_segment_padding(segments, speech_padding_ms / 1000, total_duration)
            
            # Merge close segments
            if silence_padding_ms > 0:
                merged_segments = self._merge_close_segments(padded_segments, silence_padding_ms / 1000)
            else:
                merged_segments = padded_segments
            
            # Convert to output format
            result_segments = []
            for i, segment in enumerate(merged_segments):
                result_segments.append({
                    "id": i + 1,
                    "start": round(segment['start'], 3),
                    "end": round(segment['end'], 3),
                    "duration": round(segment['end'] - segment['start'], 3),
                    "start_formatted": self._format_time(segment['start']),
                    "end_formatted": self._format_time(segment['end']),
                    "confidence": self._calculate_segment_confidence(y, int(sr), segment['start'], segment['end'])
                })
            
            # Clean up
            os.unlink(input_path)
            logger.info(f"VAD completed: {len(result_segments)} speech segments detected")
            
            return result_segments
            
        except Exception as e:
            logger.error(f"VAD failed: {str(e)}")
            if os.path.exists(input_path):
                os.unlink(input_path)
            raise
    
    async def _detect_silence_ffmpeg(self, media_url: str, start_time: Optional[str] = None,
                                   end_time: Optional[str] = None, noise_threshold: str = "-30dB",
                                   min_duration: float = 0.5, mono: bool = False,
                                   job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect silence using FFmpeg's silencedetect filter."""
        logger.info(f"Starting FFmpeg silence detection for media URL: {media_url}")
        
        # Download media file
        input_path, _ = await download_media_file(media_url)
        
        try:
            # Parse time constraints
            start_seconds = 0
            end_seconds = float('inf')
            
            if start_time:
                try:
                    h, m, s = start_time.split(':')
                    start_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                except ValueError:
                    logger.warning(f"Could not parse start time '{start_time}', using 0")
            
            if end_time:
                try:
                    h, m, s = end_time.split(':')
                    end_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                except ValueError:
                    logger.warning(f"Could not parse end time '{end_time}', using infinity")
            
            # Build FFmpeg command
            cmd = ['ffmpeg', '-i', input_path, '-af']
            
            filter_string = ""
            if mono:
                filter_string += "pan=mono|c0=0.5*c0+0.5*c1,"
            
            # Validate inputs to prevent filter injection
            import re as _re
            if not _re.match(r'^-?\d+(\.\d+)?dB$', str(noise_threshold)):
                raise ValueError(f"Invalid noise threshold format: {noise_threshold}")
            if not isinstance(min_duration, (int, float)) or min_duration <= 0:
                raise ValueError(f"Invalid min_duration: {min_duration}")
            filter_string += f"silencedetect=noise={noise_threshold}:d={min_duration}"
            cmd.extend([filter_string, '-f', 'null', '-'])
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            # Run FFmpeg command
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            
            # Parse silence detection output
            silence_intervals = []
            silence_start_pattern = r'silence_start: (\d+\.?\d*)'
            silence_end_pattern = r'silence_end: (\d+\.?\d*) \| silence_duration: (\d+\.?\d*)'
            
            silence_starts = re.findall(silence_start_pattern, result.stderr)
            silence_ends_durations = re.findall(silence_end_pattern, result.stderr)
            
            # Combine results
            for i, (end, duration) in enumerate(silence_ends_durations):
                start = silence_starts[i] if i < len(silence_starts) else "0.0"
                
                start_time_float = float(start)
                end_time_float = float(end)
                duration_float = float(duration)
                
                # Filter by time range
                if end_time_float < start_seconds or start_time_float > end_seconds:
                    continue
                
                silence_intervals.append({
                    "start": self._format_time(start_time_float),
                    "end": self._format_time(end_time_float),
                    "duration": round(duration_float, 2)
                })
            
            # Clean up
            os.unlink(input_path)
            logger.info(f"FFmpeg silence detection completed: {len(silence_intervals)} intervals found")
            
            return silence_intervals
            
        except Exception as e:
            logger.error(f"FFmpeg silence detection failed: {str(e)}")
            if os.path.exists(input_path):
                os.unlink(input_path)
            raise
    
    async def _analyze_audio_characteristics(self, media_url: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze audio characteristics for optimal processing parameters."""
        logger.info(f"Analyzing audio characteristics for: {media_url}")
        
        # Download media file
        input_path, _ = await download_media_file(media_url)
        
        try:
            # Load audio
            if librosa is None:
                raise RuntimeError("librosa is not available")
            y, sr = librosa.load(input_path, sr=None, mono=True)
            
            # Basic characteristics
            duration = len(y) / sr
            rms = np.sqrt(np.mean(y ** 2))
            
            # Dynamic range analysis
            if librosa is None:
                raise RuntimeError("librosa is not available")
            rms_frames = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            rms_db = librosa.amplitude_to_db(rms_frames, ref=np.max)
            
            # Speech characteristics
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            
            # Recommended thresholds
            noise_floor = np.percentile(rms_db[rms_db > -100], 10)
            speech_level = np.percentile(rms_db, 80)
            dynamic_range = speech_level - noise_floor
            
            # Calculate recommended volume threshold
            if dynamic_range > 30:
                recommended_threshold = 30
            elif dynamic_range > 20:
                recommended_threshold = 40
            else:
                recommended_threshold = 50
            
            analysis = {
                "duration": round(duration, 2),
                "sample_rate": int(sr),
                "rms_level": round(float(rms), 4),
                "noise_floor_db": round(float(noise_floor), 1),
                "speech_level_db": round(float(speech_level), 1),
                "dynamic_range_db": round(float(dynamic_range), 1),
                "zero_crossing_rate": round(float(zero_crossing_rate), 4),
                "spectral_centroid_hz": round(float(spectral_centroid), 1),
                "recommended_volume_threshold": recommended_threshold,
                "audio_quality": "high" if dynamic_range > 25 else "medium" if dynamic_range > 15 else "low"
            }
            
            # Clean up
            os.unlink(input_path)
            logger.info(f"Audio analysis completed: {analysis['audio_quality']} quality, {dynamic_range:.1f}dB range")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {str(e)}")
            if os.path.exists(input_path):
                os.unlink(input_path)
            raise
    
    def _apply_temporal_smoothing(self, speech_flags: np.ndarray, sr: int, hop_length: int,
                                 min_duration: float) -> np.ndarray:
        """Apply temporal smoothing to reduce noise in speech detection."""
        min_frames = int((min_duration * sr) / hop_length)
        kernel_size = min(min_frames // 2, 5)
        
        if kernel_size > 1:
            if scipy is None or scipy.signal is None:
                raise RuntimeError("scipy.signal is not available")
            speech_flags = scipy.signal.medfilt(speech_flags.astype(float), kernel_size=kernel_size) > 0.5
        
        # Fill short gaps
        gap_fill_frames = min_frames // 4
        speech_flags = self._fill_short_gaps(speech_flags, gap_fill_frames)
        
        return speech_flags
    
    def _fill_short_gaps(self, speech_flags: np.ndarray, max_gap_frames: int) -> np.ndarray:
        """Fill short gaps between speech segments."""
        result = speech_flags.copy()
        
        diff = np.diff(speech_flags.astype(int))
        speech_ends = np.where(diff == -1)[0]
        speech_starts = np.where(diff == 1)[0]
        
        for end_idx in speech_ends:
            next_starts = speech_starts[speech_starts > end_idx]
            if len(next_starts) > 0:
                next_start = next_starts[0]
                gap_size = next_start - end_idx
                
                if gap_size <= max_gap_frames:
                    result[end_idx:next_start+1] = True
        
        return result
    
    def _extract_speech_segments(self, speech_flags: np.ndarray, times: np.ndarray,
                               min_duration: float) -> List[Dict[str, float]]:
        """Extract speech segments from boolean flags."""
        segments = []
        in_speech = False
        segment_start = 0
        
        for time_val, is_speech in zip(times, speech_flags):
            if is_speech and not in_speech:
                segment_start = time_val
                in_speech = True
            elif not is_speech and in_speech:
                duration = time_val - segment_start
                if duration >= min_duration:
                    segments.append({'start': segment_start, 'end': time_val})
                in_speech = False
        
        # Handle case where audio ends during speech
        if in_speech and len(times) > 0:
            duration = times[-1] - segment_start
            if duration >= min_duration:
                segments.append({'start': segment_start, 'end': times[-1]})
        
        return segments
    
    def _apply_segment_padding(self, segments: List[Dict[str, float]], padding: float,
                             total_duration: float) -> List[Dict[str, float]]:
        """Apply padding around speech segments."""
        padded_segments = []
        
        for segment in segments:
            padded_start = max(0, segment['start'] - padding)
            padded_end = min(total_duration, segment['end'] + padding)
            padded_segments.append({'start': padded_start, 'end': padded_end})
        
        return padded_segments
    
    def _merge_close_segments(self, segments: List[Dict[str, float]],
                            max_gap: float) -> List[Dict[str, float]]:
        """Merge segments that are close together."""
        if not segments:
            return []
        
        sorted_segments = sorted(segments, key=lambda x: x['start'])
        merged = [sorted_segments[0]]
        
        for current in sorted_segments[1:]:
            last_merged = merged[-1]
            gap = current['start'] - last_merged['end']
            
            if gap <= max_gap:
                merged[-1]['end'] = max(last_merged['end'], current['end'])
            else:
                merged.append(current)
        
        return merged
    
    def _calculate_segment_confidence(self, y: np.ndarray, sr: int, start_time: float,
                                    end_time: float) -> float:
        """Calculate confidence score for a speech segment."""
        try:
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            if start_sample >= len(y) or end_sample <= start_sample:
                return 0.0
            
            segment_audio = y[start_sample:end_sample]
            
            # Calculate features
            rms = np.sqrt(np.mean(segment_audio ** 2))
            if librosa is None:
                raise RuntimeError("librosa is not available")
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(segment_audio))
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=segment_audio, sr=sr))
            
            # Normalize and combine
            rms_score = min(1.0, float(rms) * 10)
            zcr_score = min(1.0, float(zero_crossing_rate) * 5)
            sc_score = min(1.0, float(spectral_centroid) / 4000)
            
            confidence = (rms_score * 0.5 + zcr_score * 0.3 + sc_score * 0.2)
            return round(confidence, 3)
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 0.5
    
    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to HH:MM:SS.mmm format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:06.3f}"


# Create service instance
silence_service = SilenceDetectionService()