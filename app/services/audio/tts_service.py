"""
Unified TTS service supporting multiple providers.

Kokoro and Piper are delegated to the Speaches sidecar.
Edge TTS remains in-process.
"""
import os
import uuid
import logging
from typing import Optional, Dict, Any, List

from app.services.audio.edge_tts_service import edge_tts_service
from app.services.speaches.speaches_client import speaches_client

logger = logging.getLogger(__name__)


class TTSService:
    """Unified Text-to-Speech service supporting multiple providers."""

    def __init__(self):
        self.default_provider = os.environ.get("TTS_PROVIDER", "kokoro").lower()
        self.default_voice = os.environ.get("TTS_VOICE", "af_alloy")
        logger.info(f"TTS Service initialized with default provider: {self.default_provider}, default voice: {self.default_voice}")

    # ------------------------------------------------------------------
    # Kokoro / Piper via Speaches sidecar
    # ------------------------------------------------------------------
    async def generate_speech_kokoro(
        self,
        text: str,
        voice: str = "af_alloy",
        volume_multiplier: float = 1.0,
        normalization_options: Optional[Dict] = None,
        return_timestamps: bool = False,
        lang_code: Optional[str] = None,
        response_format: str = "wav",
        speed: float = 1.0,
    ) -> bytes:
        """Generate speech via Speaches Kokoro model."""
        logger.info(f"Generating speech with Kokoro (via Speaches) voice={voice}")
        return await speaches_client.generate_speech(
            text=text,
            voice=voice,
            model="speaches-ai/Kokoro-82M-v1.0-ONNX",
            response_format=response_format,
            speed=speed,
        )

    async def generate_speech_piper(
        self,
        text: str,
        voice: str = "en_US-lessac-medium",
        speed: float = 1.0,
        response_format: str = "wav",
        remove_filter: bool = False,
    ) -> bytes:
        """Generate speech via Speaches Piper model."""
        logger.info(f"Generating speech with Piper (via Speaches) voice={voice}")
        return await speaches_client.generate_speech(
            text=text,
            voice=voice,
            model="piper",
            response_format=response_format,
            speed=speed,
        )

    # ------------------------------------------------------------------
    # Main dispatcher
    # ------------------------------------------------------------------
    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        volume_multiplier: float = 1.0,
        normalization_options: Optional[Dict] = None,
        return_timestamps: bool = False,
        lang_code: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """Generate speech using the specified or default TTS provider.

        Returns:
            Tuple of (audio_data_bytes, actual_provider_used)
        """
        if not provider:
            provider = self.default_provider
        provider = provider.lower()
        logger.info(f"Generating speech using provider: {provider}")

        if not voice:
            voice = self.default_voice

        if provider == "kokoro":
            kokoro_voice = self._map_voice_to_provider(voice, "kokoro")
            logger.info(f"Mapped voice '{voice}' to Kokoro voice '{kokoro_voice}'")
            try:
                audio_data = await self.generate_speech_kokoro(
                    text=text,
                    voice=kokoro_voice,
                    volume_multiplier=volume_multiplier,
                    normalization_options=normalization_options,
                    return_timestamps=return_timestamps,
                    lang_code=lang_code,
                    response_format=response_format,
                    speed=speed,
                )
                return audio_data, "kokoro"
            except Exception as e:
                logger.warning(f"Kokoro TTS failed ({e}), falling back to Edge TTS")
                provider = "edge"
                # Fall through to edge provider below

        if provider == "piper":
            piper_voice = self._map_voice_to_provider(voice, "piper")
            logger.info(f"Mapped voice '{voice}' to Piper voice '{piper_voice}'")
            try:
                audio_data = await self.generate_speech_piper(
                    text=text,
                    voice=piper_voice,
                    speed=speed,
                    response_format=response_format,
                )
                return audio_data, "piper"
            except Exception as e:
                logger.warning(f"Piper TTS failed ({e}), falling back to Edge TTS")
                provider = "edge"
                # Fall through to edge provider below

        if provider == "edge":
            edge_voice = self._map_voice_to_provider(voice, "edge")
            logger.info(f"Mapped voice '{voice}' to Edge TTS voice '{edge_voice}'")

            try:
                is_valid = await edge_tts_service.validate_voice(edge_voice)
                if not is_valid:
                    logger.warning(f"Voice validation failed for '{edge_voice}'")

                audio_file_path = await edge_tts_service.generate_speech(
                    text=text,
                    voice=edge_voice,
                    response_format=response_format,
                    speed=speed,
                    remove_filter=False,
                )

                with open(audio_file_path, "rb") as f:
                    audio_data = f.read()

                try:
                    os.unlink(audio_file_path)
                except OSError:
                    pass

                logger.info(f"Generated {len(audio_data)} bytes using Edge TTS")
                return audio_data, "edge"

            except ValueError as e:
                if "empty after preprocessing" in str(e).lower():
                    logger.warning("Text preprocessing removed all content. Retrying without filter...")
                    try:
                        audio_file_path = await edge_tts_service.generate_speech(
                            text=text,
                            voice=edge_voice,
                            response_format=response_format,
                            speed=speed,
                            remove_filter=True,
                        )
                        with open(audio_file_path, "rb") as f:
                            audio_data = f.read()
                        try:
                            os.unlink(audio_file_path)
                        except OSError:
                            pass
                        return audio_data, "edge"
                    except Exception as retry_error:
                        raise ValueError(
                            f"Edge TTS failed even without text filtering. "
                            f"Original: {e}. Retry: {retry_error}"
                        )
                raise ValueError(f"Failed to generate speech with Edge TTS: {e}")

            except Exception as e:
                raise ValueError(
                    f"Failed to generate speech with Edge TTS: {e}. "
                    f"Voice: {edge_voice}, Text length: {len(text)}"
                )

        else:
            raise ValueError(f"Unsupported TTS provider: {provider}. Supported: kokoro, piper, edge")

    # ------------------------------------------------------------------
    # Streaming (Edge TTS only)
    # ------------------------------------------------------------------
    async def generate_speech_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        speed: float = 1.0,
        remove_filter: bool = False,
    ):
        """Generate streaming speech. Only Edge TTS supports streaming."""
        if not provider:
            provider = self.default_provider
        provider = provider.lower()

        if not voice:
            voice = self.default_voice

        if provider == "edge":
            async for chunk in edge_tts_service.generate_speech_stream(
                text=text, voice=voice, speed=speed, remove_filter=remove_filter
            ):
                yield chunk
        elif provider in ("kokoro", "piper"):
            raise ValueError(f"{provider} TTS does not support streaming. Use regular generation instead.")
        else:
            raise ValueError(f"Unsupported TTS provider for streaming: {provider}. Only 'edge' supports streaming.")

    # ------------------------------------------------------------------
    # Voice mapping
    # ------------------------------------------------------------------
    def _map_voice_to_provider(self, voice: str, target_provider: str) -> str:
        """Map a voice name to be compatible with the target TTS provider."""
        # Edge TTS voice (xx-XX-NameNeural)
        if "-" in voice and "Neural" in voice:
            if target_provider == "edge":
                return voice
            elif target_provider == "kokoro":
                lang_code = voice.split("-")[0]
                lang_to_kokoro = {
                    "en": "af_heart", "fr": "ff_siwis", "es": "em_alex",
                    "it": "if_sara", "pt": "pf_dora", "ja": "jf_alpha",
                    "zh": "zf_xiaoxiao", "hi": "hf_alpha", "de": "am_michael",
                }
                return lang_to_kokoro.get(lang_code, "af_heart")
            elif target_provider == "piper":
                lang_code = voice.split("-")[0]
                lang_to_piper = {
                    "en": "en_US-lessac-medium", "fr": "fr_FR-siwis-medium",
                    "es": "es_ES-spanish_male-medium", "it": "it_IT-diego-medium",
                    "pt": "pt_BR-faber-medium", "ja": "ja_JP-kokoro-medium",
                    "zh": "zh_CN-huayan-medium", "de": "de_DE-thorsten-medium",
                }
                return lang_to_piper.get(lang_code, "en_US-lessac-medium")

        # Kokoro voice (af_, am_, etc.)
        elif voice.startswith(("af_", "am_", "bf_", "bm_", "jf_", "jm_", "zf_", "zm_",
                               "ef_", "em_", "ff_", "hf_", "hm_", "if_", "im_", "pf_", "pm_")):
            if target_provider == "kokoro":
                return voice
            elif target_provider == "edge":
                return self._get_edge_fallback_voice(voice)
            elif target_provider == "piper":
                kokoro_to_piper = {
                    "af_heart": "en_US-lessac-medium", "af_bella": "en_US-amy-medium",
                    "af_alloy": "en_US-lessac-medium", "am_michael": "en_US-ryan-medium",
                    "bf_emma": "en_GB-southern_english_female-medium",
                    "bm_george": "en_GB-alan-medium", "ff_siwis": "fr_FR-siwis-medium",
                }
                return kokoro_to_piper.get(voice, "en_US-lessac-medium")

        # Piper voice (lang_region-name-quality)
        elif "_" in voice and "-" in voice:
            if target_provider == "piper":
                return voice
            elif target_provider == "kokoro":
                piper_to_kokoro = {
                    "en_US-lessac-medium": "af_heart", "en_US-lessac-low": "af_heart",
                    "en_US-lessac-high": "af_heart", "en_US-amy-medium": "af_bella",
                    "en_US-amy-low": "af_bella", "en_US-ryan-medium": "am_michael",
                    "en_US-ryan-low": "am_michael", "en_US-ryan-high": "am_michael",
                    "en_GB-alan-medium": "bm_george", "en_GB-alan-low": "bm_george",
                    "en_GB-southern_english_female-medium": "bf_emma",
                    "fr_FR-siwis-medium": "ff_siwis", "fr_FR-siwis-low": "ff_siwis",
                }
                return piper_to_kokoro.get(voice, "af_heart")
            elif target_provider == "edge":
                piper_to_edge = {
                    "en_US-lessac-medium": "en-US-AriaNeural",
                    "en_US-amy-medium": "en-US-AmberNeural",
                    "en_US-ryan-medium": "en-US-RyanNeural",
                    "en_GB-alan-medium": "en-GB-RyanNeural",
                    "en_GB-southern_english_female-medium": "en-GB-SoniaNeural",
                    "fr_FR-siwis-medium": "fr-FR-DeniseNeural",
                }
                return piper_to_edge.get(voice, "en-US-AriaNeural")

        # Unknown format defaults
        defaults = {"kokoro": "af_heart", "piper": "en_US-lessac-medium", "edge": "en-US-AriaNeural"}
        return defaults.get(target_provider, voice)

    def _get_edge_fallback_voice(self, kokoro_voice: str) -> str:
        """Map Kokoro voice names to equivalent Edge TTS voices."""
        voice_mapping = {
            "af_alloy": "en-US-AriaNeural", "af_heart": "en-US-JennyNeural",
            "af_sky": "en-US-GuyNeural", "af_nova": "en-US-SaraNeural",
            "af_shimmer": "en-US-AmberNeural", "af_echo": "en-US-BrandonNeural",
            "af_fable": "en-US-ChristopherNeural", "af_onyx": "en-US-EricNeural",
            "af_bella": "en-US-EmmaNeural", "af_aoede": "en-US-AvaNeural",
            "af_jessica": "en-US-MichelleNeural", "af_kore": "en-US-MonicaNeural",
            "af_nicole": "en-US-NancyNeural", "af_river": "en-US-SaraNeural",
            "af_sarah": "en-US-SaraNeural", "am_adam": "en-US-AndrewNeural",
            "am_echo": "en-US-BrianNeural", "am_eric": "en-US-EricNeural",
            "am_fenrir": "en-US-GuyNeural", "am_liam": "en-US-RyanNeural",
            "am_michael": "en-US-ChristopherNeural", "am_onyx": "en-US-DavisNeural",
            "am_puck": "en-US-TonyNeural", "am_santa": "en-US-RogerNeural",
            "bf_alice": "en-GB-SoniaNeural", "bf_emma": "en-GB-LibbyNeural",
            "bf_isabella": "en-GB-BellaNeural", "bf_lily": "en-GB-MaisieNeural",
            "bm_daniel": "en-GB-RyanNeural", "bm_fable": "en-GB-ThomasNeural",
            "bm_george": "en-GB-AlfieNeural", "bm_lewis": "en-GB-NoahNeural",
            "ff_siwis": "fr-FR-DeniseNeural",
        }
        if "-" in kokoro_voice and "Neural" in kokoro_voice:
            return kokoro_voice
        return voice_mapping.get(kokoro_voice, "en-US-AriaNeural")

    # ------------------------------------------------------------------
    # Job processing
    # ------------------------------------------------------------------
    async def process_text_to_speech(self, job_id: str, params: dict) -> dict:
        """Process text to speech conversion as a job."""
        text = params.get("text")
        voice = params.get("voice", "af_heart")
        provider = params.get("provider")
        response_format = params.get("response_format", "mp3")
        speed = params.get("speed", 1.0)
        volume_multiplier = params.get("volume_multiplier", 1.0)
        normalization_options = params.get("normalization_options")
        return_timestamps = params.get("return_timestamps", False)
        lang_code = params.get("lang_code")

        if not text:
            raise ValueError("Text parameter is required")

        created_files: list[str] = []
        audio_url = None

        try:
            audio_data, actual_provider = await self.generate_speech(
                text=text, voice=voice, provider=provider,
                response_format=response_format, speed=speed,
                volume_multiplier=volume_multiplier,
                normalization_options=normalization_options,
                return_timestamps=return_timestamps, lang_code=lang_code,
            )

            file_extension = response_format.lower()
            if file_extension == "pcm":
                file_extension = "wav"

            audio_filename = f"{uuid.uuid4()}.{file_extension}"
            audio_output_path = f"temp/output/{audio_filename}"
            os.makedirs(os.path.dirname(audio_output_path), exist_ok=True)

            if not audio_data or len(audio_data) < 100:
                raise ValueError(f"Generated audio data too small: {len(audio_data) if audio_data else 0} bytes")

            with open(audio_output_path, "wb") as f:
                f.write(audio_data)
            created_files.append(audio_output_path)

            file_size = os.path.getsize(audio_output_path)
            if file_size < 100:
                raise ValueError(f"Generated audio file too small: {file_size} bytes")

            from app.services.s3.s3 import s3_service
            s3_key = f"audio/{audio_filename}"
            audio_url = await s3_service.upload_file(audio_output_path, s3_key)
            audio_url = audio_url.split("?")[0]

            word_count = len(text.split())
            estimated_duration = max(1.0, word_count / 2.5)

            result = {
                "audio_url": audio_url, "audio_path": s3_key,
                "tts_engine": actual_provider, "voice": voice,
                "response_format": response_format, "speed": speed,
                "estimated_duration": estimated_duration, "word_count": word_count,
            }
            if actual_provider == "kokoro":
                result["volume_multiplier"] = volume_multiplier
                result["lang_code"] = lang_code
                if return_timestamps:
                    result["word_timestamps"] = []
            return result
        except Exception:
            raise
        finally:
            if audio_url:
                for path in created_files:
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception:
                            pass

    # ------------------------------------------------------------------
    # Voice / model queries
    # ------------------------------------------------------------------
    async def get_available_voices(self, provider: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get available voices for the specified provider."""
        voices: Dict[str, List[Dict[str, Any]]] = {}

        if not provider or provider.lower() == "kokoro":
            try:
                speaches_voices = await speaches_client.get_voices()
                voices["kokoro"] = speaches_voices if speaches_voices else self._fallback_kokoro_voices()
            except Exception as e:
                logger.error(f"Failed to get Kokoro voices from Speaches: {e}")
                voices["kokoro"] = self._fallback_kokoro_voices()

        if not provider or provider.lower() == "piper":
            try:
                speaches_voices = await speaches_client.get_voices()
                # Filter for piper voices if mixed
                voices["piper"] = speaches_voices if speaches_voices else []
            except Exception as e:
                logger.error(f"Failed to get Piper voices from Speaches: {e}")
                voices["piper"] = []

        if not provider or provider.lower() == "edge":
            try:
                edge_voices = await edge_tts_service.get_available_voices(language="all")
                voices["edge"] = edge_voices
            except Exception as e:
                logger.error(f"Failed to get Edge TTS voices: {e}")
                voices["edge"] = []

        return voices

    def _fallback_kokoro_voices(self) -> list[dict]:
        return [
            {"name": "af_heart", "language": "en-US", "description": "American Female - Heart", "gender": "female"},
            {"name": "af_alloy", "language": "en-US", "description": "American Female - Alloy", "gender": "female"},
            {"name": "af_bella", "language": "en-US", "description": "American Female - Bella", "gender": "female"},
            {"name": "am_michael", "language": "en-US", "description": "American Male - Michael", "gender": "male"},
            {"name": "bf_emma", "language": "en-GB", "description": "British Female - Emma", "gender": "female"},
            {"name": "bm_george", "language": "en-GB", "description": "British Male - George", "gender": "male"},
        ]

    def get_supported_providers(self) -> List[str]:
        return ["kokoro", "piper", "edge"]

    def get_supported_formats(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        formats = {
            "kokoro": ["mp3", "wav", "opus", "flac"],
            "piper": ["mp3", "wav", "opus", "flac"],
            "edge": ["mp3", "wav", "opus", "aac", "flac", "pcm"],
        }
        if provider:
            return {provider: formats.get(provider.lower(), [])}
        return formats

    def get_models(self, provider: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
        models = {
            "edge": edge_tts_service.get_supported_models(),
            "kokoro": [{"id": "kokoro", "name": "Kokoro TTS (via Speaches)"}],
            "piper": [{"id": "piper", "name": "Piper TTS (via Speaches)"}],
        }
        if provider:
            return {provider: models.get(provider.lower(), [])}
        return models

    def get_models_formatted(self, provider: Optional[str] = None) -> List[Dict[str, str]]:
        if provider and provider.lower() == "edge":
            return edge_tts_service.get_models_formatted()
        elif provider and provider.lower() == "kokoro":
            return [{"id": "kokoro"}]
        elif provider and provider.lower() == "piper":
            return [{"id": "piper"}]
        else:
            all_models: list[dict[str, str]] = []
            all_models.extend(edge_tts_service.get_models_formatted())
            all_models.append({"id": "kokoro"})
            all_models.append({"id": "piper"})
            return all_models

    def get_voices_formatted(self, provider: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
        voices: Dict[str, List[Dict[str, str]]] = {}
        if not provider or provider.lower() == "edge":
            voices["edge"] = edge_tts_service.get_voices_formatted()
        if not provider or provider.lower() == "kokoro":
            voices["kokoro"] = [
                {"id": "af_heart", "name": "American Female - Heart"},
                {"id": "af_bella", "name": "American Female - Bella"},
                {"id": "af_alloy", "name": "American Female - Alloy"},
                {"id": "am_michael", "name": "American Male - Michael"},
                {"id": "bf_emma", "name": "British Female - Emma"},
                {"id": "bm_george", "name": "British Male - George"},
            ]
        if not provider or provider.lower() == "piper":
            voices["piper"] = [
                {"id": "en_US-lessac-medium", "name": "English US - Lessac"},
                {"id": "en_US-amy-medium", "name": "English US - Amy"},
                {"id": "en_GB-alan-medium", "name": "English GB - Alan"},
                {"id": "fr_FR-siwis-medium", "name": "French - Siwis"},
            ]
        return voices


# Global service instance
tts_service = TTSService()
