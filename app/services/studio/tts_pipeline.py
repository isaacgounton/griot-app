"""TTS Pipeline: Generate TTS audio per scene, then transcribe the clean TTS
audio alone with Whisper to extract accurate word timestamps.

This is the core of the audio/caption sync fix — no re-transcription of the
final mixed video.
"""
from __future__ import annotations

import os
import tempfile
import uuid

from loguru import logger

from app.services.audio.tts_service import tts_service
from app.services.speaches.stt_client import transcribe_audio
from app.services.s3.s3 import s3_service


async def generate_scene_tts(
    scene_id: str,
    script_text: str,
    tts_provider: str = "kokoro",
    voice_name: str = "af_heart",
    voice_speed: float = 1.0,
    language: str = "en",
) -> dict:
    """Generate TTS for a single scene and extract word timestamps.

    Returns:
        {
            "audio_url": str | None,
            "audio_duration": float,
            "word_timestamps": [{"word": str, "start": float, "end": float}, ...]
        }
    """
    if not script_text.strip():
        return {"audio_url": None, "audio_duration": 0.0, "word_timestamps": []}

    # Step 1: Generate TTS audio bytes (WAV for best Whisper accuracy)
    audio_bytes, actual_provider = await tts_service.generate_speech(
        text=script_text,
        voice=voice_name,
        provider=tts_provider,
        speed=voice_speed,
        lang_code=language,
        response_format="wav",
    )

    # Step 2: Save to temp file
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(tmp_fd)
    try:
        with open(tmp_path, "wb") as f:
            f.write(audio_bytes)

        # Step 3: Upload to S3
        s3_key = f"studio/tts/{scene_id}_{uuid.uuid4().hex[:8]}.wav"
        audio_url = await s3_service.upload_file(tmp_path, s3_key)

        # Step 4: Transcribe the clean TTS audio ALONE with Whisper
        # This is the key sync fix — no background music interference
        segments, info = await transcribe_audio(
            file_path=tmp_path,
            model="Systran/faster-whisper-base",
            language=language if language != "auto" else None,
            word_timestamps=True,
        )

        audio_duration = info.duration

        # Step 5: Extract word timestamps
        word_timestamps: list[dict] = []
        for segment in segments:
            if segment.words:
                for wt in segment.words:
                    word_timestamps.append({
                        "word": wt.word.strip(),
                        "start": round(wt.start, 3),
                        "end": round(wt.end, 3),
                    })
            else:
                # Fallback: distribute words evenly across segment duration
                words = segment.text.strip().split()
                if words:
                    seg_dur = segment.end - segment.start
                    word_dur = seg_dur / len(words)
                    for i, w in enumerate(words):
                        word_timestamps.append({
                            "word": w,
                            "start": round(segment.start + i * word_dur, 3),
                            "end": round(segment.start + (i + 1) * word_dur, 3),
                        })

        logger.info(
            f"Scene {scene_id}: TTS generated ({audio_duration:.2f}s, {actual_provider}), "
            f"{len(word_timestamps)} word timestamps extracted"
        )

        return {
            "audio_url": audio_url,
            "audio_duration": audio_duration,
            "word_timestamps": word_timestamps,
        }

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def generate_project_tts(
    project_id: str,
    scenes: list[dict],
    settings: dict,
) -> list[dict]:
    """Generate TTS for all scenes in a project.

    Returns list of {scene_id, audio_url, audio_duration, word_timestamps}.
    """
    results = []
    for scene in scenes:
        if not scene.get("script_text", "").strip():
            results.append({
                "scene_id": scene["id"],
                "audio_url": None,
                "audio_duration": scene.get("duration", 3.0),
                "word_timestamps": [],
            })
            continue

        result = await generate_scene_tts(
            scene_id=scene["id"],
            script_text=scene["script_text"],
            tts_provider=settings.get("tts_provider", "kokoro"),
            voice_name=settings.get("voice_name", "af_heart"),
            voice_speed=settings.get("voice_speed", 1.0),
            language=settings.get("language", "en"),
        )
        result["scene_id"] = scene["id"]
        results.append(result)

    return results
