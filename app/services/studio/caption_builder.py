"""Build caption data from pre-computed word timestamps.

No Whisper re-transcription needed — timestamps come from the clean TTS audio
transcription done in tts_pipeline.py.
"""
from __future__ import annotations

import os
import tempfile
import uuid

from loguru import logger


def build_caption_segments(
    scenes: list[dict],
    max_words_per_line: int = 3,
    pause_threshold: float = 0.35,
) -> list[dict]:
    """Convert per-scene word timestamps into caption segments.

    Each scene must have:
        - start_time: float (offset in the final timeline)
        - word_timestamps: [{"word": str, "start": float, "end": float}, ...]

    Word timestamps are relative to the scene's TTS audio start (0.0).
    We add scene.start_time to get absolute timeline positions.

    Chunks break on reaching *max_words_per_line* OR on a gap >=
    *pause_threshold* seconds between words, so the caption disappears
    during pauses and reappears when speech resumes.

    Returns list of segments for the ASS renderer:
        [{"start": float, "end": float, "text": str,
          "words": [{"word", "start", "end"}, ...]}]
    """
    segments: list[dict] = []

    # Warn if all scenes share start_time=0 — captions will overlap
    offsets = [s.get("start_time", 0.0) for s in scenes if s.get("word_timestamps")]
    if len(offsets) > 1 and all(o == 0.0 for o in offsets):
        logger.warning(
            f"All {len(offsets)} captioned scenes have start_time=0.0 — captions will overlap! "
            "Ensure start_time is computed before calling build_caption_segments()."
        )

    for scene in scenes:
        scene_offset = scene.get("start_time", 0.0)
        wts = scene.get("word_timestamps") or []
        if not wts:
            continue

        # Group words into lines, breaking on word count OR pauses
        current_chunk: list[dict] = []
        for i, w in enumerate(wts):
            abs_w = {
                "word": w["word"],
                "start": round(w["start"] + scene_offset, 3),
                "end": round(w["end"] + scene_offset, 3),
            }
            current_chunk.append(abs_w)

            at_max = len(current_chunk) >= max_words_per_line

            has_pause = False
            if i < len(wts) - 1:
                gap = wts[i + 1]["start"] - w["end"]
                if gap >= pause_threshold:
                    has_pause = True

            if at_max or has_pause:
                text = " ".join(cw["word"] for cw in current_chunk)
                segments.append({
                    "start": current_chunk[0]["start"],
                    "end": current_chunk[-1]["end"],
                    "text": text,
                    "words": current_chunk,
                })
                current_chunk = []

        if current_chunk:
            text = " ".join(cw["word"] for cw in current_chunk)
            segments.append({
                "start": current_chunk[0]["start"],
                "end": current_chunk[-1]["end"],
                "text": text,
                "words": current_chunk,
            })

    return segments


