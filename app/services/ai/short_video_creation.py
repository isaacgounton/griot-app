"""
Short video creation service — thin adapter over the unified video pipeline.

Converts MCP / frontend short-video params into flat pipeline params
and delegates to ``app.services.video_pipeline.orchestrator.process()``.
"""

from typing import Any
from app.utils.logging import get_logger

logger = get_logger()


class ShortVideoCreationService:
    """Service for creating short videos compatible with MCP and frontend."""

    async def create_short_video(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create a short video from scenes using the unified video pipeline."""
        from app.services.video_pipeline.orchestrator import process

        scenes = params.get("scenes", [])
        if not scenes:
            raise ValueError("At least one scene is required")

        logger.info(f"Creating short video with {len(scenes)} scenes")

        resolution = params.get("resolution", "1080x1920")
        width, height = _parse_resolution(resolution)

        if height > width:
            orientation = "portrait"
        elif width > height:
            orientation = "landscape"
        else:
            orientation = "square"

        total_est_duration = sum(s.get("duration", 3.0) for s in scenes)

        pipeline_params: dict[str, Any] = {
            # Scenes (unified pipeline handles segmentation)
            "scenes": scenes,
            # TTS
            "voice": params.get("voice_name", "af_bella"),
            "tts_provider": params.get("voice_provider", "kokoro"),
            "language": params.get("language", "en"),
            # Dimensions
            "orientation": orientation,
            "width": width,
            "height": height,
            # Media
            "footage_provider": params.get("footage_provider", "pexels"),
            # Audio
            "background_music": params.get("background_music"),
            "background_music_volume": 0.3,
            # Captions
            "add_captions": True,
            "caption_style": params.get("caption_style", "viral_bounce"),
            "caption_color": params.get("caption_color"),
            "caption_position": params.get("caption_position", "center"),
            # Video
            "frame_rate": params.get("fps", 30),
            "max_duration": max(20, params.get("max_duration", 60), int(total_est_duration) + 10),
        }

        result = await process(pipeline_params)

        formatted = {
            "video_url": result.get("video_url"),
            "final_video_url": result.get("final_video_url") or result.get("video_url"),
            "video_with_audio_url": result.get("video_with_audio_url"),
            "audio_url": result.get("audio_url"),
            "srt_url": result.get("srt_url"),
            "duration": result.get("video_duration", total_est_duration),
            "script_used": result.get("script"),
            "scenes_processed": len(scenes),
            "resolution": f"{width}x{height}",
            "voice_used": f"{params.get('voice_provider', 'kokoro')}:{params.get('voice_name', 'af_bella')}",
            "language": params.get("language", "en"),
            "processing_time": result.get("processing_time", 0.0),
        }

        if result.get("background_music_url"):
            formatted["background_music_url"] = result["background_music_url"]

        logger.info(f"Short video created successfully: {formatted['duration']:.1f}s")
        return formatted

    async def process_topic_to_short_video(self, topic: str, params: dict[str, Any]) -> dict[str, Any]:
        """Create a short video from a topic using AI script generation.

        Generates a script + search queries, converts them to scenes,
        then delegates to ``create_short_video``.
        """
        from app.services.text.script_generator import AIScriptGenerator
        from app.services.media.video_search_query_generator import VideoSearchQueryGenerator

        script_service = AIScriptGenerator()
        script_result = await script_service.generate_script({
            "topic": topic,
            "script_type": params.get("script_type", "facts"),
            "max_duration": params.get("max_duration", 50),
            "language": params.get("language", "english"),
            "provider": params.get("script_provider", "auto"),
        })
        generated_script = script_result["script"]
        logger.info(f"Generated script from topic '{topic}': {len(generated_script)} chars")

        search_service = VideoSearchQueryGenerator()
        search_result = await search_service.generate_video_search_queries({
            "script": generated_script,
            "segment_duration": params.get("segment_duration", 3.0),
            "provider": "auto",
            "language": params.get("language", "en"),
        })
        queries = search_result["queries"]

        # Convert queries to scenes format
        words = generated_script.split()
        words_per_query = len(words) // len(queries) if queries else len(words)
        scenes = []
        for i, query in enumerate(queries):
            start = i * words_per_query
            end = min((i + 1) * words_per_query, len(words))
            scenes.append({
                "text": " ".join(words[start:end]),
                "duration": query.get("duration", 3.0),
                "searchTerms": [query.get("query", topic)],
            })

        if not scenes:
            scenes = [{"text": generated_script, "duration": params.get("max_duration", 50), "searchTerms": [topic]}]

        result = await self.create_short_video({
            "scenes": scenes,
            "voice_provider": params.get("voice_provider", "kokoro"),
            "voice_name": params.get("voice_name", "af_bella"),
            "language": params.get("language", "en"),
            "background_music": params.get("background_music"),
            "resolution": params.get("resolution", "1080x1920"),
            "fps": params.get("fps", 30),
        })

        result.update({
            "topic_used": topic,
            "script_generated": generated_script,
            "word_count": len(words),
            "auto_generated": True,
        })
        return result


def _parse_resolution(resolution: str) -> tuple[int, int]:
    """Parse 'WxH' string, defaulting to 1080x1920."""
    if "x" in resolution:
        try:
            w, h = map(int, resolution.split("x"))
            return w, h
        except ValueError:
            pass
    return 1080, 1920


# Singleton instance
short_video_service = ShortVideoCreationService()
