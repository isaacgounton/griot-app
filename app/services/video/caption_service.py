"""
Advanced video captioning service with auto-transcription and multiple caption styles.
Based on no-code-architects-toolkit implementation with FastAPI async patterns.

Features:
- Auto-transcription using Whisper when captions not provided
- 5 caption styles: classic, karaoke, highlight, underline, word_by_word
- Text replacement for removing filler words
- Exclude time ranges to skip caption parts
- Advanced styling options
"""
import os
import uuid
import logging
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple, cast
from urllib.parse import urlparse, ParseResult

# Type stubs not available for these libraries - ignore type checking
import srt  # type: ignore

from app.services.speaches.stt_client import transcribe_audio
from app.utils.media import download_media_file
from app.services.s3 import s3_service
# Configure logging
logger = logging.getLogger(__name__)

# Temporary storage path
TEMP_PATH = "temp"

# Position to ASS alignment code mapping
POSITION_ALIGNMENT_MAP = {
    "bottom_left": 1,
    "bottom_center": 2,
    "bottom_right": 3,
    "middle_left": 4,
    "middle_center": 5,
    "middle_right": 6,
    "top_left": 7,
    "top_center": 8,
    "top_right": 9
}


def rgb_to_ass_color(rgb_color: str) -> str:
    """
    Convert RGB hex (#RRGGBB) to ASS color format (&H00BBGGRR).

    Args:
        rgb_color: RGB hex color string (e.g., "#FFFFFF")

    Returns:
        ASS format color string
    """
    # Handle None input gracefully
    if not rgb_color or not isinstance(rgb_color, str):
        return "&H00FFFFFF"  # Default to white

    # Check if it's a string (might be already in ASS format)
    rgb_color = rgb_color.lstrip('#')
    if len(rgb_color) == 6:
        try:
            r = int(rgb_color[0:2], 16)
            g = int(rgb_color[2:4], 16)
            b = int(rgb_color[4:6], 16)
            return f"&H00{b:02X}{g:02X}{r:02X}"
        except ValueError:
            pass
    return "&H00FFFFFF"  # Default to white


def timecode_to_seconds(timecode: str) -> float:
    """
    Convert timecode string (hh:mm:ss.ms) to seconds.
    
    Args:
        timecode: Timecode in format "hh:mm:ss.ms"
        
    Returns:
        Time in seconds as float
    """
    try:
        parts = timecode.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
    except (ValueError, AttributeError):
        pass
    return 0.0


