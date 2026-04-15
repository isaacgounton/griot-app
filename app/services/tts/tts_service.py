"""
Enhanced TTS (Text-to-Speech) Service for AI agents.

Delegates to the Speaches sidecar for Kokoro TTS generation.
"""
import os
import re
import time
import tempfile
from typing import List, Optional, Dict, Any
import logging

from app.services.speaches.speaches_client import speaches_client
from app.services.s3.s3 import s3_service

logger = logging.getLogger(__name__)

LANGUAGE_VOICE_CONFIG = {
    "en-us": [
        "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica",
        "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah",
        "af_sky", "am_adam", "am_echo", "am_eric", "am_fenrir",
        "am_liam", "am_michael", "am_onyx", "am_puck", "bm_george",
        "bm_lewis",
    ],
    "en-gb": [
        "bf_alan", "bf_isla", "bm_daniel", "bm_fable", "bm_griffin",
        "bm_hal", "bm_james", "bm_luke", "bm_male", "bm_santa",
    ],
    "es": ["em_alex", "ef_dora", "em_santa"],
    "fr": ["ff_siwis", "fm_alan", "fm_santa"],
    "hi": ["hf_alpha", "hf_beta", "hm_omega", "hm_santa"],
    "it": ["if_sara", "im_nicola", "im_santa"],
    "pt": ["pf_dora", "pm_alex", "pm_santa"],
    "ja": ["jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_santa"],
    "zh": ["zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"],
}


class TTSService:
    """TTS service for AI agents. Delegates to Speaches sidecar."""

    def __init__(self, engine: str = "kokoro"):
        self.engine = engine
        logger.info(f"TTSService initialized with engine={engine} (via Speaches)")

    async def generate_speech(
        self,
        text: str,
        language: str = "en-us",
        voice: Optional[str] = None,
        output_path: Optional[str] = None,
        speed: float = 1.0,
    ) -> Optional[str]:
        """Generate speech from text via Speaches sidecar.

        Returns:
            Path to generated audio file, or None if failed.
        """
        if not text.strip():
            logger.warning("Empty text provided for TTS")
            return None

        if output_path is None:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_{int(time.time())}_{hash(text) % 10000}.wav")

        # Pick voice
        if voice is None:
            voices = LANGUAGE_VOICE_CONFIG.get(language.lower(), LANGUAGE_VOICE_CONFIG["en-us"])
            voice = voices[0] if voices else "af_heart"

        try:
            audio_bytes = await speaches_client.generate_speech(
                text=text,
                voice=voice,
                model="speaches-ai/Kokoro-82M-v1.0-ONNX",
                response_format="wav",
                speed=speed,
            )

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"TTS generation completed: {output_path} ({len(audio_bytes)} bytes)")
            return output_path

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    async def process_job(self, job_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a TTS job."""
        try:
            text = job_data["text"]
            language = job_data.get("language", "en-us")
            voice = job_data.get("voice")
            speed = job_data.get("speed", 1.0)

            audio_path = await self.generate_speech(text, language, voice, speed=speed)

            if audio_path:
                s3_url = await s3_service.upload_file(audio_path, f"tts/{job_id}.wav")
                return {
                    "status": "completed",
                    "audio_url": s3_url,
                    "audio_path": audio_path,
                    "language": language,
                    "voice": voice,
                    "engine": self.engine,
                }
            else:
                return {"status": "failed", "error": "TTS generation failed"}

        except Exception as e:
            logger.error(f"TTS job processing failed: {e}")
            return {"status": "failed", "error": str(e)}


# Create TTS service instance
tts_service = TTSService()
