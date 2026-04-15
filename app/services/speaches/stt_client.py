"""STT helper that delegates to the Speaches sidecar.

Provides a drop-in replacement for code that previously used
``faster_whisper.WhisperModel`` directly.  Returns segments in the
same shape so callers need minimal changes.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.services.speaches.speaches_client import speaches_client

logger = logging.getLogger(__name__)


@dataclass
class WordTiming:
    """Mirrors faster-whisper word timing."""
    word: str
    start: float
    end: float
    probability: float = 1.0


@dataclass
class Segment:
    """Mirrors faster-whisper Segment namedtuple."""
    id: int
    start: float
    end: float
    text: str
    words: list[WordTiming] = field(default_factory=list)
    avg_logprob: float = 0.0
    no_speech_prob: float = 0.0


@dataclass
class TranscriptionInfo:
    """Mirrors faster-whisper TranscriptionInfo."""
    language: str
    language_probability: float
    duration: float


async def transcribe_audio(
    file_path: str,
    model: str = "Systran/faster-whisper-base",
    language: Optional[str] = None,
    word_timestamps: bool = False,
) -> tuple[list[Segment], TranscriptionInfo]:
    """Transcribe an audio file via the Speaches sidecar.

    Returns (segments, info) with the same shapes as faster-whisper so
    existing callers can switch with minimal edits.
    """
    result = await speaches_client.transcribe(
        file_path=file_path,
        model=model,
        language=language,
        response_format="verbose_json",
        timestamp_granularities=["word", "segment"] if word_timestamps else None,
    )

    # Parse segments from the verbose_json response
    raw_segments = result.get("segments", [])

    # OpenAI-compatible APIs return word timestamps at the TOP level of
    # the response, not inside each segment.  Collect them once and
    # distribute into their parent segments below.
    top_level_words: list[dict] = result.get("words", []) if word_timestamps else []

    segments: list[Segment] = []
    for i, seg in enumerate(raw_segments):
        words: list[WordTiming] = []
        if word_timestamps:
            # Prefer per-segment words (faster-whisper native format)
            seg_words = seg.get("words", [])
            if not seg_words and top_level_words:
                # Fall back to top-level words — assign to this segment by
                # time overlap.  Use half-open interval [seg_start, seg_end)
                # so boundary words go to the later segment.  The last
                # segment uses a closed upper bound to catch the final word.
                seg_start = seg.get("start", 0.0)
                seg_end = seg.get("end", 0.0)
                is_last = i == len(raw_segments) - 1
                seg_words = [
                    w for w in top_level_words
                    if w.get("start", 0.0) >= seg_start
                    and (
                        w.get("start", 0.0) <= seg_end
                        if is_last
                        else w.get("start", 0.0) < seg_end
                    )
                ]
            for w in seg_words:
                words.append(WordTiming(
                    word=w.get("word", ""),
                    start=w.get("start", 0.0),
                    end=w.get("end", 0.0),
                    probability=w.get("probability", 1.0),
                ))
        segments.append(Segment(
            id=i,
            start=seg.get("start", 0.0),
            end=seg.get("end", 0.0),
            text=seg.get("text", ""),
            words=words,
            avg_logprob=seg.get("avg_logprob", 0.0),
            no_speech_prob=seg.get("no_speech_prob", 0.0),
        ))

    if word_timestamps and not any(s.words for s in segments) and top_level_words:
        logger.warning(
            f"Top-level words ({len(top_level_words)}) could not be assigned "
            f"to any of {len(segments)} segments — word timestamps may be missing"
        )

    # Build info
    duration = result.get("duration", 0.0)
    if not duration and segments:
        duration = segments[-1].end
    info = TranscriptionInfo(
        language=result.get("language", language or "en"),
        language_probability=result.get("language_probability", 1.0) if "language_probability" in result else 1.0,
        duration=duration,
    )

    return segments, info