def seconds_to_ass_time(seconds: float) -> str:
    """
    Convert seconds to ASS time format (h:mm:ss.cs).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        ASS format time string
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def normalize_exclude_time_ranges(exclude_ranges: List[Dict[str, str]]) -> List[Dict[str, float]]:
    """
    Normalize exclude_time_ranges from timecode strings to seconds.
    
    Args:
        exclude_ranges: List of dicts with 'start' and 'end' timecodes
        
    Returns:
        List of dicts with 'start' and 'end' as floats (seconds)
    """
    normalized: List[Dict[str, float]] = []
    for time_range in exclude_ranges:
        start = timecode_to_seconds(time_range['start'])
        end = timecode_to_seconds(time_range['end'])
        if end > start:
            normalized.append({'start': start, 'end': end})
        else:
            logger.warning(f"Invalid time range {time_range}, skipping")
    return normalized


def is_in_excluded_range(start_time: float, end_time: float, exclude_ranges: List[Dict[str, float]]) -> bool:
    """
    Check if a caption time overlaps with any excluded range.
    
    Args:
        start_time: Caption start time in seconds
        end_time: Caption end time in seconds
        exclude_ranges: List of excluded time ranges
        
    Returns:
        True if caption overlaps with an excluded range
    """
    for time_range in exclude_ranges:
        if not (end_time <= time_range['start'] or start_time >= time_range['end']):
            return True
    return False


class AdvancedCaptionService:
    """Service for advanced video captioning with auto-transcription and multiple styles."""

    def __init__(self):
        """Initialize the advanced caption service."""
        # Ensure temp directory exists
        os.makedirs(TEMP_PATH, exist_ok=True)
        os.makedirs(os.path.join(TEMP_PATH, "output"), exist_ok=True)

    async def _generate_transcription(self, video_path: str, language: str = 'auto') -> Dict[str, Any]:
        """
        Generate transcription from video audio using Speaches sidecar.

        Args:
            video_path: Path to video file
            language: Language code ('en', 'fr', 'auto')

        Returns:
            Transcription result with segments and word timestamps
        """
        try:
            logger.info(f"Transcribing video: {video_path}, language: {language}")

            segments, info = await transcribe_audio(
                file_path=video_path,
                model="Systran/faster-whisper-base",
                language=None if language == 'auto' else language,
                word_timestamps=True,
            )

            # Convert to dict structure expected by the rest of the service
            segments_list: List[Dict[str, Any]] = []
            for segment in segments:
                segment_data: Dict[str, Any] = {
                    'id': segment.id,
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'words': []
                }

                if segment.words:
                    for word in segment.words:
                        segment_data['words'].append({
                            'word': word.word,
                            'start': word.start,
                            'end': word.end
                        })

                segments_list.append(segment_data)

            result: Dict[str, Any] = {
                'segments': segments_list,
                'language': info.language
            }

            logger.info(f"Transcription complete. Found {len(result['segments'])} segments")
            return result

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            raise

    def _srt_to_transcription_result(self, srt_content: str) -> Dict[str, Any]:
        """
        Convert SRT content to transcription result format.
        
        Args:
            srt_content: SRT format subtitle content
            
        Returns:
            Transcription result dict with segments
        """
        try:
            subtitles = list(srt.parse(srt_content))  # type: ignore
            segments: List[Dict[str, Any]] = []
            
            for idx, sub in enumerate(subtitles):
                start = sub.start.total_seconds()
                end = sub.end.total_seconds()
                text = sub.content
                
                # Estimate word timings within the segment
                words_list = text.split()
                duration = end - start
                word_duration = duration / len(words_list) if words_list else duration
                
                words: List[Dict[str, Any]] = []
                current_time = start
                for word in words_list:
                    words.append({
                        'word': word,
                        'start': current_time,
                        'end': min(current_time + word_duration, end)
                    })
                    current_time += word_duration
                
                segments.append({
                    'id': idx,
                    'start': start,
                    'end': end,
                    'text': text,
                    'words': words
                })
            
            return {'segments': segments, 'language': 'unknown'}
            
        except Exception as e:
            logger.error(f"Error parsing SRT: {e}", exc_info=True)
            raise

    def _is_srt_format(self, content: str) -> bool:
        """
        Check if content is in SRT format.
        
        Args:
            content: Text content to check
            
        Returns:
            True if content appears to be SRT format
        """
        # Simple heuristic: SRT format typically starts with a number followed by timestamp
        lines = content.strip().split('\n')
        if len(lines) < 3:
            return False
            
        # Check if first line is a number
        try:
            int(lines[0].strip())
        except ValueError:
            return False
            
        # Check if second line contains timestamp pattern (HH:MM:SS,mmm --> HH:MM:SS,mmm)
        if len(lines) > 1 and '-->' in lines[1]:
            return True
            
        return False

    async def _generate_transcription_from_text(self, text: str, video_path: str) -> Dict[str, Any]:
        """
        Generate transcription-like structure from plain text, distributing words
        evenly across the actual video duration. Used as fallback when Whisper
        transcription is unavailable.

        Args:
            text: Plain text to convert
            video_path: Path to video file (for duration)

        Returns:
            Transcription result structure
        """
        try:
            # Get video duration
            import subprocess
            import json

            cmd = [
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "json", video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                info = json.loads(result.stdout)
                duration = float(info['format']['duration'])
            else:
                duration = 30.0  # Default fallback

            words = text.split()
            total_words = len(words)

            if total_words == 0:
                return {'segments': [], 'language': 'auto'}

            # Distribute words uniformly across the video duration.
            # This is a fallback — Whisper word timestamps are preferred.
            word_duration = duration / total_words

            word_timestamps: List[Dict[str, Any]] = []
            for i, word in enumerate(words):
                word_timestamps.append({
                    'word': word,
                    'start': i * word_duration,
                    'end': (i + 1) * word_duration,
                })

            # Group into segments (max 8 words or ~3s per segment, break at sentence ends)
            segments: List[Dict[str, Any]] = []
            max_words_per_segment = 8
            target_segment_duration = 3.0
            seg_words: List[Dict[str, Any]] = []

            for wd in word_timestamps:
                seg_words.append(wd)

                seg_dur = wd['end'] - seg_words[0]['start']
                at_sentence_end = wd['word'].rstrip().endswith(('.', '!', '?', ':'))

                should_break = (
                    len(seg_words) >= max_words_per_segment or
                    seg_dur >= target_segment_duration or
                    (at_sentence_end and len(seg_words) >= 3)
                )

                if should_break:
                    segments.append({
                        'start': seg_words[0]['start'],
                        'end': seg_words[-1]['end'],
                        'text': ' '.join(w['word'] for w in seg_words),
                        'words': list(seg_words),
                    })
                    seg_words = []

            if seg_words:
                segments.append({
                    'start': seg_words[0]['start'],
                    'end': seg_words[-1]['end'],
                    'text': ' '.join(w['word'] for w in seg_words),
                    'words': list(seg_words),
                })

            logger.info(f"Generated {len(segments)} segments from {total_words} words for {duration:.1f}s video")

            return {
                'segments': segments,
                'language': 'auto'
            }

        except Exception as e:
            logger.error(f"Error generating transcription from text: {e}", exc_info=True)
            return {
                'segments': [{'start': 0.0, 'end': min(30.0, duration if 'duration' in locals() else 30.0), 'text': text}],
                'language': 'auto'
            }

    def _align_text_with_transcription(self, provided_text: str, audio_transcription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Align provided text with actual audio transcription timing.

        Uses Whisper's word-level timestamps for precise sync. Each provided
        word is mapped 1-to-1 to the corresponding Whisper-detected word
        timestamp, preserving the exact speech timing from the TTS audio.

        Args:
            provided_text: The custom text provided by user
            audio_transcription: The actual transcription from Whisper (with word timestamps)

        Returns:
            Transcription result with provided text aligned to audio timing
        """
        try:
            provided_words = provided_text.split()

            if not provided_words or not audio_transcription.get('segments'):
                logger.warning("Cannot align text with transcription - no provided text or no audio segments")
                return audio_transcription

            # Collect ALL word-level timestamps from Whisper across all segments
            all_whisper_words: List[Dict[str, Any]] = []
            for segment in audio_transcription['segments']:
                if segment.get('words'):
                    all_whisper_words.extend(segment['words'])

            if not all_whisper_words:
                # No word-level timestamps from Whisper — fall back to using
                # the transcription as-is (segment-level timing only)
                logger.warning("No word-level timestamps from Whisper, using transcription as-is")
                return audio_transcription

            logger.info(
                f"Aligning {len(provided_words)} provided words with "
                f"{len(all_whisper_words)} Whisper words"
            )

            # Map provided words 1-to-1 to Whisper word timestamps.
            # Since TTS reads the exact script, word counts should be very close.
            aligned_words: List[Dict[str, Any]] = []
            n_provided = len(provided_words)
            n_whisper = len(all_whisper_words)

            if n_provided <= n_whisper:
                # Fewer or equal provided words — map each to corresponding Whisper word
                for i, word in enumerate(provided_words):
                    aligned_words.append({
                        'word': word,
                        'start': all_whisper_words[i]['start'],
                        'end': all_whisper_words[i]['end'],
                    })
            else:
                # More provided words than Whisper detected — distribute evenly
                # across the Whisper timeline
                for i, word in enumerate(provided_words):
                    # Map provided word index to Whisper word index proportionally
                    whisper_idx = min(int(i * n_whisper / n_provided), n_whisper - 1)
                    whisper_word = all_whisper_words[whisper_idx]

                    # For words mapping to the same Whisper word, subdivide its duration
                    # Find how many provided words map to this Whisper word
                    start_provided = int(whisper_idx * n_provided / n_whisper)
                    end_provided = int((whisper_idx + 1) * n_provided / n_whisper)
                    n_sharing = max(1, end_provided - start_provided)
                    local_idx = i - start_provided

                    w_start = whisper_word['start']
                    w_end = whisper_word['end']
                    sub_duration = (w_end - w_start) / n_sharing

                    aligned_words.append({
                        'word': word,
                        'start': w_start + local_idx * sub_duration,
                        'end': w_start + (local_idx + 1) * sub_duration,
                    })

            # Group aligned words into segments (chunks of ~5-8 words for readability)
            max_words_per_segment = 8
            target_segment_duration = 3.0  # seconds
            aligned_segments: List[Dict[str, Any]] = []
            seg_words: List[Dict[str, Any]] = []
            seg_id = 0

            for word_data in aligned_words:
                seg_words.append(word_data)

                seg_duration = word_data['end'] - seg_words[0]['start']
                at_sentence_end = word_data['word'].rstrip().endswith(('.', '!', '?', ':'))

                should_break = (
                    len(seg_words) >= max_words_per_segment or
                    seg_duration >= target_segment_duration or
                    (at_sentence_end and len(seg_words) >= 3)
                )

                if should_break:
                    aligned_segments.append({
                        'id': seg_id,
                        'start': seg_words[0]['start'],
                        'end': seg_words[-1]['end'],
                        'text': ' '.join(w['word'] for w in seg_words),
                        'words': list(seg_words),
                    })
                    seg_words = []
                    seg_id += 1

            # Flush remaining words
            if seg_words:
                aligned_segments.append({
                    'id': seg_id,
                    'start': seg_words[0]['start'],
                    'end': seg_words[-1]['end'],
                    'text': ' '.join(w['word'] for w in seg_words),
                    'words': list(seg_words),
                })

            logger.info(
                f"Aligned {len(provided_words)} provided words into "
                f"{len(aligned_segments)} segments using Whisper word timestamps"
            )

            return {
                'segments': aligned_segments,
                'language': audio_transcription.get('language', 'auto')
            }

        except Exception as e:
            logger.error(f"Error aligning text with transcription: {e}", exc_info=True)
            # Fallback to original transcription
            return audio_transcription

    def _apply_text_replacements(self, text: str, replace_dict: Dict[str, str]) -> str:
        """
        Apply text replacements (useful for removing filler words).
        
        Args:
            text: Original text
            replace_dict: Dictionary of find/replace pairs
            
        Returns:
            Text with replacements applied
        """
        for find, replace in replace_dict.items():
            # Case-insensitive replacement
            text = re.sub(re.escape(find), replace, text, flags=re.IGNORECASE)
        return text

    def _generate_ass_style(self, style_options: Dict[str, Any]) -> str:
        """
        Generate ASS style line from options.
        
        Args:
            style_options: Style configuration dict
            
        Returns:
            ASS format style string
        """
        # Convert color codes if provided as hex
        # Support all key variants: line_color / caption_color / color
        line_color = style_options.get('line_color') or style_options.get('caption_color') or style_options.get('color') or '#FFFFFF'
        # Support all key variants: word_color / highlight_color
        word_color = style_options.get('word_color') or style_options.get('highlight_color') or '#FFFF00'
        outline_color = style_options.get('outline_color') or '#000000'
        
        # Convert to ASS format if needed
        if line_color and isinstance(line_color, str) and line_color.startswith('#'):
            line_color = rgb_to_ass_color(line_color)
        elif not line_color:
            line_color = '&H00FFFFFF'  # White in ASS format

        if word_color and isinstance(word_color, str) and word_color.startswith('#'):
            word_color = rgb_to_ass_color(word_color)
        elif not word_color:
            word_color = '&H0000FFFF'  # Yellow in ASS format

        if outline_color and isinstance(outline_color, str) and outline_color.startswith('#'):
            outline_color = rgb_to_ass_color(outline_color)
        elif not outline_color:
            outline_color = '&H00000000'  # Black in ASS format
        
        # Build style line
        # Note: For karaoke, we use {\c} override in dialogue, so style colors are less critical
        # But we keep line_color as PrimaryColour for non-karaoke usage
        from typing import Union
        style_dict: Dict[str, Union[str, int]] = {
            'Name': 'Default',
            'Fontname': style_options.get('font_family', 'Arial'),
            'Fontsize': style_options.get('font_size', 52),
            'PrimaryColour': line_color,  # Base text color
            'SecondaryColour': word_color,  # Secondary color (may be used by some effects)
            'OutlineColour': outline_color,
            'BackColour': '&H00000000',
            'Bold': -1 if style_options.get('bold', False) else 0,
            'Italic': -1 if style_options.get('italic', False) else 0,
            'Underline': -1 if style_options.get('underline', False) else 0,
            'StrikeOut': -1 if style_options.get('strikeout', False) else 0,
            'ScaleX': 100,
            'ScaleY': 100,
            'Spacing': style_options.get('spacing', 0),
            'Angle': style_options.get('angle', 0),
            'BorderStyle': 1,
            'Outline': style_options.get('outline_width', 2),
            'Shadow': style_options.get('shadow_offset', 0),
            'Alignment': self._get_alignment(style_options),
            'MarginL': 10,
            'MarginR': 10,
            'MarginV': style_options.get('margin_v', 100),
            'Encoding': 1
        }
        
        return f"Style: {','.join(str(v) for v in style_dict.values())}"

    def _get_alignment(self, style_options: Dict[str, Any]) -> int:
        """
        Get ASS alignment code from position and alignment options.
        
        Args:
            style_options: Style configuration dict
            
        Returns:
            ASS alignment code (1-9)
        """
        # Check for position parameter first
        if 'position' in style_options:
            return POSITION_ALIGNMENT_MAP.get(style_options['position'], 2)
        
        # Fall back to numeric alignment if provided, default to bottom_center (2)
        return style_options.get('alignment', 2)

    def _get_position_coordinates(self, style_options: Dict[str, Any], video_resolution: Tuple[int, int]) -> Tuple[Optional[int], Optional[int]]:
        """
        Get x, y coordinates for positioning.
        
        Args:
            style_options: Style configuration dict
            video_resolution: (width, height) tuple
            
        Returns:
            (x, y) tuple or (None, None)
        """
        # Use explicit x, y if provided
        if 'x' in style_options and 'y' in style_options:
            return style_options['x'], style_options['y']
        
        # Otherwise return None to use default positioning
        return None, None

    def _merge_word_prefixes(self, words: List[str]) -> List[str]:
        """Merge tokens that end with an apostrophe or are stand-alone punctuation."""
        if not words:
            return []

        merged: List[str] = []
        pending_prefix: Optional[str] = None

        for word in words:
            token = word.strip()
            if not token:
                continue

            if pending_prefix:
                token = f"{pending_prefix}{token}"
                pending_prefix = None

            # If token ends with apostrophe or is just an apostrophe, defer and merge with next
            if token in {"'", "’"} or token.endswith("'") or token.endswith("’"):
                pending_prefix = token
                continue

            merged.append(token)

        if pending_prefix:
            merged.append(pending_prefix)

        return merged

    def _split_text_into_word_lines(self, text: str, max_words: Optional[int]) -> List[str]:
        """Split text into lines that respect the max_words_per_line limit."""
        if not text:
            return []

        if not max_words or max_words <= 0:
            return [text.strip()]

        words = self._merge_word_prefixes(text.split())
        if not words:
            return [text.strip()]

        lines: List[str] = []
        for i in range(0, len(words), max_words):
            lines.append(' '.join(words[i:i + max_words]))
        return lines

    def _chunk_words_for_karaoke(
        self,
        words: List[Dict[str, Any]],
        max_words: Optional[int],
        pause_threshold: float = 0.35,
    ) -> List[List[Dict[str, Any]]]:
        """Group word dictionaries into line-sized chunks for karaoke rendering.

        Chunks break on:
          1. Reaching *max_words* words, OR
          2. A gap >= *pause_threshold* seconds between the current word's end
             and the next word's start — so the caption disappears during pauses
             and reappears when speech resumes.
        """
        filtered_words: List[Dict[str, Any]] = [w for w in words if w.get('word')]

        if not filtered_words:
            return []

        if not max_words or max_words <= 0:
            max_words = len(filtered_words)  # effectively no word-count limit

        chunks: List[List[Dict[str, Any]]] = []
        current_chunk: List[Dict[str, Any]] = []

        for i, word in enumerate(filtered_words):
            current_chunk.append(word)

            at_max = len(current_chunk) >= max_words

            # Check for a pause after this word
            has_pause = False
            if i < len(filtered_words) - 1:
                gap = filtered_words[i + 1].get('start', 0) - word.get('end', 0)
                if gap >= pause_threshold:
                    has_pause = True

            if at_max or has_pause:
                chunks.append(current_chunk)
                current_chunk = []

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _generate_ass_header(self, style_line: str, video_resolution: Tuple[int, int]) -> str:
        """
        Generate ASS file header with style.
        
        Args:
            style_line: The style line to include
            video_resolution: (width, height) of video
            
        Returns:
            Complete ASS header string
        """
        width, height = video_resolution
        return f"""[Script Info]
Title: Video Captions
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def _process_words_for_style(self, words: List[Dict[str, Any]], replace_dict: Dict[str, str],
                                  all_caps: bool) -> List[Dict[str, Any]]:
        """Process raw word data: apply replacements, merge apostrophes, apply caps.

        Returns list of processed word dicts with 'word', 'start', 'end' keys.
        Shared by karaoke, bounce, and typewriter handlers.
        """
        processed_words: List[Dict[str, Any]] = []
        pending_prefix: Optional[Dict[str, Any]] = None
        for w_info in words:
            raw_word = w_info.get('word', '').strip()
            if not raw_word:
                continue
            cleaned_word = self._apply_text_replacements(raw_word, replace_dict).strip()
            if not cleaned_word:
                continue
            if pending_prefix:
                cleaned_word = f"{pending_prefix['word']}{cleaned_word}"
                start_time = pending_prefix['start']
                pending_prefix = None
            else:
                start_time = w_info['start']
            if cleaned_word in {"'", "\u2019"} or cleaned_word.endswith("'") or cleaned_word.endswith("\u2019"):
                pending_prefix = {'word': cleaned_word, 'start': start_time, 'end': w_info['end']}
                continue
            if all_caps:
                cleaned_word = cleaned_word.upper()
            processed_words.append({
                'word': cleaned_word,
                'start': start_time,
                'end': w_info['end']
            })
        if pending_prefix:
            processed_words.append({
                'word': pending_prefix['word'],
                'start': pending_prefix['start'],
                'end': pending_prefix['end']
            })
        return processed_words

    def _handle_classic_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any],
                               replace_dict: Dict[str, str]) -> List[str]:
        """
        Generate classic style captions (all text shown at once).

        Args:
            transcription: Transcription result
            style_options: Style options
            replace_dict: Text replacements

        Returns:
            List of ASS dialogue lines
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)
        max_words = style_options.get('max_words_per_line')
        if max_words is not None:
            try:
                max_words = int(max_words)
            except (TypeError, ValueError):
                logger.warning(f"Invalid max_words_per_line value: {max_words}, ignoring")
                max_words = None
        if max_words is not None and max_words <= 0:
            max_words = None  # Treat 0 or negative as no limit

        for segment in transcription['segments']:
            text = segment['text'].strip()

            # Apply text replacements
            text = self._apply_text_replacements(text, replace_dict)

            # Apply all caps if requested
            if all_caps:
                text = text.upper()

            # Handle max_words_per_line - show chunks sequentially
            if max_words is not None and max_words > 0 and len(text.split()) > max_words:
                # Split into chunks and show each chunk sequentially
                lines = self._split_text_into_word_lines(text, max_words)

                # Calculate timing for each chunk
                segment_duration = segment['end'] - segment['start']
                chunk_duration = segment_duration / len(lines)

                for i, line in enumerate(lines):
                    if not line.strip():
                        continue

                    chunk_start = segment['start'] + (i * chunk_duration)
                    chunk_end = chunk_start + chunk_duration

                    start_time = seconds_to_ass_time(chunk_start)
                    end_time = seconds_to_ass_time(chunk_end)

                    dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line.strip()}")
            else:
                # No max_words - show entire segment at once
                start_time = seconds_to_ass_time(segment['start'])
                end_time = seconds_to_ass_time(segment['end'])
                dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")

        return dialogues

    def _handle_karaoke_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any], 
                               replace_dict: Dict[str, str]) -> List[str]:
        """
        Generate karaoke style captions (words highlight sequentially using \\k tags).
        Uses the same approach as no-code-architects-toolkit.
        
        Args:
            transcription: Transcription result with word timestamps
            style_options: Style options
            replace_dict: Text replacements
            
        Returns:
            List of ASS dialogue lines with karaoke effects
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)
        # Get max_words_per_line, default to None (no limit)
        # Ensure it's an integer if provided
        max_words = style_options.get('max_words_per_line')
        if max_words is not None:
            try:
                max_words = int(max_words)
                if max_words <= 0:
                    max_words = None  # Treat 0 or negative as no limit
            except (TypeError, ValueError):
                logger.warning(f"Invalid max_words_per_line value: {max_words}, ignoring")
                max_words = None
        
        # Get colors - support all key variants
        word_color = style_options.get('word_color') or style_options.get('highlight_color') or '#FFFF00'
        line_color = style_options.get('line_color') or style_options.get('caption_color') or style_options.get('color') or '#FFFFFF'

        # Convert to ASS format
        if isinstance(word_color, str) and word_color.startswith('#'):
            word_color_ass = rgb_to_ass_color(word_color)
        else:
            word_color_ass = word_color
        if isinstance(line_color, str) and line_color.startswith('#'):
            line_color_ass = rgb_to_ass_color(line_color)
        else:
            line_color_ass = line_color

        logger.info(f"Karaoke style settings: max_words_per_line={max_words}, all_caps={all_caps}, word_color={word_color_ass}, line_color={line_color_ass}")
        logger.info(f"Full style_options: {style_options}")
        
        for segment in transcription['segments']:
            if not segment.get('words'):
                # Fallback to classic if no word timestamps
                logger.warning(f"Segment has no word timestamps, falling back to classic style")
                text = segment['text'].strip()
                text = self._apply_text_replacements(text, replace_dict)
                if all_caps:
                    text = text.upper()
                start_time = seconds_to_ass_time(segment['start'])
                end_time = seconds_to_ass_time(segment['end'])
                dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
                continue
            
            # Build karaoke text with word-by-word highlighting
            processed_words = self._process_words_for_style(segment['words'], replace_dict, all_caps)
            if not processed_words:
                logger.warning("No usable words after processing replacements; skipping segment")
                continue

            word_chunks = self._chunk_words_for_karaoke(processed_words, max_words)

            # Show each chunk sequentially instead of all at once
            # Small timing offset to reduce "jumpy" captions appearing before audio
            CAPTION_TIMING_OFFSET = 0.05  # 50ms delay for better sync

            for chunk in word_chunks:
                chunk_parts: List[str] = []
                for i, entry in enumerate(chunk):
                    # Apply offset to start times for better audio sync
                    adjusted_start = entry['start'] + CAPTION_TIMING_OFFSET

                    if i < len(chunk) - 1:
                        # Include the gap to the next word so \k stays in sync
                        k_duration = chunk[i + 1]['start'] - adjusted_start
                    else:
                        k_duration = entry['end'] - adjusted_start
                    duration_cs = max(1, int(round(max(k_duration, 0.01) * 100)))
                    chunk_parts.append(f"{{\\k{duration_cs}}}{entry['word']} ")

                dialogue_text = ''.join(chunk_parts).strip()
                start_time = seconds_to_ass_time(chunk[0]['start'] + CAPTION_TIMING_OFFSET)
                end_time = seconds_to_ass_time(chunk[-1]['end'])

                final_dialogue = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\c{word_color_ass}\\2c{line_color_ass}}}{dialogue_text}"
                logger.debug(f"Karaoke dialogue: {final_dialogue[:300]}...")
                dialogues.append(final_dialogue)
        
        return dialogues

    def _handle_bounce_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any],
                              replace_dict: Dict[str, str]) -> List[str]:
        """Generate bounce style captions (words pop in with scale animation + karaoke fill).

        Each word starts at 130% scale, shrinks to 100% over 200ms via \\t() transform,
        while \\kf karaoke fill sweeps across it.
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)
        max_words = style_options.get('max_words_per_line')
        if max_words is not None:
            try:
                max_words = int(max_words)
                if max_words <= 0:
                    max_words = None
            except (TypeError, ValueError):
                max_words = None

        word_color = style_options.get('word_color') or style_options.get('highlight_color') or '#FFFF00'
        line_color = style_options.get('line_color') or style_options.get('caption_color') or style_options.get('color') or '#FFFFFF'
        word_color_ass = rgb_to_ass_color(word_color) if isinstance(word_color, str) and word_color.startswith('#') else word_color
        line_color_ass = rgb_to_ass_color(line_color) if isinstance(line_color, str) and line_color.startswith('#') else line_color

        for segment in transcription['segments']:
            if not segment.get('words'):
                text = segment['text'].strip()
                text = self._apply_text_replacements(text, replace_dict)
                if all_caps:
                    text = text.upper()
                start_time = seconds_to_ass_time(segment['start'])
                end_time = seconds_to_ass_time(segment['end'])
                dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
                continue

            processed_words = self._process_words_for_style(segment['words'], replace_dict, all_caps)
            if not processed_words:
                continue

            word_chunks = self._chunk_words_for_karaoke(processed_words, max_words)

            for chunk in word_chunks:
                chunk_parts: List[str] = []
                for i, entry in enumerate(chunk):
                    # Apply offset to start times for better audio sync
                    adjusted_start = entry['start'] + CAPTION_TIMING_OFFSET

                    if i < len(chunk) - 1:
                        k_duration = chunk[i + 1]['start'] - adjusted_start
                    else:
                        k_duration = entry['end'] - adjusted_start
                    duration_cs = max(1, int(round(max(k_duration, 0.01) * 100)))
                    # Scale up then animate to normal + karaoke fill
                    chunk_parts.append(
                        f"{{\\fscx130\\fscy130\\t(0,200,\\fscx100\\fscy100)\\kf{duration_cs}}}{entry['word']} "
                    )

                dialogue_text = ''.join(chunk_parts).strip()
                start_time = seconds_to_ass_time(chunk[0]['start'] + CAPTION_TIMING_OFFSET)
                end_time = seconds_to_ass_time(chunk[-1]['end'])
                final_dialogue = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\c{word_color_ass}\\2c{line_color_ass}}}{dialogue_text}"
                dialogues.append(final_dialogue)

        return dialogues

    def _handle_typewriter_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any],
                                  replace_dict: Dict[str, str]) -> List[str]:
        """Generate typewriter style captions (character-by-character reveal).

        Each word's characters get individual \\kf tags so text is revealed
        character-by-character rather than word-by-word.
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)
        max_words = style_options.get('max_words_per_line')
        if max_words is not None:
            try:
                max_words = int(max_words)
                if max_words <= 0:
                    max_words = None
            except (TypeError, ValueError):
                max_words = None

        word_color = style_options.get('word_color') or style_options.get('highlight_color') or '#FFFF00'
        line_color = style_options.get('line_color') or style_options.get('caption_color') or style_options.get('color') or '#FFFFFF'
        word_color_ass = rgb_to_ass_color(word_color) if isinstance(word_color, str) and word_color.startswith('#') else word_color
        line_color_ass = rgb_to_ass_color(line_color) if isinstance(line_color, str) and line_color.startswith('#') else line_color

        for segment in transcription['segments']:
            if not segment.get('words'):
                text = segment['text'].strip()
                text = self._apply_text_replacements(text, replace_dict)
                if all_caps:
                    text = text.upper()
                start_time = seconds_to_ass_time(segment['start'])
                end_time = seconds_to_ass_time(segment['end'])
                dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
                continue

            processed_words = self._process_words_for_style(segment['words'], replace_dict, all_caps)
            if not processed_words:
                continue

            word_chunks = self._chunk_words_for_karaoke(processed_words, max_words)

            for chunk in word_chunks:
                typewriter_parts: List[str] = []
                for entry in chunk:
                    word_text = entry['word']
                    word_duration_cs = max(1, int(round(max(entry['end'] - entry['start'], 0.01) * 100)))
                    chars = list(word_text)
                    if not chars:
                        continue
                    char_cs = max(1, word_duration_cs // len(chars))
                    for ch in chars:
                        typewriter_parts.append(f"{{\\kf{char_cs}}}{ch}")
                    # Space between words (instant)
                    typewriter_parts.append("{\\kf0} ")

                dialogue_text = ''.join(typewriter_parts).strip()
                start_time = seconds_to_ass_time(chunk[0]['start'])
                end_time = seconds_to_ass_time(chunk[-1]['end'])
                final_dialogue = f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\c{word_color_ass}\\2c{line_color_ass}}}{dialogue_text}"
                dialogues.append(final_dialogue)

        return dialogues

    def _handle_fade_in_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any],
                               replace_dict: Dict[str, str]) -> List[str]:
        """Generate fade-in style captions (each line fades in smoothly).

        Uses \\fad(300,0) on each dialogue line for a 300ms fade from transparent to opaque.
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)
        max_words = style_options.get('max_words_per_line')
        if max_words is not None:
            try:
                max_words = int(max_words)
                if max_words <= 0:
                    max_words = None
            except (TypeError, ValueError):
                max_words = None

        fade_in_ms = 300

        for segment in transcription['segments']:
            text = segment['text'].strip()
            text = self._apply_text_replacements(text, replace_dict)
            if all_caps:
                text = text.upper()

            if max_words and max_words > 0 and len(text.split()) > max_words:
                lines = self._split_text_into_word_lines(text, max_words)
                segment_duration = segment['end'] - segment['start']
                chunk_duration = segment_duration / len(lines)

                for i, line in enumerate(lines):
                    if not line.strip():
                        continue
                    chunk_start = segment['start'] + (i * chunk_duration)
                    chunk_end = chunk_start + chunk_duration
                    start_time = seconds_to_ass_time(chunk_start)
                    end_time = seconds_to_ass_time(chunk_end)
                    dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\fad({fade_in_ms},0)}}{line.strip()}")
            else:
                start_time = seconds_to_ass_time(segment['start'])
                end_time = seconds_to_ass_time(segment['end'])
                dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\fad({fade_in_ms},0)}}{text}")

        return dialogues

    def _handle_highlight_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any],
                                 replace_dict: Dict[str, str]) -> List[str]:
        """
        Generate highlight style captions (full text shown, current word highlighted with color).

        Args:
            transcription: Transcription result with word timestamps
            style_options: Style options
            replace_dict: Text replacements

        Returns:
            List of ASS dialogue lines with color highlighting
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)

        # Get max_words_per_line for highlight style
        max_words = style_options.get('max_words_per_line')
        if max_words is not None:
            try:
                max_words = int(max_words)
                if max_words <= 0:
                    max_words = None  # Treat 0 or negative as no limit
            except (TypeError, ValueError):
                logger.warning(f"Invalid max_words_per_line value: {max_words}, ignoring")
                max_words = None

        # Get colors - support all key variants
        line_color = style_options.get('line_color') or style_options.get('caption_color') or style_options.get('color') or '#FFFFFF'
        word_color = style_options.get('word_color') or style_options.get('highlight_color') or '#FFFF00'

        # Convert to ASS format
        if line_color and isinstance(line_color, str) and line_color.startswith('#'):
            line_color = rgb_to_ass_color(line_color)
        if word_color and isinstance(word_color, str) and word_color.startswith('#'):
            word_color = rgb_to_ass_color(word_color)

        for segment in transcription['segments']:
            if not segment.get('words'):
                # Fallback to classic
                text = segment['text'].strip()
                text = self._apply_text_replacements(text, replace_dict)
                if all_caps:
                    text = text.upper()

                # Handle max_words_per_line if specified - show chunks sequentially
                if max_words is not None and max_words > 0 and len(text.split()) > max_words:
                    lines = self._split_text_into_word_lines(text, max_words)

                    # Calculate timing for each chunk
                    segment_duration = segment['end'] - segment['start']
                    chunk_duration = segment_duration / len(lines)

                    for i, line in enumerate(lines):
                        if not line.strip():
                            continue

                        chunk_start = segment['start'] + (i * chunk_duration)
                        chunk_end = chunk_start + chunk_duration

                        start_time = seconds_to_ass_time(chunk_start)
                        end_time = seconds_to_ass_time(chunk_end)

                        dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line.strip()}")
                else:
                    start_time = seconds_to_ass_time(segment['start'])
                    end_time = seconds_to_ass_time(segment['end'])
                    dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
                continue

            # Process words with max_words_per_line consideration
            words = segment['words']
            all_words_text = [w['word'].strip() for w in words]

            # Apply replacements and caps to all words
            all_words_text = [self._apply_text_replacements(w, replace_dict) for w in all_words_text]
            if all_caps:
                all_words_text = [w.upper() for w in all_words_text]

            # If max_words is specified, chunk words into lines
            if max_words and max_words > 0:
                # Create word chunks respecting max_words_per_line
                word_chunks = self._chunk_words_for_karaoke([
                    {'word': word, 'start': w['start'], 'end': w['end']}
                    for word, w in zip(all_words_text, words)
                ], max_words)

                for chunk in word_chunks:
                    # For each chunk, highlight each word within that chunk
                    chunk_words = [item['word'] for item in chunk]
                    for idx, entry in enumerate(chunk):
                        # Build line with current word highlighted
                        line_parts: List[str] = []
                        for i, word in enumerate(chunk_words):
                            if i == idx:
                                # Highlight current word
                                line_parts.append(f"{{\\c{word_color}}}{word}{{\\c{line_color}}}")
                            else:
                                line_parts.append(word)

                        line_text = ' '.join(line_parts)
                        # Each word gets its own time window (when it's the highlighted one)
                        start_time = seconds_to_ass_time(entry['start'])
                        end_time = seconds_to_ass_time(entry['end'])
                        dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text}")
            else:
                # Original behavior - each word gets its own dialogue line
                for idx, word_data in enumerate(words):
                    # Build line with current word highlighted
                    line_parts: List[str] = []
                    for i, word in enumerate(all_words_text):
                        if i == idx:
                            # Highlight current word
                            line_parts.append(f"{{\\c{word_color}}}{word}{{\\c{line_color}}}")
                        else:
                            line_parts.append(word)

                    line_text = ' '.join(line_parts)
                    start_time = seconds_to_ass_time(word_data['start'])
                    end_time = seconds_to_ass_time(word_data['end'])
                    dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text}")

        return dialogues

    def _handle_underline_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any],
                                 replace_dict: Dict[str, str]) -> List[str]:
        """
        Generate underline style captions (full text shown, current word underlined).

        Args:
            transcription: Transcription result with word timestamps
            style_options: Style options
            replace_dict: Text replacements

        Returns:
            List of ASS dialogue lines with underline effect
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)
        max_words = style_options.get('max_words_per_line')
        if max_words is not None:
            try:
                max_words = int(max_words)
            except (TypeError, ValueError):
                logger.warning(f"Invalid max_words_per_line value: {max_words}, ignoring")
                max_words = None
        if max_words is not None and max_words <= 0:
            max_words = None  # Treat 0 or negative as no limit

        for segment in transcription['segments']:
            if not segment.get('words'):
                # Fallback to classic
                text = segment['text'].strip()
                text = self._apply_text_replacements(text, replace_dict)
                if all_caps:
                    text = text.upper()

                # Handle max_words_per_line if specified
                if max_words is not None and max_words > 0 and len(text.split()) > max_words:
                    lines = self._split_text_into_word_lines(text, max_words)

                    # Calculate timing for each chunk
                    segment_duration = segment['end'] - segment['start']
                    chunk_duration = segment_duration / len(lines)

                    for i, line in enumerate(lines):
                        if not line.strip():
                            continue

                        chunk_start = segment['start'] + (i * chunk_duration)
                        chunk_end = chunk_start + chunk_duration

                        start_time = seconds_to_ass_time(chunk_start)
                        end_time = seconds_to_ass_time(chunk_end)

                        dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line.strip()}")
                else:
                    start_time = seconds_to_ass_time(segment['start'])
                    end_time = seconds_to_ass_time(segment['end'])
                    dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
                continue

            # Process words with max_words_per_line consideration
            words = segment['words']
            all_words_text = [w['word'].strip() for w in words]

            # Apply replacements and caps
            all_words_text = [self._apply_text_replacements(w, replace_dict) for w in all_words_text]
            if all_caps:
                all_words_text = [w.upper() for w in all_words_text]

            # If max_words is specified, chunk words into lines
            if max_words and max_words > 0:
                # Create word chunks respecting max_words_per_line
                word_chunks = self._chunk_words_for_karaoke([
                    {'word': word, 'start': w['start'], 'end': w['end']}
                    for word, w in zip(all_words_text, words)
                ], max_words)

                for chunk in word_chunks:
                    # For each chunk, underline each word within that chunk
                    chunk_words = [item['word'] for item in chunk]
                    for idx, entry in enumerate(chunk):
                        # Build line with current word underlined
                        line_parts: List[str] = []
                        for i, word in enumerate(chunk_words):
                            if i == idx:
                                # Underline current word
                                line_parts.append(f"{{\\u1}}{word}{{\\u0}}")
                            else:
                                line_parts.append(word)

                        line_text = ' '.join(line_parts)
                        start_time = seconds_to_ass_time(chunk[0]['start'])
                        end_time = seconds_to_ass_time(chunk[-1]['end'])
                        dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text}")
            else:
                # Original behavior - each word gets its own dialogue line
                for idx, word_data in enumerate(words):
                    # Build line with current word underlined
                    line_parts: List[str] = []
                    for i, word in enumerate(all_words_text):
                        if i == idx:
                            # Underline current word
                            line_parts.append(f"{{\\u1}}{word}{{\\u0}}")
                        else:
                            line_parts.append(word)

                    line_text = ' '.join(line_parts)
                    start_time = seconds_to_ass_time(word_data['start'])
                    end_time = seconds_to_ass_time(word_data['end'])
                    dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text}")

        return dialogues

    def _handle_word_by_word_style(self, transcription: Dict[str, Any], style_options: Dict[str, Any], 
                                     replace_dict: Dict[str, str]) -> List[str]:
        """
        Generate word-by-word style captions (show one word at a time).
        
        Args:
            transcription: Transcription result with word timestamps
            style_options: Style options
            replace_dict: Text replacements
            
        Returns:
            List of ASS dialogue lines showing one word at a time
        """
        dialogues: List[str] = []
        all_caps = style_options.get('all_caps', False)
        
        for segment in transcription['segments']:
            if not segment.get('words'):
                # Fallback to classic
                text = segment['text'].strip()
                text = self._apply_text_replacements(text, replace_dict)
                if all_caps:
                    text = text.upper()
                start_time = seconds_to_ass_time(segment['start'])
                end_time = seconds_to_ass_time(segment['end'])
                dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
                continue
            
            # Show each word individually
            for word_data in segment['words']:
                word = word_data['word'].strip()
                word = self._apply_text_replacements(word, replace_dict)
                if all_caps:
                    word = word.upper()
                
                start_time = seconds_to_ass_time(word_data['start'])
                end_time = seconds_to_ass_time(word_data['end'])
                dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{word}")
        
        return dialogues

    def _process_subtitle_events(self, transcription: Dict[str, Any], style_type: str, 
                                  style_options: Dict[str, Any], replace_dict: Dict[str, str],
                                  video_resolution: Tuple[int, int]) -> str:
        """
        Process transcription into ASS subtitle events based on style.
        
        Args:
            transcription: Transcription result
            style_type: Style type (classic, karaoke, highlight, underline, word_by_word)
            style_options: Style configuration
            replace_dict: Text replacements
            video_resolution: Video dimensions
            
        Returns:
            Complete ASS subtitle content
        """
        try:
            # Log style options for debugging
            logger.info(f"Processing subtitles with style '{style_type}' and options: {style_options}")
            
            # Generate style line
            style_line = self._generate_ass_style(style_options)
            logger.debug(f"Generated ASS style line: {style_line}")
            
            # Generate header
            ass_header = self._generate_ass_header(style_line, video_resolution)
            
            # Generate dialogue lines based on style
            if style_type == 'bounce':
                dialogues = self._handle_bounce_style(transcription, style_options, replace_dict)
            elif style_type == 'typewriter':
                dialogues = self._handle_typewriter_style(transcription, style_options, replace_dict)
            elif style_type == 'fade_in':
                dialogues = self._handle_fade_in_style(transcription, style_options, replace_dict)
            elif style_type in ('karaoke', 'neon', 'pop'):
                dialogues = self._handle_karaoke_style(transcription, style_options, replace_dict)
            elif style_type in ('highlight', 'glow'):
                dialogues = self._handle_highlight_style(transcription, style_options, replace_dict)
            elif style_type == 'underline':
                dialogues = self._handle_underline_style(transcription, style_options, replace_dict)
            elif style_type == 'word_by_word':
                dialogues = self._handle_word_by_word_style(transcription, style_options, replace_dict)
            else:  # classic or unknown
                dialogues = self._handle_classic_style(transcription, style_options, replace_dict)
            
            logger.info(f"Generated {len(dialogues)} dialogue lines for style '{style_type}'")
            
            # Combine header and dialogues
            ass_content = ass_header + '\n'.join(dialogues)
            
            return ass_content
            
        except Exception as e:
            logger.error(f"Error processing subtitle events: {e}", exc_info=True)
            raise

    def _filter_subtitle_lines(self, ass_content: str, exclude_ranges: List[Dict[str, float]]) -> str:
        """
        Filter out dialogue lines that fall within excluded time ranges.
        
        Args:
            ass_content: Complete ASS file content
            exclude_ranges: List of excluded time ranges (in seconds)
            
        Returns:
            Filtered ASS content
        """
        if not exclude_ranges:
            return ass_content
        
        lines = ass_content.split('\n')
        filtered_lines: List[str] = []
        
        for line in lines:
            if line.startswith('Dialogue:'):
                # Parse dialogue line to get timing
                parts = line.split(',', 9)
                if len(parts) >= 3:
                    start_str = parts[1]
                    end_str = parts[2]
                    
                    # Convert ASS time to seconds
                    try:
                        start_parts = start_str.split(':')
                        start_sec = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + float(start_parts[2])
                        
                        end_parts = end_str.split(':')
                        end_sec = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + float(end_parts[2])
                        
                        # Check if in excluded range
                        if not is_in_excluded_range(start_sec, end_sec, exclude_ranges):
                            filtered_lines.append(line)
                    except (ValueError, IndexError):
                        # If parsing fails, keep the line
                        filtered_lines.append(line)
            else:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    async def _get_video_resolution(self, video_path: str) -> Tuple[int, int]:
        """
        Get video resolution using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            (width, height) tuple
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                width, height = output.split(',')
                return int(width), int(height)
            else:
                logger.warning(f"Could not get video resolution, using default. Error: {stderr.decode() if stderr else 'Unknown error'}")
                return 1920, 1080
                
        except Exception as e:
            logger.error(f"Error getting video resolution: {e}")
            return 1920, 1080

    async def process_caption_job(self, job_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a caption job with advanced features.
        
        Args:
            job_id: Job identifier
            params: Job parameters including:
                - video_url: Video URL (required)
                - captions: Caption content/URL (optional - will auto-transcribe if not provided)
                - settings: Style settings dict (optional)
                - replace: Text replacement array (optional)
                - exclude_time_ranges: Time ranges to exclude (optional)
                - language: Language for transcription (optional, default: 'auto')
                
        Returns:
            Dict with url, path, and metadata
        """
        video_path = None
        caption_path = None
        output_path = None
        
        try:
            # Extract parameters
            video_url = params['video_url']
            captions = params.get('captions')
            settings = params.get('settings', {})
            replace = params.get('replace', [])
            exclude_time_ranges = params.get('exclude_time_ranges', [])
            language = params.get('language', 'auto')
            supplied_transcription = params.get('transcription_result')
            
            # Convert AnyUrl objects to strings
            video_url = str(video_url)
            if captions:
                captions = str(captions)
            
            # Normalize exclude_time_ranges
            if exclude_time_ranges:
                exclude_time_ranges = normalize_exclude_time_ranges(exclude_time_ranges)
            
            # Convert replace array to dict
            replace_dict: Dict[str, str] = {}
            for item in replace:
                if 'find' in item and 'replace' in item:
                    replace_dict[item['find']] = item['replace']
            
            logger.info(f"Job {job_id}: Processing advanced caption job for {video_url}")
            logger.info(f"Job {job_id}: Settings: {settings}")
            logger.info(f"Job {job_id}: Style: {settings.get('style', 'classic')}")
            
            # Download video
            video_path, _ = await download_media_file(video_url, TEMP_PATH)
            logger.info(f"Job {job_id}: Video downloaded to {video_path}")
            
            # Get video resolution
            video_resolution = await self._get_video_resolution(video_path)
            logger.info(f"Job {job_id}: Video resolution: {video_resolution}")
            
            # Get or generate transcription
            transcription_result = None

            if supplied_transcription:
                logger.info(f"Job {job_id}: Using supplied transcription result")
                transcription_result = supplied_transcription

            if captions:
                # Check if captions is a URL
                parsed = cast(ParseResult, urlparse(captions))
                if parsed.scheme in ['http', 'https']:
                    # Download caption file
                    logger.info(f"Job {job_id}: Downloading captions from URL")
                    caption_file, _ = await download_media_file(captions, TEMP_PATH)
                    with open(caption_file, 'r', encoding='utf-8') as f:
                        caption_content = f.read()
                    os.remove(caption_file)
                else:
                    caption_content = captions
                
                # Check if it's ASS format
                if '[Script Info]' in caption_content:
                    # Use ASS directly
                    logger.info(f"Job {job_id}: Using provided ASS captions")
                    subtitle_content = caption_content
                elif self._is_srt_format(caption_content):
                    # Treat as SRT, convert to transcription format
                    logger.info(f"Job {job_id}: Converting SRT to transcription format")
                    transcription_result = self._srt_to_transcription_result(caption_content)
                else:
                    # Treat as plain text. Prefer supplied word timings; otherwise
                    # transcribe the audio first and align the text to that clock.
                    if transcription_result:
                        logger.info(f"Job {job_id}: Aligning custom text to supplied transcription timing")
                        transcription_result = self._align_text_with_transcription(caption_content, transcription_result)
                    else:
                        logger.info(f"Job {job_id}: Custom text provided, transcribing audio and aligning text")
                        try:
                            # First get the actual transcription from audio (Whisper word timestamps)
                            audio_transcription = await self._generate_transcription(video_path, language)
                            # Then align the provided text with the audio transcription
                            transcription_result = self._align_text_with_transcription(caption_content, audio_transcription)
                        except Exception as whisper_err:
                            # Whisper unavailable — fall back to duration-based estimation
                            logger.warning(f"Job {job_id}: Whisper transcription failed ({whisper_err}), using text-based timing")
                            transcription_result = await self._generate_transcription_from_text(caption_content, video_path)
            else:
                if transcription_result:
                    logger.info(f"Job {job_id}: No captions provided, using supplied transcription timing")
                else:
                    # Generate transcription from audio
                    logger.info(f"Job {job_id}: No captions provided, auto-transcribing")
                    transcription_result = await self._generate_transcription(video_path, language)
            
            # Generate ASS subtitle content if we have transcription
            subtitle_content = None
            if transcription_result:
                style_type = settings.get('style', 'classic').lower()
                logger.info(f"Job {job_id}: Generating {style_type} style captions")
                subtitle_content = self._process_subtitle_events(
                    transcription_result,
                    style_type,
                    settings,
                    replace_dict,
                    video_resolution
                )
                
                # Apply exclude_time_ranges filter
                if exclude_time_ranges:
                    logger.info(f"Job {job_id}: Filtering excluded time ranges")
                    subtitle_content = self._filter_subtitle_lines(subtitle_content, exclude_time_ranges)
            
            # Make sure we have subtitle content
            if not subtitle_content:
                raise ValueError("No subtitle content generated")
            
            # Save ASS file
            caption_filename = f"{job_id}_captions.ass"
            caption_path = os.path.join(TEMP_PATH, caption_filename)
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(subtitle_content)
            logger.info(f"Job {job_id}: Caption file saved to {caption_path}")
            
            # Add captions to video using FFmpeg
            output_filename = f"{job_id}_captioned.mp4"
            output_path = os.path.join(TEMP_PATH, "output", output_filename)
            
            logger.info(f"Job {job_id}: Adding captions to video with FFmpeg")
            
            # Build FFmpeg command
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles='{caption_path}'",
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Job {job_id}: FFmpeg error: {error_msg}")
                raise Exception(f"FFmpeg processing failed: {error_msg}")
            
            logger.info(f"Job {job_id}: FFmpeg processing complete")
            
            # Upload to S3
            s3_key = f"videos/captioned_{uuid.uuid4().hex}.mp4"
            s3_url = await s3_service.upload_file(output_path, s3_key)
            logger.info(f"Job {job_id}: Uploaded to S3: {s3_url}")
            
            # Get file metadata
            file_size = os.path.getsize(output_path)
            
            # Clean up temporary files
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if caption_path and os.path.exists(caption_path):
                os.remove(caption_path)
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
            
            return {
                "url": s3_url,
                "path": s3_key,
                "file_size": file_size,
                "width": video_resolution[0],
                "height": video_resolution[1],
                "style": settings.get('style', 'classic')
            }
            
        except Exception as e:
            logger.error(f"Job {job_id}: Caption processing failed: {e}", exc_info=True)
            
            # Clean up on error
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if caption_path and os.path.exists(caption_path):
                os.remove(caption_path)
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
            
            raise


# Create service instance
advanced_caption_service = AdvancedCaptionService()
