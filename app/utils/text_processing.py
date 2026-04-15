"""
Enhanced text processing utilities for TTS with context preparation.
Based on the openai-edge-tts project text processing capabilities.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import emoji
    EMOJI_AVAILABLE = True
except ImportError:
    EMOJI_AVAILABLE = False
    logger.warning("emoji package not available. Emoji processing will be skipped.")


def prepare_tts_input_with_context(text: str, remove_filter: bool = False) -> str:
    """
    Prepare text for TTS by cleaning Markdown and adding contextual hints.
    Based on the openai-edge-tts project implementation.
    
    Args:
        text: Raw text containing potential Markdown formatting
        remove_filter: If True, skip text processing
        
    Returns:
        Cleaned text suitable for TTS
    """
    if remove_filter:
        return text
    
    # Remove emojis if emoji package is available
    if EMOJI_AVAILABLE:
        text = emoji.replace_emoji(text, replace='')

    # Add context for headers
    def header_replacer(match):
        level = len(match.group(1))  # Number of '#' symbols
        header_text = match.group(2).strip()
        if level == 1:
            return f"Title — {header_text}\n"
        elif level == 2:
            return f"Section — {header_text}\n"
        else:
            return f"Subsection — {header_text}\n"

    text = re.sub(r"^(#{1,6})\s+(.*)", header_replacer, text, flags=re.MULTILINE)

    # Remove links while keeping the link text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Describe inline code
    text = re.sub(r"`([^`]+)`", r"code snippet: \1", text)

    # Remove bold/italic symbols but keep the content
    text = re.sub(r"(\*\*|__|\*|_)", '', text)

    # Remove code blocks (multi-line) with a description
    text = re.sub(r"```([\s\S]+?)```", r"(code block omitted)", text)

    # Remove image syntax but add alt text if available
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"Image: \1", text)

    # Remove HTML tags
    text = re.sub(r"</?[^>]+(>|$)", '', text)

    # Normalize line breaks
    text = re.sub(r"\n{2,}", '\n\n', text)  # Ensure consistent paragraph separation

    # Replace multiple spaces within lines
    text = re.sub(r" {2,}", ' ', text)

    # Trim leading and trailing whitespace from the whole text
    text = text.strip()

    return text


def normalize_text_advanced(text: str, options: Optional[dict] = None) -> str:
    """
    Advanced text normalization with configurable options.
    
    Args:
        text: Text to normalize
        options: Normalization options dictionary
        
    Returns:
        Normalized text
    """
    if not options:
        options = {}
    
    # URL normalization
    if options.get('url_normalization', True):
        text = re.sub(r'https?://[^\s]+', 'U R L', text)
    
    # Email normalization  
    if options.get('email_normalization', True):
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email address', text)
    
    # Phone normalization
    if options.get('phone_normalization', True):
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'phone number', text)
        text = re.sub(r'\b\+\d{1,3}[-.\s]?\d{1,14}\b', 'phone number', text)  # International format
    
    # Unit normalization
    if options.get('unit_normalization', False):
        # File sizes
        text = re.sub(r'(\d+)\s*(KB|kb)', r'\1 kilobytes', text)
        text = re.sub(r'(\d+)\s*(MB|mb)', r'\1 megabytes', text)
        text = re.sub(r'(\d+)\s*(GB|gb)', r'\1 gigabytes', text)
        text = re.sub(r'(\d+)\s*(TB|tb)', r'\1 terabytes', text)
        
        # Distances
        text = re.sub(r'(\d+)\s*(km|KM)', r'\1 kilometers', text)
        text = re.sub(r'(\d+)\s*(m|M)(?=\s|$)', r'\1 meters', text)
        text = re.sub(r'(\d+)\s*(cm|CM)', r'\1 centimeters', text)
        
        # Weights
        text = re.sub(r'(\d+)\s*(kg|KG)', r'\1 kilograms', text)
        text = re.sub(r'(\d+)\s*(g|G)(?=\s|$)', r'\1 grams', text)
    
    # Replace remaining symbols
    if options.get('replace_remaining_symbols', True):
        symbol_replacements = {
            '&': ' and ',
            '@': ' at ',
            '%': ' percent ',
            '#': ' hashtag ',
            '$': ' dollar ',
            '+': ' plus ',
            '=': ' equals ',
            '<': ' less than ',
            '>': ' greater than ',
            '|': ' pipe ',
            '~': ' tilde ',
            '^': ' caret ',
            '°': ' degrees ',
            '±': ' plus or minus ',
            '×': ' times ',
            '÷': ' divided by ',
        }
        for symbol, replacement in symbol_replacements.items():
            text = text.replace(symbol, replacement)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def process_pause_tags_advanced(text: str) -> str:
    """
    Process pause tags in text with advanced silence generation.
    
    Args:
        text: Text containing pause tags like [pause:0.5s]
        
    Returns:
        Text with pause tags converted to appropriate format
    """
    # Pattern to match [pause:Xs] or [pause:X.Ys]
    pause_pattern = re.compile(r'\[pause:([\d.]+)s?\]', re.IGNORECASE)
    
    def replace_pause(match):
        try:
            duration = float(match.group(1))
            # Convert to approximate silence (could be improved with actual silence generation)
            if duration <= 0.5:
                return "... "
            elif duration <= 1.0:
                return "... ... "
            elif duration <= 2.0:
                return "... ... ... "
            else:
                # For longer pauses, use multiple dots
                dots_count = min(int(duration * 2), 10)  # Cap at 10 dots
                return "... " * dots_count
        except ValueError:
            # If duration can't be parsed, return a default pause
            return "... "
    
    return pause_pattern.sub(replace_pause, text)


def clean_text_for_speech(text: str, comprehensive_cleaning: bool = True) -> str:
    """
    Comprehensive text cleaning for speech synthesis.
    
    Args:
        text: Raw text to clean
        comprehensive_cleaning: Whether to apply all cleaning rules
        
    Returns:
        Cleaned text optimized for TTS
    """
    if not text:
        return ""
    
    if comprehensive_cleaning:
        # Apply Markdown cleaning
        text = prepare_tts_input_with_context(text, remove_filter=False)
        
        # Apply advanced normalization
        text = normalize_text_advanced(text, {
            'url_normalization': True,
            'email_normalization': True,
            'phone_normalization': True,
            'unit_normalization': False,  # Can be enabled if needed
            'replace_remaining_symbols': True
        })
        
        # Process pause tags
        text = process_pause_tags_advanced(text)
    
    # Final cleanup
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = text.strip()
    
    return text


def extract_language_from_text(text: str) -> Optional[str]:
    """
    Attempt to detect the primary language of the text.
    Basic implementation - could be enhanced with proper language detection.
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code or None if detection fails
    """
    # Very basic language detection based on character patterns
    # This is a simplified version - a proper implementation would use a language detection library
    
    # Check for common patterns
    if re.search(r'[\u4e00-\u9fff]', text):  # Chinese characters
        return 'zh'
    elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):  # Japanese hiragana/katakana
        return 'ja'
    elif re.search(r'[\u0900-\u097f]', text):  # Hindi/Devanagari
        return 'hi'
    elif re.search(r'[àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]', text):  # Extended Latin (European)
        # Could be French, Spanish, German, etc. - would need more sophisticated detection
        return 'en'  # Default to English for now
    else:
        return 'en'  # Default to English


def validate_text_length(text: str, max_length: int = 5000) -> tuple[bool, str]:
    """
    Validate text length for TTS processing.
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Text cannot be empty"
    
    if len(text) > max_length:
        return False, f"Text exceeds maximum length of {max_length} characters (current: {len(text)})"
    
    return True, ""