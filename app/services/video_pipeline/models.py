"""Typed data models for the video pipeline steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional  # noqa: F401 - used in older Python compat


@dataclass
class SceneInput:
    """A user-provided scene with text, search terms, and estimated duration."""
    text: str
    search_terms: list[str] = field(default_factory=list)
    duration: float = 3.0


@dataclass
class PipelineParams:
    """Normalized parameters for the entire pipeline run."""
    # Core
    topic: str | None = None
    custom_script: str | None = None
    auto_topic: bool = False
    script_type: str = "facts"
    script_provider: str = "auto"

    # Scenes mode (pre-segmented input from scene builder)
    scenes: list[SceneInput] | None = None

    # Dimensions
    orientation: str = "landscape"
    width: int = 1280
    height: int = 720

    # TTS
    enable_voice_over: bool = True
    tts_provider: str = "kokoro"
    voice_name: str = "af_sarah"
    voice_speed: float = 1.0
    language: str = "en"

    # Media
    footage_provider: str = "pexels"
    media_type: str = "video"
    footage_quality: str = "high"
    motion_params: dict = field(default_factory=dict)

    # AI video/image specific
    ai_video_provider: str = "pollinations"
    ai_video_model: str = "veo"
    ai_image_provider: str = "together"
    ai_image_model: str = ""

    # Audio
    enable_built_in_audio: bool = False
    background_music: str | None = None
    background_music_mood: str = "upbeat"
    background_music_volume: float = 0.3

    # Captions
    add_captions: bool = False
    caption_style: str = "tiktok_viral"
    caption_properties: dict = field(default_factory=dict)

    # Video output
    max_duration: int = 60
    frame_rate: int = 30
    crossfade_duration: float = 0.3

    # Raw params pass-through for strategies
    raw_params: dict = field(default_factory=dict)


@dataclass
class ScriptResult:
    """Output of the script generation step."""
    script_text: str
    word_count: int
    topic_used: str


@dataclass
class AudioResult:
    """Output of the TTS audio generation step."""
    audio_url: str | None   # None if voice-over disabled
    audio_duration: float    # actual TTS duration, or default_duration
    word_timestamps: list[dict] = field(default_factory=list)
    # Whisper's natural phrase-level segments, each with its own words[].
    # Preserving these allows captions to break at speech pauses naturally.
    whisper_segments: list[dict] = field(default_factory=list)


@dataclass
class Segment:
    """A single video segment with timing and media info."""
    index: int
    sentence: str
    word_count: int
    duration: float
    start_time: float
    end_time: float
    query: str
    semantics: dict = field(default_factory=dict)
    # Filled after media acquisition:
    media_url: str | None = None
    provider: str | None = None


@dataclass
class SegmentationResult:
    """Output of the segmentation step."""
    segments: list[Segment]
    total_duration: float


@dataclass
class MediaResult:
    """Output of the media acquisition step."""
    segments: list[Segment]
    valid_count: int
    strategy_name: str


@dataclass
class CompositionResult:
    """Output of the video composition step."""
    composed_video_url: str


@dataclass
class AudioMixResult:
    """Output of the audio mixing step."""
    video_url: str
    audio_url: str | None
    background_music_url: str | None


@dataclass
class CaptionResult:
    """Output of the caption rendering step."""
    video_url: str
    srt_url: str | None
