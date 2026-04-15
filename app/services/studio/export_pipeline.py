"""Export Pipeline: Full video export with audio-first sync.

Pipeline:
1. Download all scene media and TTS audio
2. Compose visual track — each clip sized to its TTS audio duration
3. Mix TTS voiceover audio
4. Layer background music
5. Build captions from pre-computed word timestamps
6. Burn captions with FFmpeg
7. Upload final video to S3
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import uuid

from loguru import logger

from app.services.s3.s3 import s3_service
from app.services.studio.caption_builder import (
    build_caption_segments,
    generate_ass_from_segments,
)


# ── Image extensions for detection ────────────────────────────────────────────
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}


def _is_image_url(url: str) -> bool:
    """Check if a URL points to an image based on extension."""
    if not url:
        return False
    # Strip query params before checking extension
    path = url.split("?")[0].lower()
    return any(path.endswith(ext) for ext in _IMAGE_EXTENSIONS)


def _is_image_file(path: str) -> bool:
    """Check if a local file is an image (by probing with ffprobe)."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_type,codec_name,nb_frames,duration",
            "-of", "csv=p=0", path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout.strip().lower()
        # Image codecs: png, mjpeg, bmp, webp, etc.
        # Video codecs have duration and many frames
        if any(codec in output for codec in ("png", "mjpeg", "bmp", "webp", "gif")):
            return True
        # Also check: if nb_frames is 1 or N/A, it's likely an image
        if "1," in output or "n/a" in output:
            return True
    except Exception:
        pass
    return False


