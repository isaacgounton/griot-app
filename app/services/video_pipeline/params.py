"""Parameter normalization for the video pipeline."""
from app.services.video_pipeline.models import PipelineParams, SceneInput

LANGUAGE_MAP = {
    'en': 'english', 'fr': 'french', 'es': 'spanish', 'de': 'german',
    'it': 'italian', 'pt': 'portuguese', 'ru': 'russian', 'zh': 'chinese',
    'ja': 'japanese', 'ko': 'korean', 'ar': 'arabic', 'hi': 'hindi',
    'th': 'thai', 'vi': 'vietnamese', 'pl': 'polish', 'nl': 'dutch',
    'sv': 'swedish', 'da': 'danish', 'fi': 'finnish', 'no': 'norwegian',
    'tr': 'turkish', 'el': 'greek', 'he': 'hebrew', 'id': 'indonesian',
    'ms': 'malay', 'ro': 'romanian', 'hu': 'hungarian', 'cs': 'czech',
    'sk': 'slovak', 'uk': 'ukrainian', 'bg': 'bulgarian', 'hr': 'croatian',
    'sr': 'serbian', 'sl': 'slovenian', 'lt': 'lithuanian', 'lv': 'latvian',
    'et': 'estonian', 'ta': 'tamil', 'te': 'telugu', 'bn': 'bengali',
    'mr': 'marathi', 'gu': 'gujarati', 'kn': 'kannada', 'ml': 'malayalam',
    'ur': 'urdu', 'fa': 'persian', 'sw': 'swahili', 'af': 'afrikaans',
}

POSITION_MAP = {
    'top': 'top_center',
    'center': 'middle_center',
    'bottom': 'bottom_center',
    'top_left': 'top_left',
    'top_center': 'top_center',
    'top_right': 'top_right',
    'middle_left': 'middle_left',
    'middle_center': 'middle_center',
    'middle_right': 'middle_right',
    'bottom_left': 'bottom_left',
    'bottom_center': 'bottom_center',
    'bottom_right': 'bottom_right',
}


def normalize_params(raw: dict) -> PipelineParams:
    """Convert raw frontend params dict into a typed PipelineParams."""
    p = PipelineParams()

    # Orientation
    p.orientation = raw.get('orientation') or raw.get('video_orientation', 'landscape')

    # Dimensions
    w = raw.get('image_width') or raw.get('width')
    h = raw.get('image_height') or raw.get('height')
    defaults = {'portrait': (720, 1280), 'square': (720, 720), 'landscape': (1280, 720)}
    dw, dh = defaults.get(p.orientation, (1280, 720))
    p.width = w or dw
    p.height = h or dh

    # Language (multiple frontend keys)
    p.language = (
        raw.get('language') or raw.get('voice_language') or
        raw.get('tts_language') or raw.get('script_language') or 'en'
    )

    # TTS
    p.enable_voice_over = raw.get('enable_voice_over', True)
    p.tts_provider = raw.get('tts_provider') or raw.get('voice_provider', 'kokoro')
    p.voice_name = raw.get('voice') or raw.get('voice_name', 'af_sarah')
    p.voice_speed = raw.get('tts_speed') or raw.get('voice_speed', 1.0)

    # Script
    p.topic = raw.get('topic')
    p.custom_script = raw.get('custom_script')
    p.auto_topic = raw.get('auto_topic', False)
    p.script_type = raw.get('script_type', 'facts')
    p.script_provider = raw.get('script_provider', 'auto')
    p.max_duration = raw.get('max_duration') or raw.get('duration', 60)

    # Media
    p.footage_provider = raw.get('footage_provider', 'pexels')
    p.media_type = raw.get('media_type', 'video')
    p.footage_quality = raw.get('footage_quality', 'high')

    # AI provider params
    p.ai_video_provider = raw.get('ai_video_provider', 'pollinations')
    p.ai_video_model = raw.get('ai_video_model', 'veo')
    p.ai_image_provider = raw.get('ai_image_provider', 'together')
    p.ai_image_model = raw.get('ai_image_model', '')

    # Motion params
    motion = {}
    for key in ('effect_type', 'zoom_speed', 'pan_direction', 'ken_burns_keypoints'):
        if key in raw:
            motion[key] = raw[key]
    p.motion_params = motion

    # Audio
    p.enable_built_in_audio = raw.get('enable_built_in_audio', False)
    p.background_music = raw.get('background_music')
    p.background_music_mood = raw.get('background_music_mood', 'upbeat')
    p.background_music_volume = raw.get('background_music_volume', 0.3)

    # Captions
    p.add_captions = raw.get('add_captions', False)
    p.caption_style = raw.get('caption_style', 'tiktok_viral')
    p.caption_properties = _build_caption_properties(raw)

    # Video
    p.frame_rate = raw.get('frame_rate', 30)
    p.crossfade_duration = raw.get('crossfade_duration', 0.3)

    # Scenes mode (pre-segmented input from scene builder)
    raw_scenes = raw.get('scenes')
    if raw_scenes and isinstance(raw_scenes, list):
        p.scenes = [
            SceneInput(
                text=s.get('text', ''),
                search_terms=s.get('searchTerms', s.get('search_terms', [])),
                duration=s.get('duration', 3.0),
            )
            for s in raw_scenes
            if isinstance(s, dict) and s.get('text', '').strip()
        ]
        # Auto-set custom_script from scenes so script_step returns it as-is
        if p.scenes and not p.custom_script:
            p.custom_script = ' '.join(s.text for s in p.scenes)

    # Keep raw for strategy pass-through (strategies still expect raw dicts)
    # Inject motion_params so strategies can find them via params.get('motion_params')
    raw['motion_params'] = motion
    p.raw_params = raw

    return p


def _build_caption_properties(raw: dict) -> dict:
    """Extract and normalize caption properties from raw params."""
    props = dict(raw.get('caption_properties') or {})

    mapping = {
        'caption_color': 'line_color',
        'highlight_color': 'word_color',
        'font_size': 'font_size',
        'font_family': 'font_family',
        'words_per_line': 'max_words_per_line',
        'margin_v': 'margin_v',
        'outline_width': 'outline_width',
        'all_caps': 'all_caps',
    }
    for frontend_key, backend_key in mapping.items():
        if raw.get(frontend_key) is not None:
            props[backend_key] = raw[frontend_key]

    # Position mapping
    if raw.get('caption_position'):
        props['position'] = POSITION_MAP.get(raw['caption_position'], raw['caption_position'])

    # Fallback: word_color from line_color
    if 'word_color' not in props and 'line_color' in props:
        props['word_color'] = props['line_color']

    return props


def language_code_to_name(code: str) -> str:
    """Map language code to full name for script generator."""
    return LANGUAGE_MAP.get(code.lower(), code)


def calculate_target_words(max_duration: int) -> int:
    """Average speaking rate: ~2.8 words per second."""
    return int(max_duration * 2.8)