def generate_ass_from_segments(
    segments: list[dict],
    style_name: str = "viral_bounce",
    caption_properties: dict | None = None,
    resolution: dict | None = None,
) -> str:
    """Generate an ASS subtitle file from pre-computed caption segments.

    This uses the caption style presets from the config and applies
    word-level timing for karaoke/highlight/word_by_word effects.
    """
    from app.config import get_caption_style

    res = resolution or {"width": 1080, "height": 1920}
    style_config = get_caption_style(style_name) or {}

    # Merge with overrides
    props = {**style_config, **(caption_properties or {})}

    font_family = props.get("font_family", "Arial")
    font_size = props.get("font_size", 56)
    # Support all key variants: line_color / caption_color / color
    color = props.get("line_color") or props.get("caption_color") or props.get("color", "#FFFFFF")
    # Support all key variants: word_color / highlight_color
    highlight_color = props.get("word_color") or props.get("highlight_color", "#FFFF00")
    outline_width = props.get("outline_width", 4)
    # Support all key variants: caption_position / position
    position = props.get("caption_position") or props.get("position", "bottom_center")
    margin_v = props.get("margin_v", 80)
    bold = props.get("bold", True)
    all_caps = props.get("all_caps", False)
    animation_style = props.get("style", "karaoke")

    # Convert hex colors to ASS BGR format (&HBBGGRR&)
    def hex_to_ass(hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"&H00{b:02X}{g:02X}{r:02X}&"
        return "&H00FFFFFF&"

    # For karaoke: ASS fills from SecondaryColour → PrimaryColour,
    # so PrimaryColour must be the highlight (fill target) and
    # SecondaryColour must be the base text (starting state).
    if animation_style in ("karaoke", "bounce", "typewriter", "neon", "pop"):
        primary_color = hex_to_ass(highlight_color)
        secondary_color = hex_to_ass(color)
    else:
        primary_color = hex_to_ass(color)
        secondary_color = hex_to_ass(highlight_color)

    # Alignment based on position
    alignment = 2  # Bottom center default
    if "top" in position:
        alignment = 8
    elif "middle" in position or "center" == position:
        alignment = 5

    bold_val = -1 if bold else 0

    # ASS header
    ass = f"""[Script Info]
Title: Studio V2 Captions
ScriptType: v4.00+
PlayResX: {res['width']}
PlayResY: {res['height']}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_family},{font_size},{primary_color},{secondary_color},&H00000000&,&H80000000&,{bold_val},0,0,0,100,100,0,0,1,{outline_width},0,{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def time_to_ass(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    for seg in segments:
        start_str = time_to_ass(seg["start"])
        end_str = time_to_ass(seg["end"])

        text = seg["text"]
        if all_caps:
            text = text.upper()

        words = seg.get("words", [])

        if animation_style == "bounce" and words:
            # Bounce: scale pop + karaoke fill per word
            bounce_parts = []
            for i, w in enumerate(words):
                word_text = w["word"].upper() if all_caps else w["word"]
                if i < len(words) - 1:
                    k_dur = words[i + 1]["start"] - w["start"]
                else:
                    k_dur = w["end"] - w["start"]
                dur_cs = max(1, int(k_dur * 100))
                bounce_parts.append(
                    f"{{\\fscx130\\fscy130\\t(0,200,\\fscx100\\fscy100)\\kf{dur_cs}}}{word_text}"
                )
            text = " ".join(bounce_parts)
        elif animation_style == "typewriter" and words:
            # Typewriter: per-character karaoke fill
            typewriter_parts = []
            for i, w in enumerate(words):
                word_text = w["word"].upper() if all_caps else w["word"]
                spoken_cs = max(1, int((w["end"] - w["start"]) * 100))
                chars = list(word_text)
                char_dur = max(1, spoken_cs // len(chars)) if chars else spoken_cs
                for ch in chars:
                    typewriter_parts.append(f"{{\\kf{char_dur}}}{ch}")
                # Gap between this word's end and next word's start
                if i < len(words) - 1:
                    gap_cs = max(0, int((words[i + 1]["start"] - w["end"]) * 100))
                    typewriter_parts.append(f"{{\\kf{gap_cs}}} ")
                else:
                    typewriter_parts.append("{\\kf0} ")
            text = "".join(typewriter_parts).strip()
        elif animation_style == "fade_in":
            # Fade in: smooth opacity fade on each line
            text = f"{{\\fad(300,0)}}{text}"
        elif animation_style in ("karaoke", "neon", "pop") and words:
            # Karaoke: smooth fill per word (neon/pop are style aliases)
            karaoke_parts = []
            for i, w in enumerate(words):
                word_text = w["word"].upper() if all_caps else w["word"]
                if i < len(words) - 1:
                    k_dur = words[i + 1]["start"] - w["start"]
                else:
                    k_dur = w["end"] - w["start"]
                dur_cs = max(1, int(k_dur * 100))
                karaoke_parts.append(f"{{\\kf{dur_cs}}}{word_text}")
            text = " ".join(karaoke_parts)
        elif animation_style in ("highlight", "glow") and words:
            # Highlight: full text, current word gets highlight color
            highlight_ass = hex_to_ass(highlight_color)
            base_ass = hex_to_ass(color)
            for j, w in enumerate(words):
                parts = []
                for k, ww in enumerate(words):
                    wt = ww["word"].upper() if all_caps else ww["word"]
                    if k == j:
                        parts.append(f"{{\\c{highlight_ass}}}{wt}")
                    else:
                        parts.append(f"{{\\c{base_ass}}}{wt}")
                w_start = time_to_ass(w["start"])
                w_end = time_to_ass(w["end"])
                ass += f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{' '.join(parts)}\n"
            continue
        elif animation_style == "word_by_word" and words:
            # Word by word: one word at a time
            for w in words:
                word_text = w["word"].upper() if all_caps else w["word"]
                w_start = time_to_ass(w["start"])
                w_end = time_to_ass(w["end"])
                ass += f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{word_text}\n"
            continue

        ass += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n"

    return ass


async def render_captions_to_video(
    video_path: str,
    scenes: list[dict],
    style_name: str = "viral_bounce",
    caption_properties: dict | None = None,
    resolution: dict | None = None,
    max_words_per_line: int = 3,
) -> str:
    """Build captions from word timestamps and burn them into a video.

    Returns path to the captioned video file.
    """
    import subprocess

    segments = build_caption_segments(scenes, max_words_per_line=max_words_per_line)
    if not segments:
        logger.warning("No caption segments to render, returning original video")
        return video_path

    ass_content = generate_ass_from_segments(
        segments, style_name=style_name,
        caption_properties=caption_properties,
        resolution=resolution,
    )

    # Write ASS to temp file
    ass_fd, ass_path = tempfile.mkstemp(suffix=".ass")
    os.close(ass_fd)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # Output path
    out_fd, out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(out_fd)

    try:
        # Burn captions with FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles='{ass_path}'",
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "fast",
            out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg caption burn failed: {result.stderr[:500]}")
            # Fallback: try with ass filter instead of subtitles
            cmd_alt = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", f"ass='{ass_path}'",
                "-c:a", "copy",
                "-c:v", "libx264",
                "-preset", "fast",
                out_path,
            ]
            result = subprocess.run(cmd_alt, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"FFmpeg ass filter also failed: {result.stderr[:500]}")
                return video_path

        logger.info(f"Captions burned successfully: {len(segments)} segments")
        return out_path
    finally:
        if os.path.exists(ass_path):
            os.unlink(ass_path)
