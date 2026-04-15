from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, AnyUrl, field_validator


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Job type enumeration."""
    IMAGE_TO_VIDEO = "image_to_video"
    IMAGE_OVERLAY = "image_overlay"
    VIDEO_OVERLAY = "video_overlay"
    TEXT_TO_SPEECH = "text_to_speech"
    MUSIC_GENERATION = "music_generation"
    MEDIA_TRANSCRIPTION = "media_transcription"
    VIDEO_CONCATENATION = "video_concatenation"
    VIDEO_ADD_AUDIO = "video_add_audio"
    VIDEO_ADD_CAPTIONS = "video_add_captions"
    FFMPEG_COMPOSE = "ffmpeg_compose"
    S3_UPLOAD = "s3_upload"
    CODE_EXECUTION = "code_execution"
    MEDIA_DOWNLOAD = "media_download"
    YOUTUBE_TRANSCRIPT = "youtube_transcript"
    VIDEO_THUMBNAILS = "video_thumbnails"
    VIDEO_CLIPS = "video_clips"
    VIDEO_FRAMES = "video_frames"
    MEDIA_CONVERSION = "media_conversion"
    TEXT_OVERLAY = "text_overlay"
    AI_SCRIPT_GENERATION = "ai_script_generation"
    VIDEO_SEARCH_QUERY_GENERATION = "video_search_query_generation"
    STOCK_VIDEO_SEARCH = "stock_video_search"
    FOOTAGE_TO_VIDEO = "footage_to_video"
    METADATA_EXTRACTION = "metadata_extraction"
    SIMONE_VIDEO_TO_BLOG = "simone_video_to_blog"
    SIMONE_ENHANCED_PROCESSING = "simone_enhanced_processing"
    MEDIA_SILENCE_DETECTION = "media_silence_detection"
    MEDIA_AUDIO_ANALYSIS = "media_audio_analysis"
    YOUTUBE_SHORTS = "youtube_shorts"
    DOCUMENT_TO_MARKDOWN = "document_to_markdown"
    LANGEXTRACT_DATA_EXTRACTION = "langextract_data_extraction"
    MARKER_DOCUMENT_CONVERSION = "marker_document_conversion"
    AIIMAGE_TO_VIDEO = "aiimage_to_video"
    SHORT_VIDEO_CREATION = "short_video_creation"
    RESEARCH_NEWS = "research_news"
    SCENES_TO_VIDEO = "scenes_to_video"
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    POLLINATIONS_AUDIO = "pollinations_audio"
    POLLINATIONS_VIDEO_ANALYSIS = "pollinations_video_analysis"
    VIDEO_GENERATION = "video_generation"
    VIDEO_FROM_IMAGE = "video_from_image"
    IMAGE_SEARCH = "image_search"
    IMAGE_ENHANCEMENT = "image_enhancement"
    WEB_SCREENSHOT = "web_screenshot"
    # Studio V2
    STUDIO_TTS_GENERATION = "studio_tts_generation"
    STUDIO_MEDIA_GENERATION = "studio_media_generation"
    STUDIO_SCENE_PREVIEW = "studio_scene_preview"
    STUDIO_EXPORT = "studio_export"
    STUDIO_AI_SCENES = "studio_ai_scenes"


class Job(BaseModel):
    """Job model."""
    id: str
    status: JobStatus = JobStatus.PENDING
    operation: str
    params: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[int] = None
    created_at: str
    updated_at: str


class JobResponse(BaseModel):
    """Job response model."""
    job_id: str


class JobStatusResponse(BaseModel):
    """Job status response model."""
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class NormalizationOptions(BaseModel):
    """Text normalization options for Kokoro TTS."""
    normalize: bool = Field(
        default=True,
        description="Enable text normalization to make it easier for the model to pronounce"
    )
    unit_normalization: bool = Field(
        default=False, 
        description="Transform units like 10KB to 10 kilobytes"
    )
    url_normalization: bool = Field(
        default=True,
        description="Normalize URLs for proper pronunciation"
    )
    email_normalization: bool = Field(
        default=True,
        description="Normalize email addresses for proper pronunciation"
    )
    phone_normalization: bool = Field(
        default=True,
        description="Normalize phone numbers for proper pronunciation"
    )
    replace_remaining_symbols: bool = Field(
        default=True,
        description="Replace remaining symbols with their word equivalents"
    )


class WordTimestamp(BaseModel):
    """Word-level timestamp information."""
    word: str = Field(..., description="The word or token")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")


class TextToSpeechRequest(BaseModel):
    """
    Enhanced text to speech request model supporting multiple TTS providers with advanced features.
    
    The text will be converted to an audio file using the specified voice and provider.
    When using Kokoro provider, additional advanced features are available.
    Supports both 'text' (primary) and 'input' (OpenAI compatibility) fields.
    """
    text: Optional[str] = Field(
        default=None,
        description="The text that will be converted to speech (max 5000 characters). "
                   "For Kokoro: supports pause tags like [pause:0.5s] for silence.",
        max_length=5000
    )
    input: Optional[str] = Field(
        default=None,
        description="Alternative to 'text' field for OpenAI compatibility. "
                   "If both 'text' and 'input' are provided, 'text' takes precedence.",
        max_length=5000
    )
    
    @field_validator('input')
    @classmethod
    def validate_text_or_input_provided(cls, v, info):
        """Ensure at least one of text or input is provided."""
        text = info.data.get('text')
        if not text and not v:
            raise ValueError('Either "text" or "input" field must be provided')
        return v
    
    def get_text_content(self) -> str:
        """Get the text content, preferring 'text' over 'input' field."""
        return self.text or self.input or ""
    voice: str = Field(
        default="af_heart",
        description="Voice to use. For Kokoro: af_heart, af_bella, am_michael, etc. "
                   "Voice combinations supported with '+' (e.g., 'af_heart+af_bella'). "
                   "For Edge TTS: OpenAI-compatible voices or native Edge voices."
    )
    provider: Optional[str] = Field(
        default=None,
        description="TTS provider: 'kokoro' or 'edge'. If not specified, uses default."
    )
    response_format: str = Field(
        default="mp3",
        description="Audio format. Kokoro: mp3, wav, opus, aac, flac. Edge TTS: mp3, wav, opus, aac, flac, pcm."
    )
    speed: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Playback speed (0.0 to 2.0). Edge TTS: full range supported. Kokoro: fixed speed only."
    )
    
    # Streaming options
    stream: bool = Field(
        default=False,
        description="Stream audio response in real-time (Edge TTS only currently)."
    )
    stream_format: Optional[str] = Field(
        default="audio",
        description="Response format for streaming: 'audio' (raw audio data) or 'sse' (Server-Sent Events with JSON). Default: 'audio'"
    )
    model: Optional[str] = Field(
        default=None,
        description="TTS model to use (OpenAI compatibility). Options: 'tts-1', 'tts-1-hd', 'gpt-4o-mini-tts'"
    )
    remove_filter: bool = Field(
        default=False,
        description="Skip text preprocessing/filtering (Edge TTS only)."
    )
    
    # Advanced Kokoro-specific features
    volume_multiplier: float = Field(
        default=1.0,
        ge=0.1,
        le=3.0,
        description="Volume multiplier (0.1 to 3.0, Kokoro only)."
    )
    lang_code: Optional[str] = Field(
        default=None,
        description="Language code override for phonemization (Kokoro only, e.g., 'en', 'ja', 'zh')."
    )
    normalization_options: Optional[NormalizationOptions] = Field(
        default=None,
        description="Text normalization options (Kokoro only)."
    )
    return_timestamps: bool = Field(
        default=False,
        description="Return word-level timestamps (Kokoro only)."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class TextToSpeechResult(BaseModel):
    """Enhanced text to speech result model."""
    audio_url: AnyUrl = Field(..., description="URL to the generated audio file")
    tts_engine: str = Field(..., description="TTS engine used for generation")
    voice: str = Field(..., description="Voice used for synthesis")
    response_format: str = Field(..., description="Audio format of the output")
    estimated_duration: Optional[float] = Field(None, description="Estimated audio duration in seconds")
    word_count: Optional[int] = Field(None, description="Number of words processed")
    word_timestamps: Optional[List[WordTimestamp]] = Field(None, description="Word-level timestamps (Kokoro only)")
    speed: Optional[float] = Field(None, description="Speed multiplier used")
    volume_multiplier: Optional[float] = Field(None, description="Volume multiplier used (Kokoro only)")
    lang_code: Optional[str] = Field(None, description="Language code used (Kokoro only)") 


class MediaTranscriptionRequest(BaseModel):
    """
    Media transcription request model.

    This model represents a request to transcribe a media file (audio or video)
    using the Whisper model.
    """
    media_url: AnyUrl = Field(
        description="URL of the media file to be transcribed. Supports S3 URLs and most public media URLs."
    )
    include_text: bool = Field(
        default=True,
        description="Include plain text transcription in the response."
    )
    include_srt: bool = Field(
        default=True,
        description="Include SRT format subtitles in the response and save to S3."
    )
    word_timestamps: bool = Field(
        default=False,
        description="Include timestamps for individual words. This enables more precise timing information."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    include_segments: bool = Field(
        default=False,
        description="Include timestamped segments in the response. Segments are larger chunks of speech with start/end times."
    )
    language: Optional[str] = Field(
        default=None,
        description="Source language code for transcription (e.g., 'en', 'fr', 'es'). "
                   "If not provided, Whisper will auto-detect the language."
    )
    max_words_per_line: Optional[int] = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of words per line in the generated SRT file. "
                   "Controls how caption text is split across lines for better readability."
    )
    beam_size: Optional[int] = Field(
        default=5,
        ge=1,
        le=10,
        description="Beam search size for improved transcription accuracy. "
                   "Higher values (5-10) provide better accuracy but take longer. "
                   "Default is 5 for good balance of speed and quality."
    )
    model_size: Optional[str] = Field(
        default="base",
        description="Whisper model size: tiny, base, small, medium, large-v1, large-v2, large-v3. "
                   "Larger models are more accurate but slower."
    )
    temperature: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for transcription. 0 is deterministic (greedy). "
                   "Higher values add randomness. Default is 0."
    )
    initial_prompt: Optional[str] = Field(
        default=None,
        description="Optional text to guide the model's style or continue a previous segment. "
                   "Useful for providing context, spelling hints, or maintaining consistent formatting."
    )


class MediaTranscriptionResult(BaseModel):
    """Media transcription result model."""
    text: Optional[str] = Field(
        None,
        description="Plain text transcription of the media."
    )
    srt_url: Optional[AnyUrl] = Field(
        None, 
        description="URL to the SRT subtitle file stored in S3."
    )
    words: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Word-level timestamps with start and end times for each word."
    )
    segments: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Timestamped segments with start and end times for larger chunks of speech."
    )


class CaptionReplace(BaseModel):
    """
    Model for text replacements in captions.
    Allows automatic replacement of specific words or phrases in caption text.
    """
    find: str = Field(
        ...,
        description="Text to find in captions."
    )
    replace: str = Field(
        ...,
        description="Text to replace the found text with."
    )


class VideoCaptionProperties(BaseModel):
    """
    Properties for customizing the appearance and style of video captions.
    """
    line_color: Optional[str] = Field(
        default=None,
        description="Color of the text line (e.g., 'white', '#FFFFFF')."
    )
    word_color: Optional[str] = Field(
        default=None,
        description="Color of individual words when highlighted (e.g., 'yellow', '#FFFF00')."
    )
    outline_color: Optional[str] = Field(
        default=None,
        description="Color of text outline/stroke (e.g., 'black', '#000000')."
    )
    all_caps: Optional[bool] = Field(
        default=None,
        description="Whether to convert all text to uppercase."
    )
    max_words_per_line: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Maximum number of words to display per line in generated captions. Controls how caption text is split across lines for better readability. Valid range is 1-20, defaults to 10 if not specified."
    )
    x: Optional[int] = Field(
        default=None,
        description="X coordinate for caption positioning (manual positioning)."
    )
    y: Optional[int] = Field(
        default=None,
        description="Y coordinate for caption positioning (manual positioning)."
    )
    position: Optional[str] = Field(
        default=None,
        description="Predefined position for captions (e.g., 'bottom_center', 'top_left')."
    )
    alignment: Optional[str] = Field(
        default=None,
        description="Text alignment within caption area ('left', 'center', 'right')."
    )
    font_family: Optional[str] = Field(
        default=None,
        description="Font family to use for captions."
    )
    font_size: Optional[int] = Field(
        default=None,
        description="Font size for captions in pixels."
    )
    bold: Optional[bool] = Field(
        default=None,
        description="Whether to apply bold formatting to text."
    )
    italic: Optional[bool] = Field(
        default=None,
        description="Whether to apply italic formatting to text."
    )
    underline: Optional[bool] = Field(
        default=None,
        description="Whether to apply underline formatting to text."
    )
    strikeout: Optional[bool] = Field(
        default=None,
        description="Whether to apply strikeout formatting to text."
    )
    style: Optional[str] = Field(
        default=None,
        description="Caption display style. Options: 'classic', 'karaoke', 'highlight', 'underline', 'word_by_word', 'bounce' (popular bouncing highlight), 'viral_bounce' (enhanced bounce with scaling), 'viral_cyan', 'viral_yellow', 'viral_green', 'typewriter' (character-by-character reveal), 'fade_in' (text fades in gradually), 'modern_neon', 'cinematic_glow', 'social_pop'."
    )
    outline_width: Optional[int] = Field(
        default=None,
        description="Width of text outline/stroke in pixels."
    )
    spacing: Optional[int] = Field(
        default=None,
        description="Spacing between lines in pixels."
    )
    angle: Optional[int] = Field(
        default=None,
        description="Rotation angle of text in degrees."
    )
    shadow_offset: Optional[int] = Field(
        default=None,
        description="Shadow offset distance in pixels."
    )
    # Background properties
    background_color: Optional[str] = Field(
        default=None,
        description="Background color for captions (e.g., 'black', '#000000')."
    )
    background_opacity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Opacity of background from 0.0 (transparent) to 1.0 (opaque)."
    )
    background_padding: Optional[int] = Field(
        default=None,
        description="Padding around text within background in pixels."
    )
    background_radius: Optional[int] = Field(
        default=None,
        description="Corner radius for background in pixels for rounded corners."
    )
    
    # Modern visual effects (TikTok-style)
    gradient_colors: Optional[List[str]] = Field(
        default=None,
        description="List of colors for gradient text effect (e.g., ['#FF0000', '#00FF00', '#0000FF']). Creates rainbow or multi-color gradient effects popular on social media."
    )
    glow_effect: Optional[bool] = Field(
        default=None,
        description="Enable neon glow effect around text for modern, eye-catching appearance."
    )
    glow_color: Optional[str] = Field(
        default=None,
        description="Color for glow effect (e.g., '#00FFFF', 'cyan'). Only used when glow_effect is enabled."
    )
    glow_intensity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Glow intensity from 0.0 (subtle) to 2.0 (very bright). Higher values create more dramatic glow effects."
    )
    rounded_corners: Optional[int] = Field(
        default=None,
        ge=0,
        le=50,
        description="Rounded corner radius for text background. Enables modern, smooth background boxes around captions."
    )
    
    # Animation and timing effects
    animation_speed: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=3.0,
        description="Speed multiplier for animations (0.1 = very slow, 3.0 = very fast). Controls how quickly text animations play."
    )
    bounce_intensity: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=2.0,
        description="Bounce effect intensity for 'bounce' and 'viral_bounce' styles (0.1 = subtle, 2.0 = dramatic). Higher values create more noticeable bouncing."
    )
    typewriter_speed: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=5.0,
        description="Typewriter effect speed in characters per second. Controls how fast text appears character-by-character in 'typewriter' style."
    )
    
    # Smart AI-powered features
    auto_emoji: Optional[bool] = Field(
        default=None,
        description="Automatically replace common words with relevant emojis (e.g., 'happy' → '😊', 'fire' → '🔥'). Great for social media content."
    )
    auto_capitalization: Optional[bool] = Field(
        default=None,
        description="Smart capitalization for emphasis on important words and phrases. Uses AI to determine which words should be emphasized."
    )
    confidence_styling: Optional[bool] = Field(
        default=None,
        description="Vary text styling based on speech transcription confidence. Lower confidence words appear dimmer or with different styling."
    )
    
    # Modern viral-style caption options
    highlight_color: Optional[str] = Field(
        default=None,
        description="Color for highlighting active words in viral styles (e.g., '#00FFFF', 'cyan'). Used in viral_cyan, viral_yellow, viral_green styles."
    )
    caption_position: Optional[str] = Field(
        default=None,
        description="Caption position on video: 'top', 'center', 'bottom'. Affects vertical positioning of caption text."
    )


class ImageToVideoRequest(BaseModel):
    """
    Enhanced comprehensive request model for creating a video from an image with advanced audio and caption features.
    
    This combines the functionality of image-to-video conversion, advanced text-to-speech with multiple providers,
    audio mixing, and modern TikTok-style video captioning with AI-powered enhancements in a single request.
    
    For best results:
    - For standard quality: frame_rate=30, zoom_speed=10, video_length=10
    - For high quality: frame_rate=60, zoom_speed=10, video_length=15
    - For TikTok-style content: Use 'viral_bounce' or 'bounce' caption styles with gradient colors and glow effects
    - For professional content: Use 'fade_in' caption style with subtle animations
    """
    # Image to video parameters
    image_url: AnyUrl = Field(
        description="URL of the image to convert to video."
    )
    video_length: float = Field(
        default=10.0, 
        gt=0, 
        le=30,
        description="Length of output video in seconds. Longer videos will have smoother zoom effects."
    )
    frame_rate: int = Field(
        default=30, 
        gt=0, 
        le=60,
        description="Frame rate of output video. Use 30 for standard quality or 60 for smoother results."
    )
    zoom_speed: float = Field(
        default=10.0, 
        ge=0, 
        le=100,
        description="Speed of zoom effect (0-100). Values between 5-20 produce the smoothest results."
    )
    effect_type: str = Field(
        default="none",
        description="Type of animation effect to apply. Options: 'none', 'zoom', 'zoom_out', 'pan', 'ken_burns'. Use 'none' for a static video with no motion effects."
    )
    pan_direction: Optional[str] = Field(
        default=None,
        description="Direction of pan effect when effect_type is 'pan'. Options: 'left_to_right', 'right_to_left', 'top_to_bottom', 'bottom_to_top', 'diagonal_top_left', 'diagonal_top_right', 'diagonal_bottom_left', 'diagonal_bottom_right'."
    )
    ken_burns_keypoints: Optional[List[Dict[str, float]]] = Field(
        default=None,
        description="List of keypoints for Ken Burns effect when effect_type is 'ken_burns'. Each keypoint is a dictionary with 'time' (in seconds), 'x' (0-1), 'y' (0-1), and 'zoom' (scale factor) values. At least 2 keypoints should be provided."
    )
    
    # Narrator audio parameters (optional)
    narrator_speech_text: Optional[str] = Field(
        default=None,
        description="Text to convert to speech. If provided, a TTS audio will be added to the video."
    )
    voice: Optional[str] = Field(
        default="af_alloy",
        description="The voice to use for speech synthesis if narrator_speech_text is provided. Voice options vary by provider."
    )
    provider: Optional[str] = Field(
        default=None,
        description="TTS provider to use: 'kokoro' (high-quality neural voices) or 'edge' (Microsoft Edge TTS with OpenAI-compatible voices). If not specified, uses the default provider."
    )
    tts_speed: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=3.0,
        description="Speech speed multiplier for TTS (0.1 = very slow, 3.0 = very fast). Only supported by some providers."
    )
    tts_response_format: Optional[str] = Field(
        default="mp3",
        description="Audio format for TTS output: 'mp3', 'wav', 'flac', 'opus'. Default is 'mp3'."
    )
    narrator_audio_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL of an existing audio file to add to the video as narration. Ignored if narrator_speech_text is provided."
    )
    narrator_vol: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Volume level for the narrator audio track (0-100)."
    )
    
    # Background music parameters (optional)
    background_music_url: Optional[str] = Field(
        default=None,
        description="URL of background music to add to the video. Can be a direct audio file or YouTube URL."
    )
    background_music_vol: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Volume level for the background music track (0-100)."
    )
    
    # Enhanced caption parameters (optional)
    should_add_captions: bool = Field(
        default=False,
        description="Whether to automatically add captions by transcribing the audio. If enabled, captions will be generated from either the narrator_speech_text or the narrator audio content."
    )
    caption_properties: Optional[VideoCaptionProperties] = Field(
        default=None,
        description="Advanced styling properties for captions with TikTok-style effects, animations, and AI-powered enhancements. Used when should_add_captions is true."
    )
    caption_text_replacements: Optional[List[CaptionReplace]] = Field(
        default=None,
        description="List of text replacements to apply to generated captions. Useful for correcting TTS transcription errors or customizing content."
    )
    caption_language: Optional[str] = Field(
        default="auto",
        description="Language code for caption generation (e.g., 'en', 'fr', 'es'). Use 'auto' for automatic language detection based on TTS content."
    )
    caption_timing_mode: Optional[str] = Field(
        default="automatic",
        description="Caption timing mode: 'automatic' (sync with audio), 'manual' (use provided timings), 'word_level' (word-by-word timing). Default is 'automatic'."
    )
    
    # Video and audio synchronization
    match_length: str = Field(
        default="audio",
        description="Whether to match the output video length to the 'audio' or 'video'. If 'audio', the video will loop if necessary."
    )

    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )

    @field_validator('background_music_url', mode='before')
    @classmethod
    def validate_background_music_url(cls, v):
        """Convert empty strings to None for optional URL field."""
        if v == "":
            return None
        return v


class ImageToVideoResult(BaseModel):
    """
    Result model for the comprehensive image to video with audio and captions operation.
    """
    final_video_url: AnyUrl = Field(
        description="URL to the final video with audio and captions."
    )
    video_duration: float = Field(
        description="Duration of the output video in seconds."
    )
    has_audio: bool = Field(
        description="Whether the video has audio."
    )
    has_captions: bool = Field(
        description="Whether the video has captions."
    )
    audio_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to the audio file used (if applicable)."
    )
    srt_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to the SRT subtitle file (if applicable)."
    )


class OverlayImagePosition(BaseModel):
    """
    Position information for an overlay image.
    """
    url: AnyUrl = Field(
        description="URL of the overlay image to be placed on the base image."
    )
    x: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Horizontal position (0.0 to 1.0) where 0.0 is the left edge and 1.0 is the right edge."
    )
    y: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Vertical position (0.0 to 1.0) where 0.0 is the top edge and 1.0 is the bottom edge."
    )
    width: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Width of the overlay image relative to the base image width (0.0 to 1.0). If not specified, the original aspect ratio is maintained."
    )
    height: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Height of the overlay image relative to the base image height (0.0 to 1.0). If not specified, the original aspect ratio is maintained."
    )
    rotation: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        lt=360.0,
        description="Rotation angle in degrees (0 to 359.99)."
    )
    opacity: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Opacity of the overlay image (0.0 to 1.0) where 0.0 is fully transparent and 1.0 is fully opaque."
    )
    z_index: Optional[int] = Field(
        default=0,
        description="Z-index for layering multiple overlays. Higher values appear on top of lower values."
    )


class ImageOverlayRequest(BaseModel):
    """
    Request model for overlaying images on top of a base image.

    This model represents a request to overlay one or more images onto a base image,
    with control over position, size, rotation, and opacity.
    """
    base_image_url: AnyUrl = Field(
        description="URL of the base image on which overlays will be placed."
    )
    overlay_images: List[OverlayImagePosition] = Field(
        ...,
        min_length=1,
        description="List of overlay images with their positioning information."
    )
    output_format: Optional[str] = Field(
        default="png",
        description="Output image format (e.g., 'png', 'jpg', 'webp'). Default is 'png'."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    output_quality: Optional[int] = Field(
        default=90,
        ge=1,
        le=100,
        description="Output image quality for lossy formats like JPEG (1-100). Default is 90."
    )
    output_width: Optional[int] = Field(
        default=None,
        gt=0,
        description="Width of the output image in pixels. If not specified, the base image width is used."
    )
    output_height: Optional[int] = Field(
        default=None,
        gt=0,
        description="Height of the output image in pixels. If not specified, the base image height is used."
    )
    maintain_aspect_ratio: Optional[bool] = Field(
        default=True,
        description="Whether to maintain the aspect ratio when resizing the output image."
    )
    
    # Image Stitching Settings
    stitch_mode: Optional[bool] = Field(
        default=False,
        description="Enable stitching mode to combine all overlay images into a single seamless image instead of overlaying them."
    )
    stitch_direction: Optional[str] = Field(
        default="horizontal",
        description="Direction for stitching images. Options: 'horizontal', 'vertical', 'grid'. Default is 'horizontal'."
    )
    stitch_spacing: Optional[int] = Field(
        default=0,
        ge=0,
        le=100,
        description="Spacing between images in pixels when stitching. Default is 0 (no spacing)."
    )
    stitch_max_width: Optional[int] = Field(
        default=1920,
        gt=0,
        description="Maximum width of the stitched image in pixels. Default is 1920."
    )
    stitch_max_height: Optional[int] = Field(
        default=1080,
        gt=0,
        description="Maximum height of the stitched image in pixels. Default is 1080."
    )


class ImageOverlayResult(BaseModel):
    """
    Result model for the image overlay operation.
    """
    image_url: AnyUrl = Field(
        description="URL to the resulting image with overlays."
    )
    width: int = Field(
        description="Width of the output image in pixels."
    )
    height: int = Field(
        description="Height of the output image in pixels."
    )
    format: str = Field(
        description="Format of the output image (e.g., 'png', 'jpg')."
    )
    storage_path: str = Field(
        description="Storage path of the image in S3."
    )


class OverlayVideoPosition(BaseModel):
    """
    Position information for an overlay video.
    """
    url: AnyUrl = Field(
        description="URL of the overlay video to be placed on the base image."
    )
    x: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Horizontal position (0.0 to 1.0) where 0.0 is the left edge and 1.0 is the right edge."
    )
    y: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Vertical position (0.0 to 1.0) where 0.0 is the top edge and 1.0 is the bottom edge."
    )
    width: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Width of the overlay video relative to the base image width (0.0 to 1.0). If not specified, the original aspect ratio is maintained."
    )
    height: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Height of the overlay video relative to the base image height (0.0 to 1.0). If not specified, the original aspect ratio is maintained."
    )
    start_time: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        description="Start time in seconds when the overlay video should begin playing."
    )
    end_time: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="End time in seconds when the overlay video should stop playing. If not specified, plays until the end of the video or base video duration."
    )
    loop: Optional[bool] = Field(
        default=False,
        description="Whether to loop the overlay video if it's shorter than the base video duration."
    )
    opacity: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Opacity of the overlay video (0.0 to 1.0) where 0.0 is fully transparent and 1.0 is fully opaque."
    )
    z_index: Optional[int] = Field(
        default=0,
        description="Z-index for layering multiple overlays. Higher values appear on top of lower values."
    )
    volume: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Volume level of the overlay video audio (0.0 to 1.0). Default is 0.0 (muted)."
    )
    
    # Colorkey/Chroma Key Settings
    colorkey_enabled: Optional[bool] = Field(
        default=False,
        description="Enable colorkey/chroma key effect to make specific colors transparent."
    )
    colorkey_color: Optional[str] = Field(
        default="green",
        description="Color to make transparent (e.g., 'green', 'blue', '#00ff00'). Default is 'green'."
    )
    colorkey_similarity: Optional[float] = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Radius from the key color within which other colors also have full transparency (0.0 to 1.0). Default is 0.1."
    )
    colorkey_blend: Optional[float] = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="How the alpha value for pixels outside the similarity radius is computed (0.0 to 1.0). Default is 0.1."
    )


class VideoOverlayRequest(BaseModel):
    """
    Request model for overlaying videos on top of a base image.

    This model represents a request to overlay one or more videos onto a base image,
    creating a dynamic video composition with control over position, size, timing, and audio.
    """
    base_image_url: AnyUrl = Field(
        description="URL of the base image on which video overlays will be placed."
    )
    overlay_videos: List[OverlayVideoPosition] = Field(
        ...,
        min_length=1,
        description="List of overlay videos with their positioning and timing information."
    )
    output_duration: Optional[float] = Field(
        default=None,
        gt=0,
        le=300,
        description="Duration of the output video in seconds. If not specified, uses the longest overlay video duration."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    frame_rate: Optional[int] = Field(
        default=30,
        ge=15,
        le=60,
        description="Frame rate of the output video. Default is 30 fps."
    )
    output_width: Optional[int] = Field(
        default=None,
        gt=0,
        description="Width of the output video in pixels. If not specified, the base image width is used."
    )
    output_height: Optional[int] = Field(
        default=None,
        gt=0,
        description="Height of the output video in pixels. If not specified, the base image height is used."
    )
    maintain_aspect_ratio: Optional[bool] = Field(
        default=True,
        description="Whether to maintain the aspect ratio when resizing the output video."
    )
    background_audio_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL of background audio to add to the video. Can be a direct audio file or YouTube URL."
    )
    background_audio_volume: Optional[float] = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Volume level for the background audio track (0.0 to 1.0)."
    )


class VideoOverlayResult(BaseModel):
    """
    Result model for the video overlay operation.
    """
    video_url: AnyUrl = Field(
        description="URL to the resulting video with overlays."
    )
    width: int = Field(
        description="Width of the output video in pixels."
    )
    height: int = Field(
        description="Height of the output video in pixels."
    )
    duration: float = Field(
        description="Duration of the output video in seconds."
    )
    frame_rate: int = Field(
        description="Frame rate of the output video."
    )
    has_audio: bool = Field(
        description="Whether the output video has audio."
    )
    storage_path: str = Field(
        description="Storage path of the video in S3."
    )


class VideoConcatenateRequest(BaseModel):
    """
    Enhanced request model for concatenating multiple videos with transition effects.

    This model represents a request to concatenate multiple videos into a single video
    with professional transition effects between video segments.
    """
    video_urls: List[str] = Field(
        ...,
        description="List of video URLs to concatenate. Supports S3 URLs and other video URLs. Minimum 2 videos required."
    )
    output_format: str = Field(
        "mp4",
        description="Output video format (e.g., 'mp4', 'webm', 'mov')"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    transition: str = Field(
        "none",
        description="Transition effect between video segments. Options: 'none' (instant cut), 'fade' (fade in/out transitions), 'dissolve' (crossfade between videos), 'slide' (sliding transition), 'wipe' (wipe transition effect)."
    )
    transition_duration: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Duration of transition effects in seconds (0.1 to 5.0). Only used when transition is not 'none'."
    )
    max_segment_duration: Optional[float] = Field(
        default=None,
        ge=0.5,
        le=900.0,
        description="Maximum duration per video segment in seconds (0.5 to 900 / 15 minutes). If not specified, uses full video duration."
    )
    total_duration_limit: Optional[float] = Field(
        default=None,
        ge=1.0,
        le=3600.0,
        description="Maximum total duration for the concatenated video in seconds (1 to 3600). If not specified, no limit is applied."
    )


class VideoConcatenateResult(BaseModel):
    """
    Result model for video concatenation operation.
    """
    url: AnyUrl = Field(
        description="URL to the concatenated video file stored in S3."
    )
    path: str = Field(
        description="Storage path of the concatenated video in S3."
    )


class VideoAddAudioRequest(BaseModel):
    """
    Enhanced request model for adding audio to a video with advanced sync modes.

    This model represents a request to add background music or other audio to a video,
    with control over volume levels, length matching, and audio synchronization modes.
    """
    video_url: str = Field(
        ...,
        description="URL of the video to add audio to. Supports S3 URLs and other video URLs."
    )
    audio_url: str = Field(
        ...,
        description="URL of the audio to add to the video. Supports S3 URLs and other audio URLs."
    )
    video_volume: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Volume level for the original video track (0-100)."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    audio_volume: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Volume level for the added audio track (0-100)."
    )
    sync_mode: str = Field(
        default="replace",
        description="Audio synchronization mode. Options: 'replace' (replace original audio completely), 'mix' (blend original and new audio), 'overlay' (layer new audio over original)."
    )
    match_length: str = Field(
        default="video",
        description="Whether to match the output length to the 'audio' or 'video'. Default is 'video'."
    )
    fade_in_duration: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Duration in seconds for audio fade-in effect (0.0 to 10.0). Creates smooth audio introduction."
    )
    fade_out_duration: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Duration in seconds for audio fade-out effect (0.0 to 10.0). Creates smooth audio ending."
    )


class VideoAddAudioResult(BaseModel):
    """
    Result model for video add audio operation.
    """
    url: AnyUrl = Field(
        description="URL to the video with added audio stored in S3."
    )
    path: str = Field(
        description="Storage path of the video with added audio in S3."
    )
    duration: float = Field(
        description="Duration of the output video in seconds."
    ) 


class VideoAddCaptionsRequest(BaseModel):
    """
    Enhanced request model for adding captions to a video with advanced styling and AI features.

    This model represents a request to add captions to a video, with options for
    customizing their appearance, using different caption sources, and applying
    modern TikTok-style effects and AI-powered enhancements.
    """
    video_url: str = Field(
        ...,
        description="URL of the video to add captions to. Supports S3 URLs and other video URLs."
    )
    captions: Optional[str] = Field(
        default=None,
        description="Caption content, which can be raw text, URL to an SRT/ASS subtitle file, or None to use auto-transcription from the video's audio."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    caption_properties: Optional[VideoCaptionProperties] = Field(
        default=None,
        description="Advanced styling properties for captions, including modern TikTok-style effects, animations, and AI-powered enhancements."
    )
    replace: Optional[List[CaptionReplace]] = Field(
        default=None,
        description="List of text replacements to apply to captions. Useful for correcting transcription errors or customizing content."
    )
    language: Optional[str] = Field(
        default="auto",
        description="Language code for caption transcription (e.g., 'en', 'fr', 'es'). Use 'auto' for automatic language detection."
    )


class VideoAddCaptionsResult(BaseModel):
    """
    Result model for video add captions operation.
    """
    url: AnyUrl = Field(
        description="URL to the video with added captions stored in S3."
    )
    path: str = Field(
        description="Storage path of the video with added captions in S3."
    )
    duration: float = Field(
        description="Duration of the output video in seconds."
    )
    width: int = Field(
        description="Width of the output video in pixels."
    )
    height: int = Field(
        description="Height of the output video in pixels."
    )
    srt_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to the SRT subtitle file used (if applicable)."
    )


# FFmpeg Compose Models

class FFmpegOption(BaseModel):
    """FFmpeg option model."""
    option: str = Field(description="The FFmpeg option name (e.g., '-c:v', '-crf')")
    argument: Optional[Union[str, int, float]] = Field(
        default=None, 
        description="The argument for the option (can be string, number, or null)"
    )


class FFmpegInput(BaseModel):
    """FFmpeg input file model."""
    file_url: AnyUrl = Field(description="URL of the input file")
    options: Optional[List[FFmpegOption]] = Field(
        default=[],
        description="List of FFmpeg options specific to this input"
    )


class FFmpegFilter(BaseModel):
    """FFmpeg filter model."""
    filter: str = Field(description="The FFmpeg filter name")
    arguments: Optional[List[str]] = Field(
        default=[],
        description="List of filter arguments"
    )
    input_labels: Optional[List[str]] = Field(
        default=[],
        description="List of input stream labels for this filter"
    )
    output_label: Optional[str] = Field(
        default=None,
        description="Output label for this filter"
    )
    type: Optional[str] = Field(
        default=None,
        description="Filter type: 'video' or 'audio' (for simple filters)"
    )


class FFmpegOutput(BaseModel):
    """FFmpeg output configuration model."""
    options: List[FFmpegOption] = Field(description="List of FFmpeg options for this output")
    stream_mappings: Optional[List[str]] = Field(
        default=[],
        description="List of stream mappings specific to this output"
    )


class FFmpegMetadata(BaseModel):
    """Metadata extraction configuration."""
    thumbnail: Optional[bool] = Field(
        default=False,
        description="Whether to generate a thumbnail for the output"
    )
    filesize: Optional[bool] = Field(
        default=False,
        description="Whether to include file size in the response"
    )
    duration: Optional[bool] = Field(
        default=False,
        description="Whether to include duration in the response"
    )
    bitrate: Optional[bool] = Field(
        default=False,
        description="Whether to include bitrate in the response"
    )
    encoder: Optional[bool] = Field(
        default=False,
        description="Whether to include encoder info in the response"
    )


class FFmpegComposeRequest(BaseModel):
    """FFmpeg compose request model."""
    id: str = Field(description="Unique identifier for the request")
    inputs: List[FFmpegInput] = Field(
        ...,
        min_length=1,
        description="List of input files with their options"
    )
    stream_mappings: Optional[List[str]] = Field(
        default=[],
        description="Global stream mappings that apply to all outputs"
    )
    filters: Optional[List[FFmpegFilter]] = Field(
        default=[],
        description="List of FFmpeg filters to apply"
    )
    use_simple_video_filter: Optional[bool] = Field(
        default=False,
        description="Use -vf for video filters instead of complex filter graph"
    )
    use_simple_audio_filter: Optional[bool] = Field(
        default=False,
        description="Use -af for audio filters instead of complex filter graph"
    )
    outputs: List[FFmpegOutput] = Field(
        ...,
        min_length=1,
        description="List of output configurations"
    )
    global_options: Optional[List[FFmpegOption]] = Field(
        default=[],
        description="Global FFmpeg options"
    )
    metadata: Optional[FFmpegMetadata] = Field(
        default=None,
        description="Metadata extraction configuration"
    )
    webhook_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to send completion webhook"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class FFmpegOutputResult(BaseModel):
    """Result for a single FFmpeg output."""
    file_url: AnyUrl = Field(description="URL of the generated output file")
    thumbnail_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL of the thumbnail if requested"
    )
    filesize: Optional[int] = Field(
        default=None,
        description="File size in bytes if requested"
    )
    duration: Optional[float] = Field(
        default=None,
        description="Duration in seconds if requested"
    )
    bitrate: Optional[int] = Field(
        default=None,
        description="Bitrate in bps if requested"
    )
    encoder: Optional[str] = Field(
        default=None,
        description="Encoder used if requested"
    )


class FFmpegComposeResult(BaseModel):
    """FFmpeg compose operation result."""
    outputs: List[FFmpegOutputResult] = Field(
        description="List of generated output files with metadata"
    )
    command: str = Field(description="The FFmpeg command that was executed")
    processing_time: float = Field(description="Time taken to process in seconds")

class S3UploadRequest(BaseModel):
    """S3 upload request model."""
    file_url: AnyUrl = Field(
        description="URL of the file to upload."
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Custom file name for the downloaded file."
    )
    cookies_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to a Netscape-formatted cookies file for authentication (e.g., for YouTube)."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class CodeExecutionRequest(BaseModel):
    """Code execution request model."""
    code: str = Field(
        description="Python code to execute."
    )
    timeout: Optional[int] = Field(
        default=30,
        description="Execution timeout in seconds."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class MediaDownloadRequest(BaseModel):
    """Enhanced media download request model."""
    url: AnyUrl = Field(
        description="URL of the media to download."
    )
    format: Optional[str] = Field(
        default="best",
        description="Format to download (e.g., 'best', 'mp4', 'mp3', '720p', '480p')."
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Optional custom filename for the downloaded media. If not provided, will use the original filename."
    )
    cookies_url: Optional[str] = Field(
        default=None,
        description="Optional URL to cookies file for authenticated downloads."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    # Enhanced features
    extract_subtitles: bool = Field(
        default=False,
        description="Extract subtitles from the media."
    )
    subtitle_languages: Optional[List[str]] = Field(
        default_factory=lambda: ["en", "auto"],
        description="Subtitle languages to extract."
    )
    subtitle_formats: Optional[List[str]] = Field(
        default_factory=lambda: ["srt", "vtt"],
        description="Subtitle output formats."
    )
    extract_thumbnail: bool = Field(
        default=False,
        description="Extract thumbnail from the media."
    )
    embed_metadata: bool = Field(
        default=True,
        description="Embed metadata in the output file."
    )
    thumbnail_format: Optional[str] = Field(
        default="jpg",
        description="Thumbnail format (jpg, png, webp)."
    )


class YouTubeTranscriptRequest(BaseModel):
    """YouTube transcript request model."""
    video_url: AnyUrl = Field(
        description="YouTube video URL."
    )
    languages: Optional[List[str]] = Field(
        default=None,
        description="Preferred languages for transcripts (e.g., ['en', 'es', 'fr'])."
    )
    translate_to: Optional[str] = Field(
        default=None,
        description="Language code to translate transcript to (e.g., 'en', 'es', 'fr')."
    )
    format: Optional[str] = Field(
        default="text",
        description="Output format for transcript ('text', 'srt', 'vtt', 'json')."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class MediaConversionRequest(BaseModel):
    """Media conversion request model."""
    input_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL of the media file to convert."
    )
    file_data: Optional[str] = Field(
        default=None,
        description="Base64-encoded file data for direct file upload in JSON requests."
    )
    filename: Optional[str] = Field(
        default=None,
        description="Original filename when uploading file data."
    )
    content_type: Optional[str] = Field(
        default=None,
        description="MIME content type of the uploaded file."
    )
    output_format: str = Field(
        description="Target format for conversion (e.g., 'mp3', 'mp4', 'webp')."
    )
    quality: Optional[str] = Field(
        default="medium",
        description="Quality preset for conversion ('low', 'medium', 'high', 'lossless')."
    )
    custom_options: Optional[str] = Field(
        default=None,
        description="Custom FFmpeg options (e.g., '-vf scale=1280:-1')."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )

    @field_validator('file_data')
    @classmethod
    def validate_file_data(cls, v):
        if v is not None:
            try:
                # Validate that it's valid base64
                import base64
                base64.b64decode(v)
            except Exception:
                raise ValueError('file_data must be valid base64-encoded data')
        return v


# New Video Processing Models

class VideoThumbnailsRequest(BaseModel):
    """Video thumbnails generation request model."""
    video_url: AnyUrl = Field(
        description="URL of the video file to generate thumbnails from."
    )
    timestamps: Optional[List[float]] = Field(
        default=None,
        description="Specific timestamps in seconds for thumbnails. If not provided, thumbnails will be auto-generated at optimal points."
    )
    count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of thumbnails to generate (1-20)."
    )
    format: str = Field(
        default="jpg",
        description="Output format: jpg, png, webp."
    )
    quality: Optional[int] = Field(
        default=85,
        ge=1,
        le=100,
        description="Image quality for JPG format (1-100)."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class VideoThumbnailsResult(BaseModel):
    """Video thumbnails generation result model."""
    thumbnail_urls: List[AnyUrl] = Field(
        description="List of URLs to the generated thumbnail images."
    )
    timestamps_used: List[float] = Field(
        description="List of timestamps that were used for thumbnail generation."
    )
    count: int = Field(
        description="Number of thumbnails generated."
    )


class VideoClipSegment(BaseModel):
    """Video clip segment model for extracting specific time ranges."""
    start: float = Field(
        description="Start time in seconds."
    )
    end: float = Field(
        description="End time in seconds."
    )
    name: Optional[str] = Field(
        default=None,
        description="Optional name for the clip segment."
    )


class VideoClipsRequest(BaseModel):
    """Video clips extraction request model."""
    video_url: AnyUrl = Field(
        description="URL of the video file to extract clips from."
    )
    segments: Optional[List[VideoClipSegment]] = Field(
        default=None,
        description="List of segments with start/end times to extract. Optional if using AI search."
    )
    ai_query: Optional[str] = Field(
        default=None,
        description="Natural language query to find relevant clips using AI analysis."
    )
    output_format: str = Field(
        default="mp4",
        description="Output video format."
    )
    quality: Optional[str] = Field(
        default="medium",
        description="Quality preset for output videos."
    )
    max_clips: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of clips to extract when using AI search."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class VideoClipsResult(BaseModel):
    """Video clips extraction result model."""
    clip_urls: List[AnyUrl] = Field(
        description="List of URLs to the generated video clips."
    )
    segments_processed: int = Field(
        description="Number of segments that were successfully processed."
    )
    total_duration: Optional[float] = Field(
        default=None,
        description="Total duration of all extracted clips in seconds."
    )


class VideoFramesRequest(BaseModel):
    """Video frames extraction request model."""
    video_url: AnyUrl = Field(
        description="URL of the video file to extract frames from."
    )
    interval: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Time interval between frames in seconds (0.1-60.0)."
    )
    format: str = Field(
        default="jpg",
        description="Output image format: jpg, png, webp."
    )
    quality: int = Field(
        default=85,
        ge=1,
        le=100,
        description="Image quality for JPG format (1-100)."
    )
    max_frames: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of frames to extract. If not specified, extracts frames for the entire video."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class VideoFramesResult(BaseModel):
    """Video frames extraction result model."""
    frame_urls: List[AnyUrl] = Field(
        description="List of URLs to the extracted frame images."
    )
    total_frames: int = Field(
        description="Total number of frames extracted."
    )
    interval_used: float = Field(
        description="The time interval that was used between frames."
    )
    video_duration: Optional[float] = Field(
        default=None,
        description="Duration of the source video in seconds."
    )


class MusicGenerationRequest(BaseModel):
    """
    Music generation request model for creating music from text descriptions using Meta's MusicGen model.

    This model represents a request to generate music from a text description,
    with control over duration, model size, and output format.
    """
    description: str = Field(
        description="Text description of the music to generate (e.g., 'lo-fi music with a soothing melody')."
    )
    duration: int = Field(
        default=8,
        ge=1,
        le=30,
        description="Duration of the generated music in seconds (1-30)."
    )
    model_size: str = Field(
        default="small",
        description="Model size to use for generation. Options: 'small' (faster, lower quality)."
    )
    output_format: str = Field(
        default="wav",
        description="Output audio format. Options: 'wav', 'mp3'."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class MusicGenerationResult(BaseModel):
    """Music generation result model."""
    audio_url: AnyUrl = Field(
        description="URL to the generated music file."
    )
    duration: float = Field(
        description="Actual duration of the generated music in seconds."
    )
    model_used: str = Field(
        description="The MusicGen model that was used for generation."
    )
    file_size: int = Field(
        description="Size of the generated audio file in bytes."
    )
    sampling_rate: int = Field(
        description="Sampling rate of the generated audio."
    )


# Advanced Text Overlay Models

class TextAnimationOptions(BaseModel):
    """Animation options for text overlays."""
    type: Optional[str] = Field(
        default="none",
        description="Animation type: none, fade_in, fade_out, fade_in_out, slide_up, slide_down, slide_left, slide_right, zoom_in, zoom_out, typewriter, bounce, glow, rainbow, shake"
    )
    duration: Optional[float] = Field(
        default=0.5,
        ge=0.1,
        le=5.0,
        description="Animation duration in seconds"
    )
    delay: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Animation delay in seconds"
    )
    easing: Optional[str] = Field(
        default="ease_out",
        description="Animation easing: linear, ease_in, ease_out, ease_in_out, bounce, elastic"
    )
    intensity: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        le=3.0,
        description="Animation intensity/magnitude (1.0 = normal)"
    )
    loop: Optional[bool] = Field(
        default=False,
        description="Whether to loop the animation"
    )
    reverse: Optional[bool] = Field(
        default=False,
        description="Whether to reverse the animation on completion"
    )


class TextEffectOptions(BaseModel):
    """Advanced text effect options."""
    shadow_enabled: Optional[bool] = Field(
        default=False,
        description="Enable drop shadow effect"
    )
    shadow_color: Optional[str] = Field(
        default="black",
        description="Shadow color (hex or named color)"
    )
    shadow_offset_x: Optional[int] = Field(
        default=3,
        description="Shadow horizontal offset in pixels"
    )
    shadow_offset_y: Optional[int] = Field(
        default=3,
        description="Shadow vertical offset in pixels"
    )
    shadow_blur: Optional[float] = Field(
        default=2.0,
        ge=0.0,
        le=20.0,
        description="Shadow blur radius"
    )
    outline_enabled: Optional[bool] = Field(
        default=True,
        description="Enable text outline/stroke"
    )
    outline_color: Optional[str] = Field(
        default="black",
        description="Outline color (hex or named color)"
    )
    outline_width: Optional[float] = Field(
        default=2.0,
        ge=0.0,
        le=10.0,
        description="Outline width in pixels"
    )
    glow_enabled: Optional[bool] = Field(
        default=False,
        description="Enable glow effect"
    )
    glow_color: Optional[str] = Field(
        default="white",
        description="Glow color (hex or named color)"
    )
    glow_intensity: Optional[float] = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Glow intensity"
    )
    gradient_enabled: Optional[bool] = Field(
        default=False,
        description="Enable gradient text fill"
    )
    gradient_start: Optional[str] = Field(
        default="#FFFFFF",
        description="Gradient start color"
    )
    gradient_end: Optional[str] = Field(
        default="#000000",
        description="Gradient end color"
    )
    gradient_direction: Optional[str] = Field(
        default="vertical",
        description="Gradient direction: vertical, horizontal, diagonal_down, diagonal_up"
    )


class TextPositionOptions(BaseModel):
    """Advanced positioning options for text overlays."""
    preset: Optional[str] = Field(
        default="bottom-center",
        description="Position preset: top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right, custom"
    )
    x_position: Optional[str | int] = Field(
        default=None,
        description="Custom X position (pixels as int, or expression as string like '(w-text_w)/2')"
    )
    y_position: Optional[str | int] = Field(
        default=None,
        description="Custom Y position (pixels as int, or expression as string like '(h-text_h)/2')"
    )
    x_offset: Optional[int] = Field(
        default=0,
        description="Horizontal offset from position in pixels"
    )
    y_offset: Optional[int] = Field(
        default=50,
        description="Vertical offset from position in pixels"
    )
    margin_top: Optional[int] = Field(
        default=150,
        ge=0,
        le=500,
        description="Top margin in pixels (safe area)"
    )
    margin_bottom: Optional[int] = Field(
        default=180,
        ge=0,
        le=500,
        description="Bottom margin in pixels (safe area)"
    )
    margin_left: Optional[int] = Field(
        default=80,
        ge=0,
        le=300,
        description="Left margin in pixels (safe area)"
    )
    margin_right: Optional[int] = Field(
        default=80,
        ge=0,
        le=300,
        description="Right margin in pixels (safe area)"
    )
    face_detection: Optional[bool] = Field(
        default=False,
        description="Use AI face detection to avoid covering faces"
    )
    content_aware: Optional[bool] = Field(
        default=False,
        description="Use content analysis for optimal positioning"
    )


class TextStyleOptions(BaseModel):
    """Advanced text styling options."""
    font_family: Optional[str] = Field(
        default="Arial-Bold",
        description="Font family/file name"
    )
    font_size: Optional[int] = Field(
        default=48,
        ge=8,
        le=200,
        description="Font size in pixels"
    )
    font_weight: Optional[str] = Field(
        default="bold",
        description="Font weight: normal, bold, bolder, lighter, or numeric (100-900)"
    )
    font_style: Optional[str] = Field(
        default="normal",
        description="Font style: normal, italic, oblique"
    )
    text_color: Optional[str] = Field(
        default="white",
        description="Primary text color (hex or named color)"
    )
    text_transform: Optional[str] = Field(
        default="none",
        description="Text transformation: none, uppercase, lowercase, capitalize"
    )
    letter_spacing: Optional[float] = Field(
        default=0.0,
        description="Letter spacing in pixels"
    )
    word_spacing: Optional[float] = Field(
        default=0.0,
        description="Word spacing in pixels"
    )
    line_height: Optional[float] = Field(
        default=1.2,
        ge=0.5,
        le=3.0,
        description="Line height multiplier"
    )
    text_align: Optional[str] = Field(
        default="center",
        description="Text alignment: left, center, right, justify"
    )


class TextLayoutOptions(BaseModel):
    """Text layout and wrapping options."""
    auto_wrap: Optional[bool] = Field(
        default=True,
        description="Enable automatic text wrapping"
    )
    max_width: Optional[int] = Field(
        default=None,
        description="Maximum text width in pixels (auto if None)"
    )
    max_chars_per_line: Optional[int] = Field(
        default=25,
        ge=5,
        le=100,
        description="Maximum characters per line for wrapping"
    )
    max_words_per_line: Optional[int] = Field(
        default=4,
        ge=1,
        le=15,
        description="Maximum words per line for wrapping"
    )
    overflow: Optional[str] = Field(
        default="wrap",
        description="Text overflow handling: wrap, truncate, scroll, scale"
    )
    word_break: Optional[str] = Field(
        default="normal",
        description="Word break behavior: normal, break_all, keep_all"
    )
    hyphenation: Optional[bool] = Field(
        default=False,
        description="Enable automatic hyphenation"
    )


class TextBackgroundOptions(BaseModel):
    """Background styling options for text."""
    enabled: Optional[bool] = Field(
        default=True,
        description="Enable background box/panel"
    )
    type: Optional[str] = Field(
        default="box",
        description="Background type: box, panel, banner, bubble, none"
    )
    color: Optional[str] = Field(
        default="black",
        description="Background color (hex or named color)"
    )
    opacity: Optional[float] = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Background opacity"
    )
    padding: Optional[int] = Field(
        default=20,
        ge=0,
        le=100,
        description="Background padding in pixels"
    )
    border_radius: Optional[int] = Field(
        default=0,
        ge=0,
        le=50,
        description="Background border radius in pixels"
    )
    border_width: Optional[int] = Field(
        default=0,
        ge=0,
        le=10,
        description="Background border width in pixels"
    )
    border_color: Optional[str] = Field(
        default="white",
        description="Background border color"
    )
    blur: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=20.0,
        description="Background blur effect"
    )


class TextOverlayOptions(BaseModel):
    """Comprehensive text overlay styling options."""
    # Timing and visibility
    start_time: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        description="Start time in seconds"
    )
    duration: Optional[float] = Field(
        default=5.0,
        ge=0.1,
        le=999999.0,
        description="Duration in seconds that the text overlay should be visible"
    )
    end_time: Optional[float] = Field(
        default=None,
        description="End time in seconds (alternative to duration)"
    )
    
    # Core styling
    style: Optional[TextStyleOptions] = Field(
        default_factory=TextStyleOptions,
        description="Text styling options"
    )
    positioning: Optional[TextPositionOptions] = Field(
        default_factory=TextPositionOptions,
        description="Advanced text positioning options"
    )
    layout: Optional[TextLayoutOptions] = Field(
        default_factory=TextLayoutOptions,
        description="Text layout and wrapping options"
    )
    background: Optional[TextBackgroundOptions] = Field(
        default_factory=TextBackgroundOptions,
        description="Background styling options"
    )
    effects: Optional[TextEffectOptions] = Field(
        default_factory=TextEffectOptions,
        description="Advanced text effects"
    )
    animation: Optional[TextAnimationOptions] = Field(
        default_factory=TextAnimationOptions,
        description="Animation options"
    )
    
    # Legacy compatibility
    font_size: Optional[int] = Field(
        default=None,
        description="Legacy: Font size (use style.font_size instead)"
    )
    font_color: Optional[str] = Field(
        default=None,
        description="Legacy: Text color (use style.text_color instead)"
    )
    box_color: Optional[str] = Field(
        default=None,
        description="Legacy: Background color (use background.color instead)"
    )
    box_opacity: Optional[float] = Field(
        default=None,
        description="Legacy: Background opacity (use background.opacity instead)"
    )
    boxborderw: Optional[int] = Field(
        default=None,
        description="Legacy: Background padding (use background.padding instead)"
    )
    box_padding: Optional[int] = Field(
        default=None,
        description="Legacy: Background padding alias (same as boxborderw)"
    )
    y_offset: Optional[int] = Field(
        default=None,
        description="Legacy: Y offset (use position.y_offset instead)"
    )
    line_spacing: Optional[int] = Field(
        default=None,
        description="Legacy: Line spacing (use style.line_height instead)"
    )
    auto_wrap: Optional[bool] = Field(
        default=None,
        description="Legacy: Auto wrap text (use layout.auto_wrap instead)"
    )
    max_chars_per_line: Optional[int] = Field(
        default=None,
        description="Legacy: Max characters per line for wrapping"
    )
    position: Optional[str] = Field(
        default=None,
        description="Legacy: Position string like 'top-center', 'bottom-center' (use position.preset instead)"
    )


class TextOverlayRequest(BaseModel):
    """
    Text overlay request model for adding text to videos.

    This model represents a request to overlay text onto a video with customizable
    styling options including position, colors, fonts, and background styling.
    """
    video_url: AnyUrl = Field(
        description="URL of the video to add text overlay to."
    )
    text: str = Field(
        min_length=1,
        max_length=500,
        description="Text content to overlay on the video."
    )
    options: TextOverlayOptions = Field(
        description="Styling and positioning options for the text overlay."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


# AI Script Generation Models

class AIScriptGenerationRequest(BaseModel):
    """
    AI script generation request model for creating video scripts from topics.
    
    This model represents a request to generate a script for YouTube Shorts
    or similar short-form video content using AI language models.
    """
    topic: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="The topic or theme for script generation (e.g., 'weird facts', 'space exploration', 'cooking tips'). Optional if auto_topic is True."
    )
    auto_topic: Optional[bool] = Field(
        default=False,
        description="When True, automatically discovers trending topics based on script_type using web search. If True, topic parameter is optional."
    )
    provider: Optional[str] = Field(
        default="auto",
        description="AI provider to use: 'openai' (GPT-4o), 'groq' (Mixtral-8x7b), or 'auto' (automatically selects based on API key availability)."
    )
    script_type: Optional[str] = Field(
        default="facts",
        description="Type of script to generate: 'facts', 'story', 'educational', 'motivation', 'prayer', 'pov', 'conspiracy', 'life_hacks', 'would_you_rather', 'before_you_die', 'dark_psychology', 'reddit_stories', 'shower_thoughts', 'life_wisdom', 'daily_news'."
    )
    max_duration: Optional[int] = Field(
        default=60,
        ge=5,
        le=900,
        description="Maximum duration in seconds for the target video (5-900 seconds = 15 minutes). Affects script length."
    )
    target_words: Optional[int] = Field(
        default=200,
        ge=50,
        le=2500,
        description="Target word count for the script (50-2500 words). Generally 2.8 words per second, so 2500 words ≈ 15 minutes."
    )
    language: Optional[str] = Field(
        default="english",
        description="Language for the generated script. Supported languages: 'english', 'spanish', 'french', 'german', 'italian', 'portuguese', 'russian', 'chinese', 'japanese', 'korean', 'hindi', 'arabic', 'dutch', 'swedish', 'norwegian', 'danish', 'finnish', 'polish', 'czech', 'hungarian', 'romanian', 'turkish', 'greek', 'hebrew', 'thai', 'vietnamese', 'indonesian', 'malay', 'filipino', 'swahili'."
    )


class AIScriptGenerationResult(BaseModel):
    """AI script generation result model."""
    script: str = Field(
        description="The generated script text."
    )
    word_count: int = Field(
        description="Number of words in the generated script."
    )
    estimated_duration: float = Field(
        description="Estimated duration in seconds (based on average speaking rate)."
    )
    provider_used: str = Field(
        description="The AI provider that was used for generation."
    )
    model_used: str = Field(
        description="The specific AI model that was used."
    )


# Video Search Query Generation Models

class VideoSearchQueryRequest(BaseModel):
    """
    Video search query generation request for creating visual search terms from script content.

    This model represents a request to generate visually concrete search queries
    that can be used to find relevant stock videos for each part of a script.
    """
    script: str = Field(
        min_length=1,
        description="The script text to analyze and generate video search queries for (will be truncated to 10000 characters if longer)."
    )
    
    @field_validator('script')
    @classmethod
    def truncate_script(cls, v):
        """Truncate script to max 10000 characters instead of rejecting."""
        if v and len(v) > 10000:
            return v[:10000]
        return v
    segment_duration: Optional[float] = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Target duration in seconds for each video segment (1.0-10.0 seconds)."
    )
    provider: Optional[str] = Field(
        default="auto",
        description="AI provider to use: 'openai' (GPT-4o), 'groq' (Llama3-70b), or 'auto'."
    )
    language: Optional[str] = Field(
        default="en",
        description="Language code for the search queries (e.g., 'en', 'es', 'fr')."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class VideoSearchQuery(BaseModel):
    """Individual video search query with timing information."""
    query: str = Field(
        description="The search query for finding relevant stock video."
    )
    start_time: float = Field(
        description="Start time in seconds for when this video should appear."
    )
    end_time: float = Field(
        description="End time in seconds for when this video should end."
    )
    duration: float = Field(
        description="Duration in seconds for this video segment."
    )
    visual_concept: str = Field(
        description="Description of the visual concept being searched for."
    )


class VideoSearchQueryResult(BaseModel):
    """Video search query generation result model."""
    queries: List[VideoSearchQuery] = Field(
        description="List of video search queries with timing information."
    )
    total_duration: float = Field(
        description="Total duration covered by all video segments."
    )
    total_segments: int = Field(
        description="Number of video segments generated."
    )
    provider_used: str = Field(
        description="The AI provider that was used for generation."
    )


# Stock Video Search Models

class StockVideoSearchRequest(BaseModel):
    """
    Stock video search request for finding videos from Pexels API.
    
    This model represents a request to search for stock videos using the Pexels API
    based on search queries and filtering criteria.
    """
    query: str = Field(
        min_length=1,
        max_length=100,
        description="Search query for finding stock videos (e.g., 'ocean waves', 'city skyline')."
    )
    per_page: Optional[int] = Field(
        default=15,
        ge=1,
        le=80,
        description="Number of videos to return per search (1-80)."
    )
    min_duration: Optional[int] = Field(
        default=5,
        ge=1,
        le=60,
        description="Minimum video duration in seconds."
    )
    max_duration: Optional[int] = Field(
        default=60,
        ge=1,
        le=900,
        description="Maximum video duration in seconds (up to 15 minutes)."
    )
    orientation: Optional[str] = Field(
        default="landscape",
        description="Video orientation: 'landscape' (16:9), 'portrait' (9:16), or 'square' (1:1)."
    )
    size: Optional[str] = Field(
        default="large",
        description="Video size preference: 'large' (HD), 'medium', or 'small'."
    )


class StockVideo(BaseModel):
    """Individual stock video result."""
    id: int = Field(
        description="Pexels video ID."
    )
    url: str = Field(
        description="URL to the video on Pexels."
    )
    download_url: str = Field(
        description="Direct download URL for the video file."
    )
    duration: int = Field(
        description="Video duration in seconds."
    )
    width: int = Field(
        description="Video width in pixels."
    )
    height: int = Field(
        description="Video height in pixels."
    )
    file_size: Optional[int] = Field(
        default=None,
        description="File size in bytes (if available)."
    )
    quality: str = Field(
        description="Video quality (e.g., 'hd', 'sd')."
    )
    file_type: str = Field(
        description="Video file format (e.g., 'mp4')."
    )
    tags: List[str] = Field(
        default=[],
        description="Tags associated with the video."
    )


class StockVideoSearchResult(BaseModel):
    """Stock video search result model."""
    videos: List[StockVideo] = Field(
        description="List of found stock videos."
    )
    total_results: int = Field(
        description="Total number of videos found for the query."
    )
    page: int = Field(
        description="Current page number."
    )
    per_page: int = Field(
        description="Number of results per page."
    )
    query_used: str = Field(
        description="The search query that was used."
    )


# Topic to Video Pipeline Models

class FootageToVideoRequest(BaseModel):
    """
    End-to-end footage to video generation request.

    This model represents a complete pipeline request that takes a topic and
    automatically generates a script, finds background videos, creates TTS audio,
    adds captions, and renders the final video.
    """
    topic: Optional[str] = Field(
        default=None,
        description="The topic for video generation (e.g., 'amazing ocean facts'). Optional if auto_topic is True or custom_script is provided."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    
    @field_validator('topic')
    @classmethod
    def validate_topic_length(cls, v):
        """Validate topic length only if provided."""
        if v is not None and len(v.strip()) == 0:
            return None  # Convert empty strings to None
        if v is not None and len(v.strip()) > 200:
            raise ValueError("Topic must be 200 characters or less")
        return v
    custom_script: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Custom script text to use instead of generating from topic. When provided, script generation is skipped. Long scripts will be truncated to 10000 characters."
    )
    
    @field_validator('custom_script')
    @classmethod
    def truncate_custom_script(cls, v):
        """Truncate custom script to max 10000 characters instead of rejecting."""
        if v and len(v) > 10000:
            return v[:10000]
        return v
    auto_topic: Optional[bool] = Field(
        default=False,
        description="When True, automatically discovers trending topics based on script_type using web search. If True, topic parameter is optional."
    )
    language: Optional[str] = Field(
        default="en",
        description="Language for script generation and TTS. Use language codes like 'en', 'fr', 'es', 'de', etc."
    )
    
    # Script generation options
    script_provider: Optional[str] = Field(
        default="auto",
        description="AI provider for script generation: 'openai', 'groq', 'auto', or 'manual'."
    )
    script_type: Optional[str] = Field(
        default="facts",
        description="Type of script: 'facts', 'story', 'educational', 'motivation', 'prayer', 'pov', 'conspiracy', 'life_hacks', 'would_you_rather', 'before_you_die', 'dark_psychology', 'reddit_stories', 'shower_thoughts', 'life_wisdom', 'daily_news'."
    )
    max_duration: Optional[int] = Field(
        default=50,
        ge=5,
        le=900,
        description="Maximum video duration in seconds (5 seconds to 15 minutes)."
    )
    
    # TTS options
    voice: Optional[str] = Field(
        default="af_alloy",
        description="Voice for text-to-speech narration."
    )
    tts_provider: Optional[str] = Field(
        default=None,
        description="TTS provider: 'kokoro' or 'edge'."
    )
    tts_speed: Optional[float] = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed multiplier."
    )
    enable_voice_over: Optional[bool] = Field(
        default=True,
        description="Enable voice-over narration in the video."
    )
    enable_built_in_audio: Optional[bool] = Field(
        default=False,
        description="Enable built-in audio from AI video models (e.g., ambient sounds from VEO)."
    )
    
    # Video search options
    video_orientation: Optional[str] = Field(
        default="landscape",
        description="Video orientation: 'landscape', 'portrait', or 'square'."
    )
    segment_duration: Optional[float] = Field(
        default=3.0,
        ge=2.0,
        le=8.0,
        description="Target duration for each background video segment."
    )
    
    # Footage provider options
    footage_provider: Optional[str] = Field(
        default="pexels",
        description="Video footage provider for background clips: 'pexels', 'unsplash', 'pixabay', 'ai_generated'."
    )
    search_safety: Optional[str] = Field(
        default="moderate",
        description="Content safety filter level: 'strict', 'moderate', 'off'."
    )
    footage_quality: Optional[str] = Field(
        default="high",
        description="Background footage quality preference: 'standard', 'high', 'ultra'."
    )
    search_terms_per_scene: Optional[int] = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of search terms to generate per video segment."
    )
    
    # Background music options
    background_music: Optional[str] = Field(
        default="none",
        description="Background music option: 'none' for no music, 'ai_generate' for AI-generated music, or a mood name like 'chill', 'happy', 'dark' for stock music with that mood."
    )
    background_music_volume: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Background music volume level (0.0 to 1.0)."
    )
    music_duration: Optional[int] = Field(
        default=None,
        ge=10,
        le=900,
        description="Maximum duration for background music in seconds. If not specified, uses video duration."
    )
    
    # Caption options
    add_captions: Optional[bool] = Field(
        default=True,
        description="Whether to add captions to the video."
    )
    caption_style: Optional[str] = Field(
        default="viral_bounce",
        description="Caption style: 'classic', 'viral_bounce', 'viral_cyan', 'viral_yellow', 'viral_green', 'bounce', 'typewriter', 'fade_in', 'highlight', 'underline', 'word_by_word', 'modern_neon', 'cinematic_glow', 'social_pop'."
    )
    caption_color: Optional[str] = Field(
        default=None,
        description="Base text color for captions (e.g., '#FFFFFF'). When specified, overrides the style default."
    )
    highlight_color: Optional[str] = Field(
        default=None,
        description="Highlighted word color for karaoke/highlight styles (e.g., '#FFFF00', '#00FFFF')."
    )
    caption_position: Optional[str] = Field(
        default=None,
        description="Caption position on video: 'top_left', 'top_center', 'top_right', 'middle_left', 'middle_center', 'middle_right', 'bottom_left', 'bottom_center', 'bottom_right', or shorthand 'top', 'center', 'bottom'."
    )
    font_size: Optional[int] = Field(
        default=None,
        ge=8,
        le=200,
        description="Font size for captions in pixels."
    )
    font_family: Optional[str] = Field(
        default=None,
        description="Font family for captions (e.g., 'Arial', 'Arial-Bold', 'Helvetica')."
    )
    words_per_line: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Maximum number of words per caption line."
    )
    margin_v: Optional[int] = Field(
        default=None,
        ge=0,
        le=500,
        description="Vertical margin for captions in pixels from top/bottom edge."
    )
    outline_width: Optional[int] = Field(
        default=None,
        ge=0,
        le=20,
        description="Width of caption text outline/border in pixels."
    )
    all_caps: Optional[bool] = Field(
        default=None,
        description="Convert all caption text to uppercase."
    )
    caption_properties: Optional[VideoCaptionProperties] = Field(
        default=None,
        description="Advanced caption styling options."
    )
    
    # Output options
    output_width: Optional[int] = Field(
        default=None,
        description="Output video width in pixels. If not specified, determined by video_orientation."
    )
    output_height: Optional[int] = Field(
        default=None,
        description="Output video height in pixels. If not specified, determined by video_orientation."
    )
    frame_rate: Optional[int] = Field(
        default=30,
        ge=24,
        le=60,
        description="Output video frame rate."
    )
    
    # Additional frontend compatibility fields
    fps: Optional[int] = Field(
        default=None,
        ge=24,
        le=60,
        description="Frame rate (alias for frame_rate, for frontend compatibility)."
    )
    orientation: Optional[str] = Field(
        default=None,
        description="Video orientation (alias for video_orientation, for frontend compatibility)."
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Video resolution string (e.g., '1080x1920'). Will be parsed to set output_width and output_height."
    )
    ai_video_provider: Optional[str] = Field(
        default="modal_video",
        description="AI video provider to use when footage_provider is 'ai_generated': 'modal_video', 'wavespeed', 'comfyui'."
    )
    media_type: Optional[str] = Field(
        default="video",
        description="Media type to use for background content: 'video' (stock videos) or 'image' (stock images converted to videos)."
    )
    
    # Motion effects options (for image-to-video conversion)
    effect_type: Optional[str] = Field(
        default="zoom",
        description="Video effect type for image-to-video conversion: 'none', 'zoom', 'pan', 'ken_burns', 'fade', 'slide'. Use 'none' for static images without motion effects."
    )
    zoom_speed: Optional[int] = Field(
        default=25,
        ge=1,
        le=100,
        description="Zoom speed for zoom effect (1-100). Lower values create slower, more subtle zoom effects."
    )
    pan_direction: Optional[str] = Field(
        default=None,
        description="Direction of pan effect when effect_type is 'pan'. Options: 'left_to_right', 'right_to_left', 'top_to_bottom', 'bottom_to_top', 'diagonal_top_left', 'diagonal_top_right', 'diagonal_bottom_left', 'diagonal_bottom_right'."
    )
    ken_burns_keypoints: Optional[List[Dict[str, float]]] = Field(
        default=None,
        description="List of keypoints for Ken Burns effect when effect_type is 'ken_burns'. Each keypoint is a dictionary with 'time' (in seconds), 'x' (0-1), 'y' (0-1), and 'zoom' (scale factor) values. At least 2 keypoints should be provided."
    )
    
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """Handle Pydantic v2 initialization."""
        super().__pydantic_init_subclass__(**kwargs)
    
    def __init__(self, **data):
        """Custom initialization to handle frontend compatibility fields."""
        # Handle fps -> frame_rate compatibility
        if 'fps' in data and 'frame_rate' not in data:
            data['frame_rate'] = data['fps']
        
        # Handle orientation -> video_orientation compatibility  
        if 'orientation' in data and 'video_orientation' not in data:
            data['video_orientation'] = data['orientation']
            
            
        # Handle resolution string parsing
        if 'resolution' in data and data['resolution'] is not None:
            resolution = data['resolution']
            if 'x' in resolution:
                try:
                    width, height = resolution.split('x')
                    if 'output_width' not in data:
                        data['output_width'] = int(width)
                    if 'output_height' not in data:
                        data['output_height'] = int(height)
                        
                    # Auto-detect video_orientation from resolution if not set
                    if 'video_orientation' not in data:
                        width_val, height_val = int(width), int(height)
                        if height_val > width_val:
                            data['video_orientation'] = "portrait"
                        elif width_val > height_val:
                            data['video_orientation'] = "landscape"
                        else:
                            data['video_orientation'] = "square"
                except (ValueError, IndexError):
                    pass  # Ignore invalid resolution strings
        
        super().__init__(**data)


class FootageToVideoResult(BaseModel):
    """Footage to video generation result model."""
    final_video_url: AnyUrl = Field(
        description="URL to the final generated video with captions."
    )
    video_with_audio_url: AnyUrl = Field(
        description="URL to the video with audio but without captions."
    )
    script_generated: str = Field(
        description="The generated script text."
    )
    audio_url: AnyUrl = Field(
        description="URL to the TTS audio file."
    )
    background_videos_used: List[str] = Field(
        description="List of background video URLs that were used."
    )
    srt_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to the SRT caption file (if captions were added)."
    )
    video_duration: float = Field(
        description="Duration of the final video in seconds."
    )
    processing_time: float = Field(
        description="Total processing time in seconds."
    )
    word_count: int = Field(
        description="Word count of the generated script."
    )
    segments_count: int = Field(
        description="Number of background video segments used."
    )


class AiimageToVideoRequest(BaseModel):
    """
    Script-to-video generation request using AI-generated images.

    This model represents a complete pipeline that takes a topic, generates a script,
    creates AI images for each segment, and composes them into a video with narration.
    Similar to footage-to-video but uses AI-generated images instead of stock videos.
    """
    topic: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="The topic for video generation (e.g., 'amazing ocean facts'). Optional if auto_topic is True."
    )
    auto_topic: Optional[bool] = Field(
        default=False,
        description="When True, automatically discovers trending topics based on script_type using web search. If True, topic parameter is optional."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    language: Optional[str] = Field(
        default="en",
        description="Language for script generation and TTS. Use language codes like 'en', 'fr', 'es', 'de', etc."
    )
    
    # Script generation options
    script_provider: Optional[str] = Field(
        default="auto",
        description="AI provider for script generation: 'openai', 'groq', or 'auto'."
    )
    script_type: Optional[str] = Field(
        default="facts",
        description="Type of script: 'facts', 'story', 'educational', 'motivation', 'prayer', 'pov', 'conspiracy', 'life_hacks', 'would_you_rather', 'before_you_die', 'dark_psychology', 'reddit_stories', 'shower_thoughts', 'life_wisdom', 'daily_news'."
    )
    max_duration: Optional[int] = Field(
        default=50,
        ge=5,
        le=900,
        description="Maximum video duration in seconds (5 seconds to 15 minutes)."
    )
    
    # TTS options
    voice: Optional[str] = Field(
        default="af_alloy",
        description="Voice for text-to-speech narration."
    )
    tts_provider: Optional[str] = Field(
        default=None,
        description="TTS provider: 'kokoro' or 'edge'."
    )
    tts_speed: Optional[float] = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed multiplier."
    )
    
    # Image generation options
    image_provider: Optional[str] = Field(
        default="together",
        description="Image generation provider: 'together' (FLUX.1 Schnell), 'modal_image' (Modal Image Dev), or 'pollinations' (Pollinations.AI with multiple models)."
    )
    image_model: Optional[str] = Field(
        default=None,
        description="Image generation model to use. If not specified, uses TOGETHER_DEFAULT_MODEL environment variable or black-forest-labs/FLUX.1-schnell."
    )
    image_width: Optional[int] = Field(
        default=None,
        ge=256,
        le=2048,
        description="Generated image width in pixels. If not specified, uses TOGETHER_DEFAULT_WIDTH environment variable or 576."
    )
    image_height: Optional[int] = Field(
        default=None,
        ge=256,
        le=2048,
        description="Generated image height in pixels. If not specified, uses TOGETHER_DEFAULT_HEIGHT environment variable or 1024."
    )
    image_steps: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Number of inference steps for image generation. If not specified, uses TOGETHER_DEFAULT_STEPS environment variable or 4."
    )
    guidance_scale: Optional[float] = Field(
        default=3.5,
        ge=1.0,
        le=20.0,
        description="Guidance scale for Flux image generation (how closely to follow the prompt). Only used when image_provider is 'modal_image'."
    )
    
    # Video effects options
    effect_type: Optional[str] = Field(
        default="zoom",
        description="Video effect type: 'zoom', 'pan', 'fade', 'ken_burns', 'slide'."
    )
    zoom_speed: Optional[int] = Field(
        default=25,
        ge=1,
        le=100,
        description="Zoom speed for zoom effect (1-100)."
    )
    frame_rate: Optional[int] = Field(
        default=50,
        ge=24,
        le=60,
        description="Video frame rate."
    )
    segment_duration: Optional[float] = Field(
        default=3.0,
        ge=2.0,
        le=8.0,
        description="Target duration for each generated video segment."
    )
    
    # Music generation options
    generate_background_music: Optional[bool] = Field(
        default=False,
        description="Whether to generate AI background music for the video. If false, uses background_music for mood-based stock music."
    )
    background_music: Optional[str] = Field(
        default="none",
        description="Background music option: 'none' for no music, 'ai_generate' for AI-generated music, or a mood name like 'chill', 'happy', 'dark' for stock music with that mood."
    )
    music_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt for background music generation. If not provided, AI will generate one."
    )
    music_duration: Optional[int] = Field(
        default=None,
        ge=5,
        le=900,
        description="Duration for background music in seconds (5-900s / 15 minutes). If not provided, matches video duration."
    )
    background_music_volume: Optional[float] = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Volume level for background music (0.0 to 1.0)."
    )
    
    # Caption options
    add_captions: Optional[bool] = Field(
        default=True,
        description="Whether to add captions to the video."
    )
    caption_style: Optional[str] = Field(
        default="viral_bounce",
        description="Caption style: 'classic', 'viral_bounce', 'viral_cyan', 'viral_yellow', 'viral_green', 'bounce', 'typewriter', 'fade_in', 'highlight', 'underline', 'word_by_word', 'modern_neon', 'cinematic_glow', 'social_pop'."
    )
    caption_color: Optional[str] = Field(
        default=None,
        description="Color for caption highlighting in viral styles (e.g., '#00FFFF', '#FFFF00', '#00FF00'). When specified, overrides the default color for viral caption styles."
    )
    caption_position: Optional[str] = Field(
        default=None,
        description="Caption position on video: 'top', 'center', 'bottom'. Controls vertical positioning of caption text."
    )
    caption_properties: Optional[VideoCaptionProperties] = Field(
        default=None,
        description="Advanced caption styling options."
    )
    
    # Output options
    video_orientation: Optional[str] = Field(
        default="portrait",
        description="Video orientation: 'landscape', 'portrait', or 'square'."
    )
    output_width: Optional[int] = Field(
        default=None,
        description="Output video width in pixels. If not specified, determined by video_orientation."
    )
    output_height: Optional[int] = Field(
        default=None,
        description="Output video height in pixels. If not specified, determined by video_orientation."
    )


class AiimageToVideoResult(BaseModel):
    """Script-to-video generation result model."""
    final_video_url: AnyUrl = Field(
        description="URL to the final generated video with captions."
    )
    video_with_audio_url: AnyUrl = Field(
        description="URL to the video with audio but without captions."
    )
    script_generated: str = Field(
        description="The generated script text."
    )
    audio_url: AnyUrl = Field(
        description="URL to the TTS audio file."
    )
    generated_images: List[Dict[str, Any]] = Field(
        description="List of generated images with their prompts and URLs."
    )
    background_music_url: Optional[str] = Field(
        default=None,
        description="URL to the generated background music (if requested)."
    )
    music_prompt_generated: Optional[str] = Field(
        default=None,
        description="The AI-generated music prompt used."
    )
    srt_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to the SRT caption file (if captions were added)."
    )
    video_duration: float = Field(
        description="Duration of the final video in seconds."
    )
    processing_time: float = Field(
        description="Total processing time in seconds."
    )
    word_count: int = Field(
        description="Word count of the generated script."
    )
    segments_count: int = Field(
        description="Number of image/video segments used."
    )
    segments_data: List[Dict[str, Any]] = Field(
        description="Detailed information about each transcribed segment."
    )


# Media Silence Detection Models

class MediaSilenceRequest(BaseModel):
    """
    Media silence/speech detection request model.

    This model represents a request for silence and speech detection in media files
    with advanced Voice Activity Detection (VAD) support.
    """
    media_url: AnyUrl = Field(
        description="URL of the media file to analyze for silence/speech detection."
    )
    start: Optional[str] = Field(
        default=None,
        description="Start time in HH:MM:SS format for analysis (legacy parameter)."
    )
    end: Optional[str] = Field(
        default=None,
        description="End time in HH:MM:SS format for analysis (legacy parameter)."
    )
    noise: Optional[str] = Field(
        default="-30dB",
        pattern=r'^-?\d+(\.\d+)?dB$',
        description="Noise threshold for FFmpeg silence detection (e.g., '-30dB')."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    duration: Optional[float] = Field(
        default=0.5,
        ge=0.1,
        description="Minimum duration for silence/speech segments in seconds."
    )
    mono: Optional[bool] = Field(
        default=True,
        description="Convert audio to mono for legacy FFmpeg detection."
    )
    volume_threshold: Optional[float] = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Volume threshold percentage for advanced VAD (0-100)."
    )
    use_advanced_vad: Optional[bool] = Field(
        default=True,
        description="Use advanced Voice Activity Detection instead of FFmpeg silence detection."
    )
    min_speech_duration: Optional[float] = Field(
        default=0.5,
        ge=0.1,
        description="Minimum speech segment duration in seconds for VAD."
    )
    speech_padding_ms: Optional[int] = Field(
        default=50,
        ge=0,
        description="Padding around speech segments in milliseconds."
    )
    silence_padding_ms: Optional[int] = Field(
        default=450,
        ge=0,
        description="Maximum silence gap to merge segments in milliseconds."
    )


class MediaSilenceResult(BaseModel):
    """Media silence detection result model."""
    type: str = Field(
        description="Type of detection result: 'speech_segments' or 'silence_intervals'."
    )
    method: str = Field(
        description="Detection method used: 'advanced_vad' or 'ffmpeg_silencedetect'."
    )
    segments: List[Dict[str, Any]] = Field(
        description="List of detected segments with timing information."
    )
    total_segments: int = Field(
        description="Total number of segments detected."
    )
    parameters: Dict[str, Any] = Field(
        description="Parameters used for detection."
    )


class MediaAnalyzeRequest(BaseModel):
    """
    Media audio analysis request model.

    This model represents a request to analyze audio characteristics
    and recommend optimal processing parameters.
    """
    media_url: AnyUrl = Field(
        description="URL of the media file to analyze."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class MediaAnalyzeResult(BaseModel):
    """Media audio analysis result model."""
    duration: float = Field(
        description="Duration of the audio in seconds."
    )
    sample_rate: int = Field(
        description="Audio sample rate in Hz."
    )
    rms_level: float = Field(
        description="Root Mean Square level of the audio."
    )
    noise_floor_db: float = Field(
        description="Estimated noise floor in decibels."
    )
    speech_level_db: float = Field(
        description="Estimated speech level in decibels."
    )
    dynamic_range_db: float = Field(
        description="Dynamic range between noise floor and speech level."
    )
    zero_crossing_rate: float = Field(
        description="Average zero crossing rate (speech characteristic)."
    )
    spectral_centroid_hz: float = Field(
        description="Average spectral centroid in Hz."
    )
    recommended_volume_threshold: int = Field(
        description="Recommended volume threshold for silence detection."
    )
    audio_quality: str = Field(
        description="Assessed audio quality: 'high', 'medium', or 'low'."
    )


class YouTubeShortsRequest(BaseModel):
    """YouTube Shorts generation request model."""
    video_url: str = Field(
        description="YouTube video URL to generate shorts from."
    )
    max_duration: Optional[int] = Field(
        default=60,
        description="Maximum duration for the short in seconds (default: 60)."
    )
    quality: Optional[str] = Field(
        default="medium",
        description="Video quality for download (low, medium, high)."
    )
    crop_to_vertical: Optional[bool] = Field(
        default=True,
        description="Whether to crop the video to vertical (9:16) format."
    )
    use_ai_highlight: Optional[bool] = Field(
        default=True,
        description="Whether to use AI to detect the best highlight segment."
    )
    custom_start_time: Optional[float] = Field(
        default=None,
        description="Custom start time in seconds (overrides AI highlight detection)."
    )
    custom_end_time: Optional[float] = Field(
        default=None,
        description="Custom end time in seconds (overrides AI highlight detection)."
    )
    output_format: Optional[str] = Field(
        default="mp4",
        description="Output video format (mp4, webm, mov)."
    )


class YouTubeShortsResult(BaseModel):
    """YouTube Shorts generation result model."""
    url: str = Field(
        description="S3 URL of the generated short video."
    )
    path: str = Field(
        description="S3 path of the generated short video."
    )
    duration: float = Field(
        description="Duration of the generated short in seconds."
    )
    original_title: str = Field(
        description="Title of the original YouTube video."
    )
    highlight_start: float = Field(
        description="Start time of the highlighted segment in seconds."
    )
    highlight_end: float = Field(
        description="End time of the highlighted segment in seconds."
    )
    is_vertical: bool = Field(
        description="Whether the video was cropped to vertical format."
    )
    ai_generated: bool = Field(
        description="Whether AI was used to select the highlight."
    )


# Document processing models
class DocumentToMarkdownRequest(BaseModel):
    """
    Document to Markdown conversion request model.

    This model represents a request to convert various document formats
    (PDF, Word, Excel, PowerPoint, etc.) to Markdown format using MarkItDown.
    """
    file_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL of the document file to convert (alternative to file upload)."
    )
    output_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional output formatting options for MarkItDown conversion."
    )
    include_metadata: Optional[bool] = Field(
        default=True,
        description="Whether to include document metadata in the output."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    preserve_formatting: Optional[bool] = Field(
        default=True,
        description="Whether to preserve document formatting like tables, lists, and headers."
    )
    cookies_url: Optional[str] = Field(
        default=None,
        description="URL to download cookies file for YouTube/restricted content access (required for YouTube videos on server environments)."
    )


class DocumentToMarkdownResult(BaseModel):
    """Document to Markdown conversion result model."""
    markdown_content: str = Field(
        description="The converted document content in Markdown format."
    )
    original_filename: str = Field(
        description="Original filename of the converted document."
    )
    file_type: str = Field(
        description="Detected file type of the original document."
    )
    word_count: int = Field(
        description="Number of words in the converted content."
    )
    character_count: int = Field(
        description="Number of characters in the converted content."
    )
    processing_time: float = Field(
        description="Time taken to process the document in seconds."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Document metadata if available and requested."
    )


# Langextract (AI data extraction) models
class LangextractRequest(BaseModel):
    """
    Langextract AI-powered data extraction request model.
    
    This model represents a request to extract structured information from
    unstructured text using Google Langextract with LLM-powered analysis.
    """
    input_text: Optional[str] = Field(
        default=None,
        description="Direct text input for data extraction (alternative to file/URL)."
    )
    file_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL of the document file to extract data from (alternative to text/file upload)."
    )
    extraction_schema: Optional[str] = Field(
        default='{"entities": ["person", "organization", "location"], "relationships": ["works_for", "located_in"]}',
        description="JSON schema defining what entities, relationships, and attributes to extract."
    )
    extraction_prompt: Optional[str] = Field(
        default="Extract all people, organizations, and locations from the text. Also identify relationships between entities.",
        description="Custom prompt describing what specific information to extract."
    )
    use_custom_prompt: Optional[bool] = Field(
        default=False,
        description="Whether to use custom extraction prompt (True) or JSON schema (False)."
    )
    model: Optional[str] = Field(
        default="gemini",
        description="AI model to use for extraction: 'gemini' (primary) or 'openai' (fallback)."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class ExtractedEntity(BaseModel):
    """Single extracted entity with source grounding."""
    value: str = Field(
        description="The extracted entity value or text."
    )
    sources: List[Dict[str, Any]] = Field(
        description="Source grounding information showing exact text locations."
    )


class LangextractResult(BaseModel):
    """
    Langextract AI data extraction result model.
    
    Contains structured extracted data with source grounding information
    showing exactly where each piece of information was found in the text.
    """
    extracted_data: Dict[str, List[ExtractedEntity]] = Field(
        description="Extracted structured data organized by entity type or category."
    )
    total_extractions: int = Field(
        description="Total number of data points extracted from the text."
    )
    processing_time: float = Field(
        description="Time taken to extract data in seconds."
    )
    model_used: str = Field(
        description="AI model that was used for the extraction (gemini/openai)."
    )
    input_text_length: int = Field(
        description="Length of the input text that was processed."
    )
    input_filename: str = Field(
        description="Original filename or source identifier."
    )
    extraction_type: str = Field(
        description="Type of extraction used: 'schema_based' or 'custom_prompt'."
    )
    source_grounding_enabled: bool = Field(
        description="Whether source grounding (text location mapping) was enabled."
    )
    timestamp: str = Field(
        description="ISO timestamp when the extraction was completed."
    )
    s3_results_key: Optional[str] = Field(
        default=None,
        description="S3 key where detailed results are stored."
    )
    s3_source_key: Optional[str] = Field(
        default=None,
        description="S3 key where original source text is stored."
    )


# Scenes to Video Models

class SceneItem(BaseModel):
    """Individual scene item for scenes-to-video creation."""
    text: str = Field(
        min_length=1,
        max_length=500,
        description="Text content for this scene segment."
    )
    searchTerms: List[str] = Field(
        min_length=1,
        max_length=10,
        description="Search terms for finding background video for this scene."
    )
    duration: Optional[float] = Field(
        default=None,
        ge=1.0,
        le=15.0,
        description="Optional duration for this scene in seconds. If not specified, calculated from TTS timing."
    )


class ScenesVideoConfig(BaseModel):
    """Configuration for scenes-to-video creation."""
    voice: Optional[str] = Field(
        default="af_heart",
        description="Voice to use for TTS narration."
    )
    provider: Optional[str] = Field(
        default="kokoro",
        description="TTS provider: 'kokoro' or 'edge'."
    )
    music: Optional[str] = Field(
        default="chill",
        description="Background music mood or style."
    )
    captionPosition: Optional[str] = Field(
        default="bottom",
        description="Caption position: 'top', 'center', 'bottom'."
    )
    orientation: Optional[str] = Field(
        default="portrait",
        description="Video orientation: 'portrait' (9:16), 'landscape' (16:9), or 'square' (1:1)."
    )
    musicVolume: Optional[str] = Field(
        default="medium",
        description="Background music volume: 'low', 'medium', 'high'."
    )
    paddingBack: Optional[int] = Field(
        default=1500,
        ge=0,
        le=5000,
        description="Padding in milliseconds to add after the video."
    )
    resolution: Optional[str] = Field(
        default="1080x1920",
        description="Video resolution (e.g., '1080x1920', '1920x1080', '1080x1080')."
    )
    captionStyle: Optional[str] = Field(
        default="viral_bounce",
        description="Caption style: 'classic', 'viral_bounce', 'viral_cyan', 'viral_yellow', 'viral_green', 'bounce', 'typewriter', 'fade_in'."
    )
    captionColor: Optional[str] = Field(
        default=None,
        description="Caption color override (e.g., '#00FFFF', '#FFFF00')."
    )
    language: Optional[str] = Field(
        default="en",
        description="Language code for TTS and captions."
    )


class ScenesVideoRequest(BaseModel):
    """
    Scenes-to-video creation request model matching external API format.

    This model represents a request to create a video from predefined scenes
    with explicit search terms for background videos, matching the format
    expected by the external video creation API.
    """
    scenes: List[SceneItem] = Field(
        min_length=1,
        max_length=20,
        description="List of scenes with text content and search terms for background videos."
    )
    config: Optional[ScenesVideoConfig] = Field(
        default=None,
        description="Configuration options for video creation."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class ScenesVideoResult(BaseModel):
    """Scenes-to-video creation result model."""
    final_video_url: AnyUrl = Field(
        description="URL to the final generated video with captions."
    )
    video_with_audio_url: AnyUrl = Field(
        description="URL to the video with audio but without captions."
    )
    audio_url: AnyUrl = Field(
        description="URL to the TTS audio file."
    )
    background_videos_used: List[str] = Field(
        description="List of background video URLs that were used."
    )
    srt_url: Optional[AnyUrl] = Field(
        default=None,
        description="URL to the SRT caption file."
    )
    video_duration: float = Field(
        description="Duration of the final video in seconds."
    )
    processing_time: float = Field(
        description="Total processing time in seconds."
    )
    scenes_processed: int = Field(
        description="Number of scenes that were processed."
    )
    total_text_length: int = Field(
        description="Total character count of all scene text."
    )


# Pollinations.AI Models

class PollinationsImageRequest(BaseModel):
    """Request model for Pollinations image generation."""
    prompt: str = Field(
        min_length=1,
        description="Text description of the image to generate (will be truncated to 2000 characters if longer)"
    )

    @field_validator('prompt')
    @classmethod
    def truncate_prompt(cls, v):
        """Truncate prompt to max 2000 characters instead of rejecting."""
        if v and len(v) > 2000:
            return v[:2000]
        return v
    model: str = Field(
        default="modal_image",
        description="Model to use for generation (flux, etc.)"
    )
    width: int = Field(
        default=1024,
        ge=64,
        le=2048,
        description="Image width in pixels"
    )
    height: int = Field(
        default=1024,
        ge=64,
        le=2048,
        description="Image height in pixels"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Seed for reproducible results"
    )
    enhance: bool = Field(
        default=False,
        description="Enhance prompt using LLM for more detail"
    )
    nologo: bool = Field(
        default=False,
        description="Disable Pollinations logo overlay (requires auth)"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    safe: bool = Field(
        default=False,
        description="Strict NSFW filtering"
    )
    transparent: bool = Field(
        default=False,
        description="Generate with transparent background (gptimage model only)"
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Input image URL for image-to-image generation"
    )
    referrer: Optional[str] = Field(
        default=None,
        description="Referrer for authentication"
    )


class PollinationsTextRequest(BaseModel):
    """Request model for Pollinations text generation (GET method)."""
    prompt: str = Field(
        min_length=1,
        description="Text prompt for generation (will be truncated to 5000 characters if longer)"
    )

    @field_validator('prompt')
    @classmethod
    def truncate_prompt(cls, v):
        """Truncate prompt to max 5000 characters instead of rejecting."""
        if v and len(v) > 5000:
            return v[:5000]
        return v
    model: str = Field(
        default="openai",
        description="Model to use (openai, mistral, etc.)"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Seed for reproducible results"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=3.0,
        description="Controls randomness in output"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    presence_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Presence penalty"
    )
    frequency_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )
    system: Optional[str] = Field(
        default=None,
        max_length=500,
        description="System prompt to guide AI behavior"
    )
    json_mode: bool = Field(
        default=False,
        description="Return response formatted as JSON"
    )
    referrer: Optional[str] = Field(
        default=None,
        description="Referrer for authentication"
    )


class PollinationsChatMessage(BaseModel):
    """Chat message for Pollinations chat API."""
    role: str = Field(
        description="Message role (system, user, assistant)"
    )
    content: Union[str, List[Dict[str, Any]]] = Field(
        description="Message content (string or multimodal array)"
    )


class PollinationsChatRequest(BaseModel):
    """Request model for Pollinations chat API (POST method)."""
    messages: List[PollinationsChatMessage] = Field(
        min_length=1,
        description="Array of message objects"
    )
    model: str = Field(
        default="openai",
        description="Model to use"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Seed for reproducible results"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=3.0,
        description="Controls randomness"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    presence_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Presence penalty"
    )
    frequency_penalty: Optional[float] = Field(
        default=None,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty"
    )
    stream: bool = Field(
        default=False,
        description="Stream response"
    )
    json_mode: bool = Field(
        default=False,
        description="Force JSON output"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Available tools for function calling"
    )
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="Tool choice strategy"
    )
    referrer: Optional[str] = Field(
        default=None,
        description="Referrer for authentication"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class PollinationsAudioRequest(BaseModel):
    """Request model for Pollinations text-to-speech."""
    text: str = Field(
        min_length=1,
        max_length=1000,
        description="Text to synthesize"
    )
    voice: str = Field(
        default="alloy",
        description="Voice to use (alloy, echo, fable, onyx, nova, shimmer)"
    )
    model: str = Field(
        default="openai-audio",
        description="Must be 'openai-audio' for TTS"
    )
    response_format: str = Field(
        default="mp3",
        description="Audio output format (mp3, wav, flac, opus, aac, pcm)"
    )
    speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="Speech speed multiplier"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class PollinationsVideoAnalysisRequest(BaseModel):
    """Request model for Pollinations video analysis."""
    question: str = Field(
        default="Describe this video in detail",
        max_length=1000,
        description="Question or instruction for the video analysis"
    )
    video_url: Optional[str] = Field(
        default=None,
        description="URL to video to analyze"
    )
    model: str = Field(
        default="openai",
        description="Video analysis model to use"
    )


class PollinationsTranscriptionRequest(BaseModel):
    """Request model for Pollinations speech-to-text."""
    audio_format: str = Field(
        default="wav",
        description="Audio format (wav, mp3)"
    )
    question: str = Field(
        default="Transcribe this audio",
        description="Optional instruction text"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class PollinationsResult(BaseModel):
    """Generic result model for Pollinations operations."""
    content_url: str = Field(
        description="URL to the generated content (S3)"
    )
    content_type: str = Field(
        description="MIME type of the generated content"
    )
    file_size: Optional[int] = Field(
        default=None,
        description="File size in bytes"
    )
    generation_time: Optional[float] = Field(
        default=None,
        description="Time taken to generate content in seconds"
    )
    model_used: str = Field(
        description="Model that was used for generation"
    )
    
    
class PollinationsTextResult(BaseModel):
    """Result model for Pollinations text generation."""
    text: str = Field(
        description="Generated text content"
    )
    model_used: str = Field(
        description="Model that was used for generation"
    )
    generation_time: Optional[float] = Field(
        default=None,
        description="Time taken to generate text in seconds"
    )


# Image Enhancement/Unaize Models

class ImageEnhancementRequest(BaseModel):
    """
    Request model for image enhancement and artifact removal (unaize).
    
    This model represents a request to enhance images by removing AI-generated artifacts,
    adding natural imperfections, and adjusting color/contrast to make images look more authentic.
    """
    image_url: AnyUrl = Field(
        description="URL of the image to enhance/unaize."
    )
    enhance_color: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Strength of color enhancement (0.0 to 2.0). 0.0 = black and white, 1.0 = no change, 2.0 = full color enhancement. Default is 1.0."
    )
    enhance_contrast: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Strength of contrast enhancement (0.0 to 2.0). 0.0 = no contrast, 1.0 = no change, 2.0 = high contrast. Default is 1.0."
    )
    noise_strength: Optional[int] = Field(
        default=10,
        ge=0,
        le=100,
        description="Strength of noise to add for natural imperfections (0 to 100). Higher values add more film grain/texture. Default is 10."
    )
    remove_artifacts: Optional[bool] = Field(
        default=True,
        description="Apply AI artifact removal algorithms to reduce digital artifacts and over-smoothing. Default is True."
    )
    add_film_grain: Optional[bool] = Field(
        default=False,
        description="Add subtle film grain effect for a more natural, analog look. Default is False."
    )
    vintage_effect: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Strength of vintage/analog effect (0.0 to 1.0). Adds subtle color shifts and aging. Default is 0.0."
    )
    output_format: Optional[str] = Field(
        default="png",
        description="Output image format (e.g., 'png', 'jpg', 'webp'). Default is 'png'."
    )
    output_quality: Optional[int] = Field(
        default=90,
        ge=1,
        le=100,
        description="Output image quality for lossy formats like JPEG (1-100). Default is 90."
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )


class ImageEnhancementResult(BaseModel):
    """
    Result model for image enhancement operation.
    """
    image_url: AnyUrl = Field(
        description="URL to the enhanced image stored in S3."
    )
    storage_path: str = Field(
        description="Storage path of the enhanced image in S3."
    )
    width: int = Field(
        description="Width of the enhanced image in pixels."
    )
    height: int = Field(
        description="Height of the enhanced image in pixels."
    )
    format: str = Field(
        description="Format of the enhanced image (e.g., 'png', 'jpg')."
    )
    enhancements_applied: List[str] = Field(
        description="List of enhancements that were applied to the image."
    )
    original_size_bytes: int = Field(
        description="Size of the original image in bytes."
    )
    enhanced_size_bytes: int = Field(
        description="Size of the enhanced image in bytes."
    )


# Marker Document Processing Models

class MarkerConversionRequest(BaseModel):
    """Request model for Marker document conversion."""
    output_format: str = Field(
        default="markdown",
        description="Output format: markdown, json, html, or chunks"
    )
    force_ocr: bool = Field(
        default=False,
        description="Force OCR processing on all text"
    )
    preserve_images: bool = Field(
        default=True,
        description="Extract and save images from document"
    )
    use_llm: bool = Field(
        default=False,
        description="Use LLM for enhanced accuracy and formatting"
    )
    paginate_output: bool = Field(
        default=False,
        description="Add page breaks to output"
    )
    llm_service: Optional[str] = Field(
        default=None,
        description="LLM service to use: gemini, openai, claude, ollama"
    )
    sync: bool = Field(
        default=False,
        description="If True, return response immediately. If False (default), create async job."
    )

class MarkerConversionResult(BaseModel):
    """Result model for Marker document conversion."""
    content: str = Field(description="Converted document content")
    content_url: str = Field(description="S3 URL to the converted document")
    original_filename: str = Field(description="Original document filename")
    output_filename: str = Field(description="Generated output filename")
    output_format: str = Field(description="Output format used")
    word_count: int = Field(description="Number of words in converted content")
    character_count: int = Field(description="Number of characters in converted content")
    image_count: int = Field(description="Number of images extracted")
    image_urls: Dict[str, str] = Field(description="Dictionary of image names to S3 URLs")
    metadata: Dict[str, Any] = Field(description="Document metadata from Marker")
    processing_settings: Dict[str, Any] = Field(description="Settings used for processing")

class MarkerSupportedFormatsResponse(BaseModel):
    """Response model for Marker supported formats."""
    input_formats: List[str] = Field(description="List of supported input file formats")
    output_formats: List[str] = Field(description="List of supported output formats")
    features: List[str] = Field(description="List of Marker features")
    llm_services: List[str] = Field(description="List of supported LLM services") 
