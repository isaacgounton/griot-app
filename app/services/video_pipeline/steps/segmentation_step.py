"""Step 3: Script segmentation with proportional duration calculation.

Supports two modes:
- **Topic mode**: Script is split into sentences, durations distributed by word count,
  and AI generates search queries for each segment.
- **Scenes mode**: User-provided scenes are used directly with their own search terms.
  Actual TTS audio duration is distributed proportionally across scene estimates.
"""
import re
import logging
from app.services.video_pipeline.models import PipelineParams, SceneInput, Segment, SegmentationResult
from app.services.media.video_search_query_generator import video_search_query_generator

logger = logging.getLogger(__name__)

MIN_SEGMENT_DURATION = 1.5  # seconds


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def segment_script(
    script_text: str,
    audio_duration: float,
    params: PipelineParams,
) -> SegmentationResult:
    """Split script into timed segments with search queries.

    Delegates to scenes-mode or topic-mode depending on ``params.scenes``.
    """
    if params.scenes:
        return _segment_from_scenes(params.scenes, audio_duration)

    return await _segment_from_script(script_text, audio_duration, params)


# ---------------------------------------------------------------------------
# Scenes mode — user-provided pre-segmented scenes
# ---------------------------------------------------------------------------

def _segment_from_scenes(
    scenes: list[SceneInput],
    audio_duration: float,
) -> SegmentationResult:
    """Build segments from user-provided scenes.

    Uses scene texts as-is (no sentence splitting), user-provided search terms
    as queries (no AI generation), and scales user-estimated durations
    proportionally to the actual TTS audio duration.
    """
    if not scenes:
        raise ValueError("No scenes provided for segmentation")

    # Scale user-estimated durations to actual TTS audio length
    total_estimated = sum(s.duration for s in scenes) or len(scenes)
    scale = audio_duration / total_estimated

    segments: list[Segment] = []
    current_time = 0.0

    for i, scene in enumerate(scenes):
        duration = max(scene.duration * scale, MIN_SEGMENT_DURATION)

        # Use first search term as query, fall back to first words of text
        if scene.search_terms:
            query = scene.search_terms[0]
        else:
            query = ' '.join(scene.text.split()[:4]) or 'abstract background'

        semantics: dict = {}
        if len(scene.search_terms) > 1:
            semantics['visual_concept'] = ', '.join(scene.search_terms)

        segments.append(Segment(
            index=i,
            sentence=scene.text,
            word_count=len(scene.text.split()),
            duration=duration,
            start_time=current_time,
            end_time=current_time + duration,
            query=query,
            semantics=semantics,
        ))
        current_time += duration

    # Normalize so durations sum exactly to audio_duration
    _normalize_durations(segments, audio_duration)

    logger.info(
        f"Scenes mode: {len(segments)} segments, "
        f"durations sum to {sum(s.duration for s in segments):.2f}s "
        f"(target: {audio_duration:.2f}s)"
    )
    return SegmentationResult(segments=segments, total_duration=audio_duration)


# ---------------------------------------------------------------------------
# Topic mode — split script into sentences, AI-generate queries
# ---------------------------------------------------------------------------

def split_script_into_sentences(script: str) -> list[str]:
    """Split script into sentences, preserving meaningful chunks."""
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    return [s.strip() for s in sentences if s.strip()]


def distribute_durations(sentences: list[str], total_duration: float) -> list[float]:
    """Distribute total_duration proportionally by word count per sentence."""
    word_counts = [max(1, len(s.split())) for s in sentences]
    total_words = sum(word_counts)

    durations = [(wc / total_words) * total_duration for wc in word_counts]

    # Enforce minimum segment duration
    for i in range(len(durations)):
        if durations[i] < MIN_SEGMENT_DURATION:
            deficit = MIN_SEGMENT_DURATION - durations[i]
            durations[i] = MIN_SEGMENT_DURATION
            longer = [(j, durations[j]) for j in range(len(durations))
                      if j != i and durations[j] > MIN_SEGMENT_DURATION * 2]
            if longer:
                total_longer = sum(d for _, d in longer)
                for j, ld in longer:
                    durations[j] -= deficit * (ld / total_longer)

    # Final normalization to ensure exact sum
    current_sum = sum(durations)
    if current_sum > 0:
        scale = total_duration / current_sum
        durations = [d * scale for d in durations]

    return durations


async def _segment_from_script(
    script_text: str,
    audio_duration: float,
    params: PipelineParams,
) -> SegmentationResult:
    """Topic mode: split script into sentences and generate AI queries."""
    sentences = split_script_into_sentences(script_text)
    if not sentences:
        raise ValueError("Script produced no sentences after splitting")

    durations = distribute_durations(sentences, audio_duration)

    logger.info(
        f"Segmented script: {len(sentences)} sentences, "
        f"durations sum to {sum(durations):.2f}s (target: {audio_duration:.2f}s)"
    )

    # Build segments with timing
    segments: list[Segment] = []
    current_time = 0.0
    for i, (sentence, duration) in enumerate(zip(sentences, durations)):
        segments.append(Segment(
            index=i,
            sentence=sentence,
            word_count=len(sentence.split()),
            duration=duration,
            start_time=current_time,
            end_time=current_time + duration,
            query="",
        ))
        current_time += duration

    # Generate search queries using the scene-based path of the existing generator
    scenes = [{'text': seg.sentence, 'duration': seg.duration} for seg in segments]
    query_result = await video_search_query_generator.generate_video_search_queries({
        'scenes': scenes,
        'provider': params.script_provider,
    })

    queries = query_result.get('queries', [])
    for i, seg in enumerate(segments):
        if i < len(queries):
            seg.query = queries[i].get('query', seg.sentence[:30])
            seg.semantics = queries[i].get('semantics', {})
        else:
            seg.query = ' '.join(seg.sentence.split()[:4])

    return SegmentationResult(segments=segments, total_duration=audio_duration)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _normalize_durations(segments: list[Segment], target: float) -> None:
    """Scale segment durations so they sum exactly to *target*."""
    actual = sum(s.duration for s in segments)
    if actual <= 0 or abs(actual - target) < 0.01:
        return
    scale = target / actual
    current_time = 0.0
    for seg in segments:
        seg.duration *= scale
        seg.start_time = current_time
        seg.end_time = current_time + seg.duration
        current_time += seg.duration
