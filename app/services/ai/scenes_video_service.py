"""
Scenes-to-video service — thin adapter over the unified video pipeline.

Converts the frontend {scenes, config} format into flat pipeline params
and delegates to ``app.services.video_pipeline.orchestrator.process()``.
"""

from typing import Any


class ScenesVideoService:
    """Service for creating videos from scene-based input."""

    async def create_video(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Create video from scenes with search terms.

        Converts the route-level ``{scenes, config}`` payload into a flat
        params dict that the unified video pipeline understands, then
        returns a result dict matching the old API shape.
        """
        from app.services.video_pipeline.orchestrator import process

        scenes = request_data.get("scenes", [])
        config = request_data.get("config", {})

        if not scenes:
            raise ValueError("At least one scene is required")

        # --- Build flat pipeline params from config -----------------------
        volume_map = {"low": 0.1, "medium": 0.3, "high": 0.5}
        music_volume = volume_map.get(config.get("musicVolume", "medium"), 0.3)

        orientation = config.get("orientation", "portrait")
        resolution = config.get("resolution", "1080x1920")
        width, height = _parse_resolution(resolution, orientation)

        music = config.get("music", "chill")

        pipeline_params: dict[str, Any] = {
            # Scenes (unified pipeline handles segmentation)
            "scenes": scenes,
            # TTS
            "voice": config.get("voice", "af_heart"),
            "tts_provider": config.get("provider", "kokoro"),
            "tts_speed": config.get("ttsSpeed", 1.0),
            "enable_voice_over": config.get("enable_voice_over", True),
            "enable_built_in_audio": config.get("enable_built_in_audio", False),
            # Dimensions
            "orientation": orientation,
            "width": width,
            "height": height,
            # Language
            "language": config.get("language", "en"),
            # Media
            "footage_provider": config.get("footageProvider", "pexels"),
            "footage_quality": config.get("footageQuality", "high"),
            "media_type": config.get("mediaType", "video"),
            "ai_video_provider": config.get("aiVideoProvider", "wavespeed"),
            "ai_image_provider": config.get("aiImageProvider", "together"),
            "ai_image_model": config.get("aiImageModel", ""),
            "ai_video_model": config.get("aiVideoModel", "veo"),
            # Image-to-video motion effects
            "effect_type": config.get("effect_type", "ken_burns"),
            "zoom_speed": config.get("zoom_speed", 10),
            "pan_direction": config.get("pan_direction", "left_to_right"),
            "ken_burns_keypoints": config.get("ken_burns_keypoints"),
            # Audio
            "background_music": music if music != "none" else None,
            "background_music_volume": music_volume,
            # Captions
            "add_captions": config.get("enableCaptions", True),
            "caption_style": config.get("captionStyle", "viral_bounce"),
            "caption_color": config.get("captionColor"),
            "highlight_color": config.get("highlightColor"),
            "caption_position": config.get("captionPosition", "bottom"),
            "font_size": config.get("fontSize"),
            "font_family": config.get("fontFamily"),
            "words_per_line": config.get("wordsPerLine"),
            "margin_v": config.get("marginV"),
            "outline_width": config.get("outlineWidth"),
            "all_caps": config.get("allCaps"),
            # Video
            "frame_rate": 30,
            "max_duration": len(scenes) * 5,
        }

        result = await process(pipeline_params)

        # Return shape expected by the route / frontend
        return {
            "final_video_url": result.get("final_video_url") or result.get("video_url"),
            "video_with_audio_url": result.get("video_with_audio_url"),
            "audio_url": result.get("audio_url"),
            "srt_url": result.get("srt_url"),
            "background_music_url": result.get("background_music_url"),
            "video_duration": result.get("video_duration", 0.0),
            "processing_time": result.get("processing_time", 0.0),
            "scenes_processed": len(scenes),
            "total_text_length": sum(len(s.get("text", "")) for s in scenes),
        }


def _parse_resolution(resolution: str, orientation: str) -> tuple[int, int]:
    """Parse a 'WxH' resolution string, falling back to orientation defaults."""
    if "x" in resolution:
        try:
            w, h = map(int, resolution.split("x"))
            return w, h
        except ValueError:
            pass
    defaults = {"portrait": (1080, 1920), "landscape": (1920, 1080), "square": (1080, 1080)}
    return defaults.get(orientation, (1080, 1920))
