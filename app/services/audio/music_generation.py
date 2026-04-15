"""
Music generation service using Meta's MusicGen model.
"""
import os
import logging
import uuid
from typing import Any

# Try to import dependencies with graceful fallback
try:
    import numpy as np
    import scipy.io.wavfile
    from transformers import pipeline
    MUSIC_GENERATION_AVAILABLE = True
except ImportError as e:
    MUSIC_GENERATION_AVAILABLE = False
    missing_deps = str(e)

from app.services.s3.s3 import s3_service

logger = logging.getLogger(__name__)


class MusicGenerationService:
    """Service for generating music using Meta's MusicGen model"""
    
    def __init__(self):
        self.model_cache = {}
        self.temp_dir = os.environ.get('LOCAL_STORAGE_PATH', '/tmp')
        if not MUSIC_GENERATION_AVAILABLE:
            logger.warning(f"Music generation dependencies not available: {missing_deps}. Music generation features will be disabled.")
        
    def _get_model(self, model_size: str = "small"):
        """Get or load the MusicGen model with caching"""
        if not MUSIC_GENERATION_AVAILABLE:
            raise Exception("Music generation dependencies not available. Please install: transformers, torch, scipy, numpy")
        
        model_name = f"facebook/musicgen-stereo-{model_size}"
        
        if model_name not in self.model_cache:
            try:
                logger.info(f"Loading MusicGen model: {model_name} (this may take several minutes on first load)")
                self.model_cache[model_name] = pipeline(
                    "text-to-audio", 
                    model_name,
                    device=-1  # CPU usage
                )
                logger.info(f"Model {model_name} loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise Exception(f"Failed to load MusicGen model: {str(e)}")
        
        return self.model_cache[model_name]
    
    async def process_music_generation(self, job_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Process music generation job.
        
        Args:
            job_id: The job ID (unused but required for job queue signature)
            data: Dictionary containing music generation parameters
            
        Returns:
            Dictionary with music generation results
        """
        if not MUSIC_GENERATION_AVAILABLE:
            raise Exception("Music generation dependencies not available. Please install: transformers, torch, scipy, numpy")
        
        try:
            description = data.get('description')
            duration = data.get('duration', 8)
            model_size = data.get('model_size', 'small')
            output_format = data.get('output_format', 'wav')
            
            # Ensure duration is a valid number
            if duration is None or not isinstance(duration, (int, float)) or duration <= 0:
                duration = 8  # Default to 8 seconds
            
            if not description:
                raise ValueError("Description is required for music generation")
            
            logger.info(f"Generating music for description: '{description}' (duration: {duration}s)")
            
            # Get the model (this is the slowest part on first load)
            logger.info("Loading MusicGen model - this may take up to 2-3 minutes on first request")
            synthesizer = self._get_model(model_size)
            logger.info("Model loaded, starting music generation")
            
            # Generate unique filename
            filename = f"musicgen_{job_id or uuid.uuid4().hex}"
            temp_wav_path = os.path.join(self.temp_dir, f"{filename}.wav")
            
            # Generate music with reduced tokens for faster processing
            # Reduce tokens for CPU processing: 20 tokens per second instead of 50
            max_tokens = min(duration * 20, 300)  # Cap at 300 tokens to prevent excessive processing time
            
            logger.info(f"Generating music with {max_tokens} tokens (duration: {duration}s)")
            music = synthesizer(description, forward_params={"max_new_tokens": max_tokens})
            
            # Save as WAV file
            # Ensure sampling_rate is a plain Python int (scipy struct.pack needs it)
            sampling_rate = int(music["sampling_rate"])
            audio_data = music["audio"]

            # Ensure audio data is in the correct format
            if isinstance(audio_data, np.ndarray):
                # Pipeline returns shape (channels, samples) — transpose to (samples, channels)
                if audio_data.ndim > 1:
                    if audio_data.shape[0] <= audio_data.shape[1]:
                        # Shape is (channels, samples) — transpose
                        audio_data = audio_data.T
                else:
                    # Mono — duplicate to stereo (samples, 2)
                    audio_data = np.column_stack((audio_data, audio_data))

                # Normalize audio if needed
                max_val = np.max(np.abs(audio_data))
                if max_val > 1.0:
                    audio_data = audio_data / max_val

                # Convert to 16-bit PCM
                audio_data = (audio_data * 32767).astype(np.int16)

            # Save WAV file
            scipy.io.wavfile.write(temp_wav_path, rate=sampling_rate, data=audio_data)
            
            # For now, only support WAV output (MP3 conversion would require ffmpeg)
            if output_format.lower() == "mp3":
                logger.warning("MP3 output not yet supported, defaulting to WAV")
                output_format = "wav"
            
            output_path = temp_wav_path
            
            # Upload to S3
            file_size = os.path.getsize(output_path)
            object_name = f"audio/music/{filename}.{output_format}"
            
            audio_url = await s3_service.upload_file(
                file_path=output_path,
                object_name=object_name
            )
            
            # Clean up temp file
            if os.path.exists(output_path):
                os.remove(output_path)
            
            # Calculate actual duration from generated audio
            # For stereo audio, audio_data.shape is (samples, channels)
            if audio_data.ndim > 1:
                actual_duration = audio_data.shape[0] / sampling_rate
            else:
                actual_duration = len(audio_data) / sampling_rate
            
            return {
                "audio_url": audio_url,
                "duration": round(actual_duration, 2),
                "model_used": f"facebook/musicgen-stereo-{model_size}",
                "file_size": file_size,
                "sampling_rate": sampling_rate
            }
            
        except Exception as e:
            logger.error(f"Music generation failed: {str(e)}", exc_info=True)
            raise Exception(f"Music generation failed: {str(e)}")
    
    def clear_cache(self):
        """Clear model cache to free memory"""
        self.model_cache.clear()
        logger.info("MusicGen model cache cleared")


# Create a singleton instance
music_generation_service = MusicGenerationService()