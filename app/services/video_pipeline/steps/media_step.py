"""Step 4: Media acquisition using the appropriate strategy."""
import logging
from app.services.video_pipeline.models import PipelineParams, Segment, MediaResult

logger = logging.getLogger(__name__)


def _determine_strategy_key(params: PipelineParams) -> str:
    """Map footage_provider + media_type to strategy key."""
    if params.footage_provider == 'ai_generated':
        return 'ai_image' if params.media_type == 'image' else 'ai_video'
    else:
        return 'stock_image' if params.media_type == 'image' else 'stock_video'


async def acquire_media(
    segments: list[Segment],
    params: PipelineParams,
) -> MediaResult:
    """Acquire media for each segment using the appropriate strategy."""
    from app.services.video_pipeline.strategies import get_strategy

    strategy_key = _determine_strategy_key(params)
    strategy = get_strategy(strategy_key)

    logger.info(f"Using strategy: {strategy.get_strategy_name()} for {len(segments)} segments")

    # Convert Segment objects to the query dict format strategies expect
    full_script = ' '.join(s.sentence for s in segments)
    video_queries = []
    for seg in segments:
        video_queries.append({
            'query': seg.query,
            'start_time': seg.start_time,
            'end_time': seg.end_time,
            'duration': seg.duration,
            'script_text': seg.sentence,
            'full_script': full_script,
            'index': seg.index,
            'total_segments': len(segments),
            'semantics': seg.semantics,
        })

    media_results = await strategy.generate_media_segments(
        video_queries=video_queries,
        orientation=params.orientation,
        params=params.raw_params,
    )

    # Map results back to Segment objects
    valid_count = 0
    for i, media in enumerate(media_results):
        if i < len(segments) and media is not None:
            segments[i].media_url = media.get('download_url')
            segments[i].provider = media.get('provider')
            valid_count += 1

    if valid_count == 0:
        raise ValueError("No valid media generated for any segment")

    logger.info(f"Acquired media: {valid_count}/{len(segments)} segments")
    return MediaResult(
        segments=segments,
        valid_count=valid_count,
        strategy_name=strategy.get_strategy_name(),
    )