async def _download_file(url: str, suffix: str = ".mp4") -> str | None:
    """Download a file from URL to a temp path."""
    if not url:
        return None
    # Use correct suffix for images
    if _is_image_url(url):
        ext = "." + url.split("?")[0].rsplit(".", 1)[-1].lower()
        if ext in _IMAGE_EXTENSIONS:
            suffix = ext
    try:
        import aiohttp
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(tmp_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
                    return tmp_path
                else:
                    logger.warning(f"Download failed ({resp.status}): {url}")
                    os.unlink(tmp_path)
                    return None
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None


def _get_scene_duration(scene: dict) -> float:
    """Get the authoritative duration for a scene.

    Priority: tts_audio_duration > probed TTS audio > duration > 3.0
    The idea is audio-first: the clip should be as long as the narration.
    """
    tts_dur = scene.get("tts_audio_duration")
    if tts_dur and tts_dur > 0:
        return float(tts_dur)
    # Check if we have a cached probe result (set during download)
    probed = scene.get("_probed_tts_duration")
    if probed and probed > 0:
        return float(probed)
    dur = scene.get("duration")
    if dur and dur > 0:
        return float(dur)
    return 3.0


def _generate_blank_video(duration: float, resolution: dict, output_path: str) -> bool:
    """Generate a blank (black) video clip for scenes with no media."""
    w = resolution.get("width", 1080)
    h = resolution.get("height", 1920)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:d={duration}:r=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        logger.error(f"Blank video generation failed: {result.stderr[:300]}")
        return False
    return True


def _generate_silence(duration: float, output_path: str) -> bool:
    """Generate a silent audio file."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(duration),
        "-c:a", "aac",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Silence generation failed: {result.stderr[:300]}")
        return False
    return True


def _image_to_video(image_path: str, duration: float, output_path: str, resolution: dict) -> bool:
    """Create a video clip from a still image with the given duration."""
    w = resolution.get("width", 1080)
    h = resolution.get("height", 1920)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-t", str(duration),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-r", "30",
        "-an",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.error(f"Image-to-video failed: {result.stderr[:300]}")
        return False
    logger.debug(f"Image → video: {duration:.1f}s clip created")
    return True


def _trim_or_loop_video(input_path: str, target_duration: float, output_path: str, resolution: dict | None = None) -> bool:
    """Trim or loop a VIDEO file to match the target duration."""
    # Get input duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", input_path,
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
    try:
        input_duration = float(result.stdout.strip())
    except (ValueError, AttributeError):
        logger.warning(f"Could not probe duration, assuming {target_duration}s")
        input_duration = target_duration

    filters = []
    if resolution:
        w, h = resolution.get("width", 1080), resolution.get("height", 1920)
        filters.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2")

    if input_duration < target_duration:
        loop_count = int(target_duration / input_duration) + 1
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(loop_count),
            "-i", input_path,
            "-t", str(target_duration),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(target_duration),
        ]

    if filters:
        cmd += ["-vf", ",".join(filters)]

    cmd += ["-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", "-an", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.error(f"Trim/loop failed: {result.stderr[:300]}")
        return False
    logger.debug(f"Video trimmed/looped to {target_duration:.1f}s")
    return True


def _build_effect_filter(
    effect_type: str, duration: float, resolution: dict, settings: dict,
    *, is_image: bool = True,
) -> str | None:
    """Build an FFmpeg filter string for scene effects (zoom, pan, ken_burns, fade).

    For zoompan effects, ``d`` (frames per input frame) differs by source type:
    - Image: ``d = total_frames`` — generates all output frames from 1 image.
    - Video: ``d = 1`` — produces 1 output frame per input frame so zoompan
      progressively zooms/pans across the existing video frames.

    Returns a filter string or None if no effect.
    """
    if not effect_type or effect_type == "none":
        return None

    w = resolution.get("width", 1080)
    h = resolution.get("height", 1920)
    total_frames = int(duration * 30)
    if total_frames < 2:
        return None

    # d: frames per input frame.  Images need all frames from 1 source;
    # videos already have the frames — just transform each one.
    d_value = total_frames if is_image else 1
    # Video sources need framerate normalization before zoompan so that
    # total_frames = duration * 30 matches the actual frame count.
    fps_prefix = "" if is_image else "fps=30,"

    zoom_speed = settings.get("zoom_speed", 25) / 100  # 0-1 range
    max_zoom = 1.0 + zoom_speed  # e.g. 25% → zoom to 1.25x

    if effect_type == "zoom":
        # Slow zoom in from 1.0x to max_zoom
        return (
            f"{fps_prefix}scale=2*{w}:2*{h},"
            f"zoompan=z='min(1+on*{(max_zoom - 1) / total_frames:.6f},{max_zoom})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={d_value}:s={w}x{h}:fps=30"
        )

    if effect_type == "pan":
        pan_dir = settings.get("pan_direction", "left_to_right")
        # Zoom in slightly to allow room for panning
        z = 1.3
        # Max valid pan range: iw-iw/zoom (horizontal), ih-ih/zoom (vertical).
        # Pan linearly from 0 → max over total_frames.
        if pan_dir == "left_to_right":
            x_expr = f"on*(iw-iw/zoom)/{total_frames}"
            y_expr = "(ih-ih/zoom)/2"
        elif pan_dir == "right_to_left":
            x_expr = f"(iw-iw/zoom)-on*(iw-iw/zoom)/{total_frames}"
            y_expr = "(ih-ih/zoom)/2"
        elif pan_dir == "top_to_bottom":
            x_expr = "(iw-iw/zoom)/2"
            y_expr = f"on*(ih-ih/zoom)/{total_frames}"
        else:  # bottom_to_top
            x_expr = "(iw-iw/zoom)/2"
            y_expr = f"(ih-ih/zoom)-on*(ih-ih/zoom)/{total_frames}"
        return (
            f"{fps_prefix}scale=2*{w}:2*{h},"
            f"zoompan=z={z}:x='{x_expr}':y='{y_expr}':"
            f"d={d_value}:s={w}x{h}:fps=30"
        )

    if effect_type == "ken_burns":
        # Zoom + pan combined — pan the full available range while zooming
        z_expr = f"min(1+on*{(max_zoom - 1) / total_frames:.6f},{max_zoom})"
        x_expr = f"on*(iw-iw/zoom)/{total_frames}"
        y_expr = "(ih-ih/zoom)/2"
        return (
            f"{fps_prefix}scale=2*{w}:2*{h},"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={d_value}:s={w}x{h}:fps=30"
        )

    if effect_type == "fade":
        fade_dur = min(0.5, duration / 4)
        return f"fade=t=in:st=0:d={fade_dur},fade=t=out:st={duration - fade_dur}:d={fade_dur}"

    return None


def _apply_scene_effect(clip_path: str, effect_filter: str, output_path: str) -> bool:
    """Apply a visual effect filter to a scene clip (video input)."""
    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-vf", effect_filter,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-an",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        logger.warning(f"Scene effect failed (non-fatal): {result.stderr[:300]}")
        return False
    return True


def _apply_image_effect(
    image_path: str, effect_filter: str, output_path: str,
    expected_duration: float = 0,
) -> bool:
    """Apply a zoompan effect directly to a source image in a single FFmpeg pass.

    Much faster than image→video→effect because zoompan reads 1 image frame
    and generates all output frames from it, instead of processing N video frames.
    """
    logger.debug(f"Image effect: filter={effect_filter[:120]}... expected={expected_duration:.1f}s")
    cmd = [
        "ffmpeg", "-y",
        "-i", image_path,
        "-vf", effect_filter,
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-an",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.warning(f"Image effect failed: {result.stderr[:300]}")
        return False

    # Verify output duration matches expected scene duration
    if expected_duration > 0:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", output_path],
            capture_output=True, text=True, timeout=10,
        )
        try:
            actual = float(probe.stdout.strip())
            logger.info(f"Image effect output: {actual:.2f}s (expected {expected_duration:.1f}s)")
            if actual < expected_duration * 0.8:
                logger.warning(
                    f"Image effect clip too short ({actual:.1f}s vs {expected_duration:.1f}s), "
                    "falling back to video path"
                )
                return False
        except (ValueError, AttributeError):
            pass

    return True


def _apply_crossfade(clip_path: str, duration: float, fade_dur: float,
                     is_first: bool, is_last: bool, output_path: str) -> bool:
    """Apply fade-in/fade-out to a clip for crossfade transitions between scenes.

    Uses fade through black — preserves total duration and audio sync.
    """
    if fade_dur <= 0:
        return False

    fade_dur = min(fade_dur, duration / 3)  # Don't fade more than 1/3 of clip
    filters = []
    if not is_first:
        filters.append(f"fade=t=in:st=0:d={fade_dur}")
    if not is_last:
        filters.append(f"fade=t=out:st={duration - fade_dur}:d={fade_dur}")

    if not filters:
        return False

    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.warning(f"Crossfade failed (non-fatal): {result.stderr[:300]}")
        return False
    return True


def _prepare_scene_clip(
    media_path: str | None,
    media_url: str | None,
    duration: float,
    resolution: dict,
    output_path: str,
) -> bool:
    """Prepare a scene video clip from media (image or video) at the correct duration.

    Falls back to a blank clip if media processing fails.
    """
    if not media_path:
        return _generate_blank_video(duration, resolution, output_path)

    # Determine if media is an image or video
    is_image = _is_image_url(media_url or "") or _is_image_file(media_path)

    if is_image:
        ok = _image_to_video(media_path, duration, output_path, resolution)
    else:
        ok = _trim_or_loop_video(media_path, duration, output_path, resolution)

    if not ok:
        logger.warning("Media processing failed, using blank clip")
        return _generate_blank_video(duration, resolution, output_path)

    # Verify the output file actually has the expected duration
    verify_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", output_path,
    ]
    verify = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
    try:
        actual_dur = float(verify.stdout.strip())
        if actual_dur < duration * 0.5:
            logger.warning(
                f"Clip too short: {actual_dur:.1f}s vs target {duration:.1f}s, regenerating as blank"
            )
            return _generate_blank_video(duration, resolution, output_path)
    except (ValueError, AttributeError):
        pass

    return True


async def export_project(
    project_id: str,
    scenes: list[dict],
    audio_tracks: list[dict],
    settings: dict,
    include_captions: bool = True,
    include_background_music: bool = True,
    caption_style_override: str | None = None,
    caption_properties_override: dict | None = None,
) -> dict:
    """Full video export pipeline.

    Returns {"video_url": str, "duration": float, "processing_time": float}
    """
    import time
    start_time = time.time()

    resolution = settings.get("resolution", {"width": 1080, "height": 1920})
    caption_style = caption_style_override or settings.get("caption_style", "viral_bounce")
    caption_props = caption_properties_override or settings.get("caption_properties", {})
    # Check both key variants: words_per_line (frontend) and max_words_per_line (config)
    max_words_per_line = (
        caption_props.get("words_per_line")
        or caption_props.get("max_words_per_line")
        or 3
    )

    # Effects & transitions settings
    effect_type = settings.get("effect_type", "none")
    crossfade_duration = float(settings.get("crossfade_duration", 0))

    tmp_dir = tempfile.mkdtemp(prefix="studio_export_")
    temp_files: list[str] = []

    try:
        # ── Step 1a: Download TTS audio first (needed to determine duration) ─
        tts_paths: list[str | None] = []
        for i, scene in enumerate(scenes):
            if scene.get("tts_audio_url"):
                audio_path = await _download_file(scene["tts_audio_url"], suffix=".wav")
                if audio_path:
                    temp_files.append(audio_path)
                    # Probe actual TTS duration if metadata is missing
                    if not scene.get("tts_audio_duration"):
                        try:
                            probe = subprocess.run(
                                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                                capture_output=True, text=True, timeout=10,
                            )
                            probed_dur = float(probe.stdout.strip())
                            scene["_probed_tts_duration"] = probed_dur
                            logger.info(f"Scene {i}: probed TTS duration={probed_dur:.2f}s (metadata was missing)")
                        except (ValueError, AttributeError, subprocess.TimeoutExpired):
                            pass
                    tts_paths.append(audio_path)
                else:
                    tts_paths.append(None)
            else:
                if scene.get("script_text", "").strip():
                    logger.warning(
                        f"Scene {i}: has script ({len(scene['script_text'].split())} words) "
                        f"but no TTS audio — voice-over will be silent"
                    )
                tts_paths.append(None)

        # ── Step 1b: Download and prepare scene media clips ──────────────
        scene_clips: list[str] = []
        scene_audios: list[str] = []
        scene_durations: list[float] = []

        for i, scene in enumerate(scenes):
            scene_duration = _get_scene_duration(scene)
            scene_durations.append(scene_duration)
            scene_clip_path = os.path.join(tmp_dir, f"scene_{i:03d}.mp4")

            logger.info(
                f"Scene {i}: duration={scene_duration:.1f}s, "
                f"tts_dur={scene.get('tts_audio_duration')}, "
                f"probed_tts={scene.get('_probed_tts_duration')}, "
                f"media_type={scene.get('media_source_type')}, "
                f"has_media={bool(scene.get('media_url'))}"
            )

            # Download media if available
            media_path = None
            if scene.get("media_url"):
                media_path = await _download_file(scene["media_url"])
                if media_path:
                    temp_files.append(media_path)

            # Detect source type — images vs videos need different zoompan d values
            is_image = media_path and (
                _is_image_url(scene.get("media_url", "")) or _is_image_file(media_path)
            )
            effect_applied = False

            # Build zoompan filter with correct d for source type:
            #   Image: d=total_frames (generate all frames from 1 image)
            #   Video: d=1 (transform each existing frame progressively)
            img_effect = _build_effect_filter(
                effect_type, scene_duration, resolution, settings, is_image=True,
            )
            vid_effect = _build_effect_filter(
                effect_type, scene_duration, resolution, settings, is_image=False,
            )

            # Fast path: image + zoompan → single-pass (avoids double-encoding)
            if is_image and media_path and img_effect and "zoompan" in img_effect:
                if _apply_image_effect(media_path, img_effect, scene_clip_path,
                                       expected_duration=scene_duration):
                    effect_applied = True
                    logger.info(f"Scene {i}: single-pass image+'{effect_type}' effect")

            if not effect_applied:
                # Normal flow: create video clip first
                _prepare_scene_clip(
                    media_path=media_path,
                    media_url=scene.get("media_url"),
                    duration=scene_duration,
                    resolution=resolution,
                    output_path=scene_clip_path,
                )
                # Apply effect to the video clip (d=1 for video sources)
                active_filter = vid_effect if not is_image else img_effect
                if active_filter and not effect_applied:
                    effected_path = os.path.join(tmp_dir, f"scene_{i:03d}_fx.mp4")
                    if _apply_scene_effect(scene_clip_path, active_filter, effected_path):
                        scene_clip_path = effected_path
                        logger.info(f"Scene {i}: applied '{effect_type}' effect to video")

            # Apply crossfade (fade in/out between scenes)
            if crossfade_duration > 0 and len(scenes) > 1:
                faded_path = os.path.join(tmp_dir, f"scene_{i:03d}_cf.mp4")
                is_first = (i == 0)
                is_last = (i == len(scenes) - 1)
                if _apply_crossfade(scene_clip_path, scene_duration, crossfade_duration,
                                    is_first, is_last, faded_path):
                    scene_clip_path = faded_path

            scene_clips.append(scene_clip_path)

            # Use already-downloaded TTS audio
            scene_audio_path = os.path.join(tmp_dir, f"audio_{i:03d}.wav")
            tts_file = tts_paths[i]
            if tts_file:
                scene_audios.append(tts_file)
            else:
                _generate_silence(scene_duration, scene_audio_path)
                scene_audios.append(scene_audio_path)

        # ── Step 2: Concatenate video clips ────────────────────────────
        concat_video_path = os.path.join(tmp_dir, "concat_video.mp4")
        concat_list_path = os.path.join(tmp_dir, "concat_list.txt")

        with open(concat_list_path, "w") as f:
            for clip in scene_clips:
                f.write(f"file '{clip}'\n")

        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an",  # Strip any residual audio — TTS is mixed separately
            concat_video_path,
        ]
        concat_result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=300)
        if concat_result.returncode != 0:
            logger.error(f"Video concat failed: {concat_result.stderr[:500]}")

        # ── Step 3: Concatenate TTS audio ──────────────────────────────
        concat_audio_path = os.path.join(tmp_dir, "concat_audio.wav")
        audio_list_path = os.path.join(tmp_dir, "audio_list.txt")

        with open(audio_list_path, "w") as f:
            for audio in scene_audios:
                f.write(f"file '{audio}'\n")

        audio_concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", audio_list_path,
            "-c:a", "pcm_s16le",
            concat_audio_path,
        ]
        audio_result = subprocess.run(audio_concat_cmd, capture_output=True, text=True, timeout=120)
        if audio_result.returncode != 0:
            logger.error(f"Audio concat failed: {audio_result.stderr[:500]}")

        # ── Step 4: Mix video + TTS audio ──────────────────────────────
        mixed_path = os.path.join(tmp_dir, "mixed.mp4")
        mix_cmd = [
            "ffmpeg", "-y",
            "-i", concat_video_path,
            "-i", concat_audio_path,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            mixed_path,
        ]
        mix_result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=120)
        if mix_result.returncode != 0:
            logger.error(f"Audio mix failed: {mix_result.stderr[:500]}")

        current_video = mixed_path

        # ── Step 5: Add background music ───────────────────────────────
        if include_background_music and audio_tracks:
            bg_music_path = os.path.join(tmp_dir, "with_music.mp4")
            for track in audio_tracks:
                if track.get("audio_url"):
                    bg_path = await _download_file(track["audio_url"], suffix=".mp3")
                    if bg_path:
                        volume = track.get("volume", 0.3)
                        music_cmd = [
                            "ffmpeg", "-y",
                            "-i", current_video,
                            "-i", bg_path,
                            "-filter_complex",
                            f"[1:a]volume={volume}[bg];[0:a][bg]amix=inputs=2:duration=first:normalize=0[aout]",
                            "-map", "0:v", "-map", "[aout]",
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                            bg_music_path,
                        ]
                        subprocess.run(music_cmd, capture_output=True, timeout=120)
                        temp_files.append(bg_path)
                        current_video = bg_music_path
                        break  # One background track for now

        # ── Step 6: Burn captions ──────────────────────────────────────
        if include_captions:
            has_captions = any(s.get("word_timestamps") for s in scenes)
            if has_captions:
                # Recompute start_time from actual scene durations used in the
                # video timeline.  DB values may be stale or mismatched —
                # the authoritative timing is _get_scene_duration().
                cumulative = 0.0
                for idx, sc in enumerate(scenes):
                    sc["start_time"] = cumulative
                    dur = scene_durations[idx] if idx < len(scene_durations) else _get_scene_duration(sc)
                    cumulative += dur
                    logger.debug(
                        f"Caption timeline: scene {idx} start={sc['start_time']:.3f}s "
                        f"dur={dur:.3f}s words={len(sc.get('word_timestamps') or [])}"
                    )

                segments = build_caption_segments(scenes, max_words_per_line=max_words_per_line)
                logger.info(
                    f"Caption segments: {len(segments)} segments, "
                    f"style={caption_style}, words_per_line={max_words_per_line}"
                )
                if segments:
                    ass_content = generate_ass_from_segments(
                        segments,
                        style_name=caption_style,
                        caption_properties=caption_props,
                        resolution=resolution,
                    )
                    ass_path = os.path.join(tmp_dir, "captions.ass")
                    with open(ass_path, "w", encoding="utf-8") as f:
                        f.write(ass_content)

                    captioned_path = os.path.join(tmp_dir, "captioned.mp4")
                    ass_escaped = ass_path.replace("'", "'\\''").replace(":", "\\:")
                    caption_cmd = [
                        "ffmpeg", "-y",
                        "-i", current_video,
                        "-vf", f"ass={ass_escaped}",
                        "-c:a", "copy",
                        "-c:v", "libx264", "-preset", "fast",
                        captioned_path,
                    ]
                    result = subprocess.run(caption_cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        current_video = captioned_path
                    else:
                        logger.warning(f"Caption burn failed: {result.stderr[:300]}")

        # ── Step 7: Upload to S3 ───────────────────────────────────────
        s3_key = f"studio/exports/{project_id}/{uuid.uuid4().hex[:12]}.mp4"
        video_url = await s3_service.upload_file(current_video, s3_key)

        # Get final duration
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", current_video,
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        try:
            final_duration = float(probe_result.stdout.strip())
        except (ValueError, AttributeError):
            final_duration = sum(_get_scene_duration(s) for s in scenes)

        processing_time = time.time() - start_time

        logger.info(
            f"Export complete: {final_duration:.1f}s video, "
            f"{len(scenes)} scenes, {processing_time:.1f}s processing"
        )

        return {
            "video_url": video_url,
            "duration": final_duration,
            "processing_time": round(processing_time, 2),
            "scene_count": len(scenes),
        }

    finally:
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except Exception:
                pass
        try:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass
