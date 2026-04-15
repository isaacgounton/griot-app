"""Step 7: Caption rendering onto video."""
import uuid
import logging
from app.services.video_pipeline.models import PipelineParams, CaptionResult, AudioResult
from app.services.video.caption_service import advanced_caption_service
from app.config import get_caption_style

logger = logging.getLogger(__name__)


def _get_responsive_caption_properties(style: str, width: int, height: int) -> dict:
    """Compute responsive caption properties from config + dimensions."""
    try:
        base_config = get_caption_style(style)
    except Exception:
        base_config = {}

    is_portrait = height > width
    base_font_size = min(width, height) // 15
    if is_portrait:
        base_font_size = int(base_font_size * 0.9)

    margin_bottom = max(80, height // 10)
    max_words = 3 if is_portrait else 4
    outline_width = max(2, int(base_font_size * 0.1))

    props = {
        'style': style,
        'font_size': base_config.get('font_size', base_font_size),
        'line_color': base_config.get('line_color', '#FFFFFF'),
        'word_color': base_config.get('word_color', '#FFFF00'),
        'outline_color': base_config.get('outline_color', 'black'),
        'outline_width': base_config.get('outline_width', outline_width),
        'position': base_config.get('position', 'bottom_center'),
        'max_words_per_line': base_config.get('max_words_per_line', max_words),
        'line_spacing': base_config.get('line_spacing', 1.3 if is_portrait else 1.2),
        'margin_bottom': margin_bottom,
        'text_align': base_config.get('text_align', 'center'),
        'all_caps': base_config.get('all_caps', False),
        'font_family': base_config.get('font_family', 'Arial-Bold'),
        'bold': base_config.get('bold', True),
    }

    # Style-specific properties
    if 'viral' in style or 'bounce' in style:
        props.update({'bounce_intensity': 1.5, 'animation_speed': 1.2})
    elif 'typewriter' in style:
        props.update({'typewriter_speed': 3.0})
    elif 'fade' in style:
        props.update({'animation_speed': 1.0})

    return props


async def render_captions(
    video_url: str,
    script_text: str,
    params: PipelineParams,
    audio_result: AudioResult | None = None,
) -> CaptionResult:
    """Render captions onto video. Returns original URL if captions disabled."""

    if not params.add_captions:
        return CaptionResult(video_url=video_url, srt_url=None)

    logger.info(f"Rendering captions: style={params.caption_style}")

    # Build final caption properties: config defaults + user overrides
    props = _get_responsive_caption_properties(params.caption_style, params.width, params.height)
    props.update(params.caption_properties)

    transcription_result = None
    use_script_as_captions = True
    if audio_result and audio_result.word_timestamps:
        # Prefer Whisper's natural phrase-level segments — they break at
        # speech pauses so captions appear/disappear with the speaker's
        # rhythm, just like professional TikTok/YouTube captioning.
        if audio_result.whisper_segments:
            transcription_result = {
                'segments': audio_result.whisper_segments,
                'language': params.language,
            }
            logger.info(
                "Rendering captions from Whisper segments "
                f"({len(audio_result.whisper_segments)} segments, "
                f"{len(audio_result.word_timestamps)} words)"
            )
        else:
            # Fallback: single segment with all words (old behaviour)
            transcription_result = {
                'segments': [{
                    'id': 0,
                    'start': audio_result.word_timestamps[0]['start'],
                    'end': audio_result.word_timestamps[-1]['end'],
                    'text': script_text,
                    'words': audio_result.word_timestamps,
                }],
                'language': params.language,
            }
            logger.info(
                "Rendering captions from flat word timestamps "
                f"({len(audio_result.word_timestamps)} words, no segment boundaries)"
            )
        # Do NOT pass script_text as captions — the alignment step uses
        # naive 1:1 index mapping which breaks for French and other
        # languages where Whisper tokenizes differently from space-split.
        use_script_as_captions = False
    else:
        logger.info("No clean TTS timings available, falling back to video transcription for captions")

    caption_params = {
        'video_url': video_url,
        'captions': script_text if use_script_as_captions else None,
        'settings': props,
        'language': 'auto',
        'transcription_result': transcription_result,
    }

    try:
        result = await advanced_caption_service.process_caption_job(
            f"pipeline_captions_{uuid.uuid4().hex[:8]}", caption_params
        )
        return CaptionResult(
            video_url=result['url'],
            srt_url=result.get('srt_url'),
        )
    except Exception as e:
        logger.error(f"Caption rendering failed (non-fatal): {e}")
        return CaptionResult(video_url=video_url, srt_url=None)
