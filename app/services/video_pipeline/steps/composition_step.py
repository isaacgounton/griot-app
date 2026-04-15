"""Step 5: Video composition with crossfade transitions.

Prefers MoviePyVideoComposer (crossfade support, cycles all segments).
Falls back to BackgroundVideoComposer (FFmpeg concat) if moviepy is unavailable.
"""
import logging
from app.services.video_pipeline.models import PipelineParams, Segment, CompositionResult
from app.utils.video.background_video_composer import BackgroundVideoComposer

logger = logging.getLogger(__name__)

# Try MoviePy composer, fall back to FFmpeg-based composer
def _create_composer() -> tuple:
    """Return (composer_instance, label). Prefers MoviePy if available."""
    try:
        from app.utils.video.moviepy_video_composer import MoviePyVideoComposer
        return MoviePyVideoComposer(), "MoviePy (crossfade)"
    except ImportError:
        return BackgroundVideoComposer(), "FFmpeg (hard cut)"


async def compose_video(
    segments: list[Segment],
    audio_duration: float,
    params: PipelineParams,
) -> CompositionResult:
    """Compose video segments into a single video with crossfade transitions."""

    # Build video_segments list in the format composers expect
    video_segments = []
    for seg in segments:
        if seg.media_url:
            video_segments.append({
                'download_url': seg.media_url,
                'start_time': seg.start_time,
                'end_time': seg.end_time,
                'duration': seg.duration,
                'query': seg.query,
                'provider': seg.provider or 'unknown',
            })

    if not video_segments:
        raise ValueError("No video segments with media URLs to compose")

    composer, label = _create_composer()

    logger.info(
        f"Composing {len(video_segments)} segments into {audio_duration:.2f}s video "
        f"({params.width}x{params.height}, composer={label})"
    )

    composed_url = await composer.compose_timed_videos(
        video_segments=video_segments,
        target_duration=audio_duration,
        output_width=params.width,
        output_height=params.height,
        frame_rate=params.frame_rate,
    )

    if not composed_url:
        raise ValueError("Video composition returned no URL")

    logger.info(f"Video composed ({label}): {composed_url}")
    return CompositionResult(composed_video_url=composed_url)
