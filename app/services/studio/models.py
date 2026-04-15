"""Pydantic request/response models for Studio V2 API."""
from __future__ import annotations

from pydantic import BaseModel, Field


# ── Shared DTOs ───────────────────────────────────────────────────────────────

class WordTimestampDTO(BaseModel):
    word: str
    start: float
    end: float


# ── Project ───────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS: dict = {
    "resolution": {"width": 1080, "height": 1920},
    "frame_rate": 30,
    "tts_provider": "kokoro",
    "voice_name": "af_heart",
    "voice_speed": 1.0,
    "language": "en",
    "caption_style": "viral_bounce",
    "caption_properties": {},
    "background_music": None,
    "background_music_volume": 0.3,
    "crossfade_duration": 0.3,
    "effect_type": "ken_burns",
    "zoom_speed": 50,
    "pan_direction": "left_to_right",
    "footage_provider": "pexels",
    "ai_video_provider": "pollinations",
    "ai_image_provider": "pollinations",
    "media_type": "video",
}


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    settings: dict = Field(default_factory=lambda: DEFAULT_SETTINGS.copy())


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    settings: dict | None = None


# ── Scene ─────────────────────────────────────────────────────────────────────

class SceneCreateRequest(BaseModel):
    script_text: str = ""
    media_source_type: str | None = None
    media_search_terms: list[str] | None = None
    media_prompt: str | None = None
    media_url: str | None = None
    duration: float = 3.0
    transition_type: str = "crossfade"
    transition_duration: float = 0.3
    after_index: int | None = None  # Insert after this index (None = append)


class SceneUpdateRequest(BaseModel):
    script_text: str | None = None
    media_source_type: str | None = None
    media_search_terms: list[str] | None = None
    media_prompt: str | None = None
    media_url: str | None = None
    duration: float | None = None
    transition_type: str | None = None
    transition_duration: float | None = None


class ReorderScenesRequest(BaseModel):
    scene_ids: list[str]


# ── Generation Requests ──────────────────────────────────────────────────────

class GenerateTTSRequest(BaseModel):
    """Generate TTS + word timestamps for specified scenes (or all)."""
    scene_ids: list[str] | None = None


class GenerateMediaRequest(BaseModel):
    """Source/generate media for specified scenes (or all)."""
    scene_ids: list[str] | None = None


class GenerateAIScenesRequest(BaseModel):
    """Let AI generate scenes from a topic or script."""
    topic: str | None = None
    script: str | None = None
    scene_count: int = 5
    language: str = "en"


class ExportRequest(BaseModel):
    """Export the final video."""
    include_captions: bool = True
    include_background_music: bool = True
    caption_style_override: str | None = None
    caption_properties_override: dict | None = None


# ── Audio Track ───────────────────────────────────────────────────────────────

class AudioTrackCreateRequest(BaseModel):
    track_type: str = "background_music"
    name: str
    audio_url: str
    start_time: float = 0.0
    duration: float | None = None
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0


class AudioTrackUpdateRequest(BaseModel):
    name: str | None = None
    volume: float | None = None
    start_time: float | None = None
    duration: float | None = None
    fade_in: float | None = None
    fade_out: float | None = None


# ── Responses ─────────────────────────────────────────────────────────────────

class SceneResponse(BaseModel):
    id: str
    order_index: int
    script_text: str
    status: str
    tts_audio_url: str | None = None
    tts_audio_duration: float | None = None
    word_timestamps: list[WordTimestampDTO] | None = None
    media_source_type: str | None = None
    media_url: str | None = None
    media_search_terms: list[str] | None = None
    media_prompt: str | None = None
    media_provider: str | None = None
    start_time: float
    duration: float
    transition_type: str | None = None
    transition_duration: float
    preview_url: str | None = None
    thumbnail_url: str | None = None

    model_config = {"from_attributes": True}


class AudioTrackResponse(BaseModel):
    id: str
    track_type: str
    name: str
    audio_url: str
    start_time: float
    duration: float | None = None
    volume: float
    fade_in: float
    fade_out: float

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    settings: dict
    scenes: list[SceneResponse] = []
    audio_tracks: list[AudioTrackResponse] = []
    total_duration: float = 0.0
    final_video_url: str | None = None
    created_at: str
    updated_at: str


class ProjectListItem(BaseModel):
    id: str
    name: str
    status: str
    scene_count: int
    total_duration: float
    thumbnail_url: str | None = None
    created_at: str
    updated_at: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: str | None = None
    result: dict | None = None
    error: str | None = None
