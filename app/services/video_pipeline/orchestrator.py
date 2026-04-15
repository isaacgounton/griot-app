"""Video pipeline orchestrator — calls steps in sequence."""
import time
import logging
from app.services.video_pipeline.models import PipelineParams
from app.services.video_pipeline.params import normalize_params

logger = logging.getLogger(__name__)


async def process(raw_params: dict) -> dict:
    """Run the full video pipeline and return a result dict matching the old API shape."""
    from app.services.video_pipeline.steps.script_step import generate_script
    from app.services.video_pipeline.steps.audio_step import (
        generate_tts_audio, mix_audio_with_video, add_background_music,
    )
    from app.services.video_pipeline.steps.segmentation_step import segment_script
    from app.services.video_pipeline.steps.media_step import acquire_media
    from app.services.video_pipeline.steps.composition_step import compose_video
    from app.services.video_pipeline.steps.caption_step import render_captions

    start_time = time.time()
    params: PipelineParams = normalize_params(raw_params)

    # Step 1 — Script
    logger.info("=== Step 1: Script generation ===")
    script_result = await generate_script(params)
    logger.info(f"Script: {script_result.word_count} words, topic='{script_result.topic_used}'")

    # Step 2 — TTS audio
    logger.info("=== Step 2: TTS audio ===")
    audio_result = await generate_tts_audio(script_result.script_text, params)
    logger.info(f"Audio: {audio_result.audio_duration:.2f}s, url={audio_result.audio_url}")

    # Step 3 — Segmentation (proportional durations fix)
    logger.info("=== Step 3: Segmentation ===")
    seg_result = await segment_script(
        script_result.script_text, audio_result.audio_duration, params,
    )
    logger.info(f"Segments: {len(seg_result.segments)}, total={seg_result.total_duration:.2f}s")

    # Step 4 — Media acquisition
    logger.info("=== Step 4: Media acquisition ===")
    media_result = await acquire_media(seg_result.segments, params)
    logger.info(f"Media: {media_result.valid_count}/{len(seg_result.segments)} via {media_result.strategy_name}")

    # Step 5 — Video composition (MoviePy crossfade fix)
    logger.info("=== Step 5: Video composition ===")
    comp_result = await compose_video(
        media_result.segments, audio_result.audio_duration, params,
    )
    logger.info(f"Composed video: {comp_result.composed_video_url}")

    # Step 6 — Audio mixing
    logger.info("=== Step 6: Audio mixing ===")
    audio_mix = await mix_audio_with_video(
        comp_result.composed_video_url, audio_result, params,
    )

    # Step 6b — Background music
    audio_mix = await add_background_music(
        audio_mix, comp_result.composed_video_url,
        audio_result.audio_duration, params,
    )
    logger.info(f"Audio mixed video: {audio_mix.video_url}")

    # Step 7 — Captions
    logger.info("=== Step 7: Captions ===")
    caption_result = await render_captions(
        audio_mix.video_url, script_result.script_text, params, audio_result,
    )
    logger.info(f"Final video: {caption_result.video_url}")

    processing_time = round(time.time() - start_time, 1)
    logger.info(f"Pipeline complete in {processing_time}s")

    # Build response — includes both new field names and backward-compat aliases
    return {
        'url': caption_result.video_url,
        'video_url': caption_result.video_url,
        'final_video_url': caption_result.video_url,
        'video_with_audio_url': audio_mix.video_url,
        'srt_url': caption_result.srt_url,
        'audio_url': audio_mix.audio_url,
        'background_music_url': audio_mix.background_music_url,
        'script': script_result.script_text,
        'topic': script_result.topic_used,
        'duration': audio_result.audio_duration,
        'video_duration': audio_result.audio_duration,
        'word_count': script_result.word_count,
        'segments_count': len(seg_result.segments),
        'strategy': media_result.strategy_name,
        'resolution': f"{params.width}x{params.height}",
        'processing_time': processing_time,
    }
