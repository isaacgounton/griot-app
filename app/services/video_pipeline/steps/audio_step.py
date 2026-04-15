"""Step 2: TTS audio generation, audio mixing, and background music."""
import os
import uuid
import logging
import tempfile
import subprocess
import aiohttp
from app.services.video_pipeline.models import PipelineParams, AudioResult, AudioMixResult
from app.services.audio.tts_service import tts_service as text_to_speech_service
from app.services.s3.s3 import s3_service
from app.services.media.metadata import metadata_service
from app.services.video.add_audio import add_audio_service
from app.services.music import music_service
from app.services.speaches.stt_client import transcribe_audio

logger = logging.getLogger(__name__)


async def generate_tts_audio(script_text: str, params: PipelineParams) -> AudioResult:
    """Generate TTS audio and measure its duration. Returns default duration if voice-over disabled."""

    if not params.enable_voice_over:
        logger.info("Voice-over disabled, using default duration")
        return AudioResult(
            audio_url=None,
            audio_duration=float(params.max_duration),
            word_timestamps=[],
        )

    logger.info(f"Generating TTS: provider={params.tts_provider}, voice={params.voice_name}")
    audio_result = await text_to_speech_service.generate_speech(
        text=script_text,
        voice=params.voice_name,
        provider=params.tts_provider,
        speed=params.voice_speed,
        lang_code=params.language,
    )

    # TTS returns (bytes, provider_name) tuple
    tmp_path = None
    word_timestamps: list[dict] = []
    whisper_segments: list[dict] = []

    if isinstance(audio_result, tuple):
        audio_bytes, _actual_provider = audio_result
        audio_filename = f"{uuid.uuid4().hex}.mp3"
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            audio_url = await s3_service.upload_file(tmp_path, f"audio/{audio_filename}")

            # Extract word timings from the clean TTS audio before it is mixed
            # with any other soundtrack. This is the authoritative caption clock.
            try:
                segments, _ = await transcribe_audio(
                    file_path=tmp_path,
                    model="Systran/faster-whisper-base",
                    language=params.language if params.language != "auto" else None,
                    word_timestamps=True,
                )
                for segment in segments:
                    seg_words: list[dict] = []
                    if segment.words:
                        for wt in segment.words:
                            cleaned = wt.word.strip()
                            if not cleaned:
                                continue
                            w = {
                                'word': cleaned,
                                'start': round(wt.start, 3),
                                'end': round(wt.end, 3),
                            }
                            word_timestamps.append(w)
                            seg_words.append(w)
                    else:
                        words = segment.text.strip().split()
                        if not words:
                            continue
                        seg_dur = max(segment.end - segment.start, 0.0)
                        word_dur = seg_dur / len(words) if words else 0.0
                        for i, word in enumerate(words):
                            w = {
                                'word': word,
                                'start': round(segment.start + i * word_dur, 3),
                                'end': round(segment.start + (i + 1) * word_dur, 3),
                            }
                            word_timestamps.append(w)
                            seg_words.append(w)

                    if seg_words:
                        whisper_segments.append({
                            'start': round(segment.start, 3),
                            'end': round(segment.end, 3),
                            'text': segment.text.strip(),
                            'words': seg_words,
                        })

                logger.info(
                    f"Extracted {len(word_timestamps)} TTS word timestamps "
                    f"across {len(whisper_segments)} Whisper segments for captions"
                )
            except Exception as exc:
                logger.warning(f"Failed to extract TTS word timestamps, captions will fall back to video transcription: {exc}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        audio_url = audio_result.get('audio_url') if isinstance(audio_result, dict) else None

    if not audio_url:
        raise ValueError("TTS generation failed: no audio URL")

    # Get actual audio duration
    metadata = await metadata_service.get_metadata(audio_url)
    duration = metadata.get('duration', 60.0)

    logger.info(f"TTS audio: {audio_url}, duration: {duration:.2f}s")
    return AudioResult(
        audio_url=audio_url,
        audio_duration=duration,
        word_timestamps=word_timestamps,
        whisper_segments=whisper_segments,
    )


async def mix_audio_with_video(
    composed_video_url: str,
    audio_result: AudioResult,
    params: PipelineParams,
) -> AudioMixResult:
    """
    Mix audio tracks with video. Handles 4 scenarios:
    1. Voice-over ON + Built-in Audio ON  -> mix TTS + video audio
    2. Voice-over OFF + Built-in Audio ON -> keep video audio as-is
    3. Voice-over ON + Built-in Audio OFF -> replace with TTS only
    4. Voice-over OFF + Built-in Audio OFF -> silent video
    """
    vo = params.enable_voice_over and audio_result.audio_url is not None
    bia = params.enable_built_in_audio

    # Scenario 4: Silent
    if not vo and not bia:
        logger.info("Audio scenario: silent video")
        return AudioMixResult(video_url=composed_video_url, audio_url=None, background_music_url=None)

    # Scenario 2: Built-in audio only
    if not vo and bia:
        logger.info("Audio scenario: built-in audio only")
        return AudioMixResult(video_url=composed_video_url, audio_url=None, background_music_url=None)

    # Scenarios 1 and 3 both need TTS added to video
    sync_mode = 'mix' if bia else 'replace'
    video_volume = 30 if bia else 0

    logger.info(f"Audio scenario: TTS {'+ built-in' if bia else 'only'} (sync={sync_mode})")
    audio_params = {
        'video_url': composed_video_url,
        'audio_url': audio_result.audio_url,
        'sync_mode': sync_mode,
        'match_length': 'audio',
        'video_volume': video_volume,
        'audio_volume': 100,
    }
    result = await add_audio_service.process_job(
        f"pipeline_audio_{uuid.uuid4().hex[:8]}", audio_params
    )

    return AudioMixResult(
        video_url=result['url'],
        audio_url=audio_result.audio_url,
        background_music_url=None,
    )


async def add_background_music(
    audio_mix: AudioMixResult,
    composed_video_url: str,
    audio_duration: float,
    params: PipelineParams,
) -> AudioMixResult:
    """Layer background music on top of existing audio. Fails gracefully."""
    bg = params.background_music
    if not bg or bg == 'none' or bg == '' or not audio_mix.audio_url:
        return audio_mix

    logger.info(f"Adding background music: {bg}")
    try:
        background_music_url = None
        background_music_path = None
        voice_audio_path = f"/tmp/voice_audio_{uuid.uuid4()}.mp3"

        # Download voice audio
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_mix.audio_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download voice audio: {response.status}")
                    return audio_mix
                with open(voice_audio_path, 'wb') as f:
                    f.write(await response.read())

        if bg == 'generate':
            try:
                from app.services.audio.music_generation import music_generation_service

                music_params = {
                    'description': f"Instrumental background music with {params.background_music_mood} mood, suitable for video narration",
                    'duration': min(int(audio_duration), 30),
                    'model_size': 'small',
                    'output_format': 'wav',
                }
                music_result = await music_generation_service.process_music_generation(
                    f"bg_music_{uuid.uuid4().hex[:8]}", music_params
                )
                if music_result and music_result.get('audio_url'):
                    background_music_url = music_result['audio_url']
                    background_music_path = f"/tmp/bg_music_{uuid.uuid4()}.wav"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(background_music_url) as resp:
                            if resp.status == 200:
                                with open(background_music_path, 'wb') as f:
                                    f.write(await resp.read())
            except Exception as e:
                logger.warning(f"AI music generation failed: {e}, falling back to mood-based track")
                bg = params.background_music_mood  # fall through to mood selection

        if not background_music_path:
            # Select track by mood
            mood = bg if bg != 'generate' else params.background_music_mood
            tracks = await music_service.get_tracks_by_mood(mood)
            if tracks:
                selected = tracks[0]
                background_music_path = music_service.get_track_path(selected['file'])
                if background_music_path:
                    s3_key = f"music/{selected['file']}"
                    background_music_url = await s3_service.upload_file(background_music_path, s3_key)
                    logger.info(f"Using mood-based track: {selected['title']}")
            if not background_music_path:
                logger.warning(f"No tracks found for mood, skipping background music")
                return audio_mix

        if not background_music_path or not os.path.exists(background_music_path):
            return audio_mix

        # Mix with FFmpeg
        output_path = f"/tmp/audio_with_music_{uuid.uuid4()}.mp3"
        vol = params.background_music_volume
        cmd = [
            'ffmpeg', '-y',
            '-i', voice_audio_path,
            '-i', background_music_path,
            '-filter_complex',
            f'[0:a]volume=1.0[voice];[1:a]volume={vol}[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0',
            '-t', str(audio_duration),
            '-c:a', 'libmp3lame', '-b:a', '192k',
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg audio mixing failed: {result.stderr}")
            return audio_mix

        mixed_audio_url = await s3_service.upload_file(output_path, f"audio/mixed_audio_{uuid.uuid4()}.mp3")

        # Cleanup temp files
        for path in (voice_audio_path, output_path):
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass

        # Re-add mixed audio to video
        audio_params = {
            'video_url': composed_video_url,
            'audio_url': mixed_audio_url,
            'sync_mode': 'replace',
            'match_length': 'audio',
            'video_volume': 0,
            'audio_volume': 100,
        }
        audio_result = await add_audio_service.process_job(
            f"pipeline_music_audio_{uuid.uuid4().hex[:8]}", audio_params
        )

        return AudioMixResult(
            video_url=audio_result['url'],
            audio_url=mixed_audio_url,
            background_music_url=background_music_url,
        )

    except Exception as e:
        logger.error(f"Background music failed (non-fatal): {e}")
        return audio_mix
