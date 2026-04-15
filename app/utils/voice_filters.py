"""
Voice filtering and discovery utilities for TTS.

Provides functions to filter, search, and discover voices
across different TTS providers.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceGender(str, Enum):
    """Voice gender types."""
    MALE = "Male"
    FEMALE = "Female"
    NEUTRAL = "Neutral"


class VoiceCharacteristic(str, Enum):
    """Voice characteristics."""
    CALM = "calm"
    ENERGETIC = "energetic"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    WARM = "warm"
    BRIGHT = "bright"
    DEEP = "deep"
    SOFT = "soft"


class VoiceFilter:
    """Utilities for filtering voices."""
    
    @staticmethod
    def filter_by_gender(
        voices: List[Dict[str, Any]],
        gender: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter voices by gender.
        
        Args:
            voices: List of voice dictionaries
            gender: Gender to filter by ('Male', 'Female', 'Neutral')
            
        Returns:
            Filtered list of voices
        """
        if not gender:
            return voices
        
        return [
            voice for voice in voices
            if voice.get("gender", "").lower() == gender.lower()
        ]
    
    @staticmethod
    def filter_by_language(
        voices: List[Dict[str, Any]],
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter voices by language or locale.
        
        Args:
            voices: List of voice dictionaries
            language: Language code (e.g., 'en', 'en-US', 'fr-FR')
            
        Returns:
            Filtered list of voices
        """
        if not language:
            return voices
        
        language_lower = language.lower()
        filtered = []
        
        for voice in voices:
            voice_lang = voice.get("language", "").lower()
            # Support both exact match and prefix match
            if voice_lang == language_lower or voice_lang.startswith(language_lower):
                filtered.append(voice)
        
        return filtered
    
    @staticmethod
    def filter_by_name_pattern(
        voices: List[Dict[str, Any]],
        pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter voices by name pattern (case-insensitive substring match).
        
        Args:
            voices: List of voice dictionaries
            pattern: Name pattern to search for
            
        Returns:
            Filtered list of voices
        """
        if not pattern:
            return voices
        
        pattern_lower = pattern.lower()
        filtered = []
        
        for voice in voices:
            name = voice.get("name", "").lower()
            display_name = voice.get("display_name", "").lower()
            
            if pattern_lower in name or pattern_lower in display_name:
                filtered.append(voice)
        
        return filtered
    
    @staticmethod
    def filter_by_characteristic(
        voices: List[Dict[str, Any]],
        characteristic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter voices by characteristic (e.g., calm, energetic, professional).
        
        Args:
            voices: List of voice dictionaries
            characteristic: Characteristic to filter by
            
        Returns:
            Filtered list of voices
        """
        if not characteristic:
            return voices
        
        characteristic_lower = characteristic.lower()
        filtered = []
        
        for voice in voices:
            characteristics = voice.get("characteristics", [])
            if isinstance(characteristics, list):
                if any(c.lower() == characteristic_lower for c in characteristics):
                    filtered.append(voice)
        
        return filtered
    
    @staticmethod
    def filter_by_provider(
        voices_dict: Dict[str, List[Dict[str, Any]]],
        provider: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter providers from voice dictionary.
        
        Args:
            voices_dict: Dictionary mapping provider names to voice lists
            provider: Specific provider to filter by
            
        Returns:
            Filtered dictionary with selected provider(s)
        """
        if not provider:
            return voices_dict
        
        provider_lower = provider.lower()
        if provider_lower in voices_dict:
            return {provider_lower: voices_dict[provider_lower]}
        
        return {}
    
    @staticmethod
    def search_voices(
        voices: List[Dict[str, Any]],
        query: str,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search voices using full-text search on multiple fields.
        
        Args:
            voices: List of voice dictionaries
            query: Search query
            fields: Fields to search in (default: name, display_name, language)
            
        Returns:
            Filtered list of matching voices
        """
        if not query:
            return voices
        
        if fields is None:
            fields = ["name", "display_name", "language", "gender"]
        
        query_lower = query.lower()
        matched = []
        
        for voice in voices:
            for field in fields:
                value = voice.get(field, "")
                if isinstance(value, str) and query_lower in value.lower():
                    matched.append(voice)
                    break
        
        return matched


class VoiceRecommender:
    """Recommendations for voice selection based on use cases."""
    
    # Presets for common use cases
    PRESETS = {
        "professional": {
            "gender": None,  # Any gender
            "characteristics": ["professional"],
            "description": "Professional sounding voices for business/formal contexts"
        },
        "casual": {
            "gender": None,
            "characteristics": ["friendly", "warm"],
            "description": "Friendly, casual voices for conversational content"
        },
        "energetic": {
            "gender": None,
            "characteristics": ["energetic", "bright"],
            "description": "Energetic voices for engaging content"
        },
        "calm": {
            "gender": None,
            "characteristics": ["calm", "soft"],
            "description": "Calm, soothing voices for relaxation/meditation"
        },
        "male": {
            "gender": "Male",
            "characteristics": None,
            "description": "Male voices"
        },
        "female": {
            "gender": "Female",
            "characteristics": None,
            "description": "Female voices"
        }
    }
    
    @staticmethod
    def get_recommended_voices(
        voices: List[Dict[str, Any]],
        use_case: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get voice recommendations for a specific use case.
        
        Args:
            voices: Available voices
            use_case: Use case preset (professional, casual, energetic, calm, male, female)
            language: Filter by language
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended voices
        """
        if use_case and use_case in VoiceRecommender.PRESETS:
            preset = VoiceRecommender.PRESETS[use_case]
            
            # Filter by gender if specified
            if preset["gender"]:
                voices = VoiceFilter.filter_by_gender(voices, preset["gender"])
            
            # Filter by language
            if language:
                voices = VoiceFilter.filter_by_language(voices, language)
            
            # Filter by characteristics if specified
            if preset["characteristics"]:
                filtered = []
                for char in preset["characteristics"]:
                    filtered.extend(
                        VoiceFilter.filter_by_characteristic(voices, char)
                    )
                voices = list({v["name"]: v for v in filtered}.values())  # Deduplicate
        
        elif language:
            voices = VoiceFilter.filter_by_language(voices, language)
        
        return voices[:limit]
    
    @staticmethod
    def get_voice_summary(voice: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of a voice.
        
        Args:
            voice: Voice dictionary
            
        Returns:
            Summary string
        """
        parts = []
        
        if "display_name" in voice:
            parts.append(voice["display_name"])
        elif "name" in voice:
            parts.append(voice["name"])
        
        if "gender" in voice:
            parts.append(f"({voice['gender']})")
        
        if "language" in voice:
            parts.append(f"[{voice['language']}]")
        
        if "characteristics" in voice and voice["characteristics"]:
            chars = ", ".join(voice["characteristics"])
            parts.append(f"- {chars}")
        
        return " ".join(parts)


def get_voice_options(
    voices_dict: Dict[str, List[Dict[str, Any]]],
    provider: Optional[str] = None,
    gender: Optional[str] = None,
    language: Optional[str] = None,
    use_case: Optional[str] = None,
    search_query: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Comprehensive voice discovery function.
    
    Args:
        voices_dict: Dictionary mapping provider names to voice lists
        provider: Filter by provider
        gender: Filter by gender
        language: Filter by language
        use_case: Get recommendations for use case
        search_query: Search voices by text
        limit: Maximum number of results
        
    Returns:
        Dictionary with filtered voices and metadata
    """
    # Filter by provider
    if provider:
        voices_dict = VoiceFilter.filter_by_provider(voices_dict, provider)
    
    # Flatten providers into single list
    all_voices = []
    for prov, voice_list in voices_dict.items():
        for voice in voice_list:
            voice["provider"] = prov
            all_voices.append(voice)
    
    # Apply filters
    if search_query:
        all_voices = VoiceFilter.search_voices(all_voices, search_query)
    elif use_case:
        all_voices = VoiceRecommender.get_recommended_voices(
            all_voices, use_case, language, limit
        )
    else:
        if gender:
            all_voices = VoiceFilter.filter_by_gender(all_voices, gender)
        if language:
            all_voices = VoiceFilter.filter_by_language(all_voices, language)
        
        all_voices = all_voices[:limit]
    
    # Group by provider for response
    grouped = {}
    for voice in all_voices:
        prov = voice.pop("provider", "unknown")
        if prov not in grouped:
            grouped[prov] = []
        grouped[prov].append(voice)
    
    return {
        "total": len(all_voices),
        "limit": limit,
        "voices": grouped,
        "summary": {
            "by_provider": {k: len(v) for k, v in grouped.items()},
            "filters": {
                "provider": provider,
                "gender": gender,
                "language": language,
                "use_case": use_case,
                "search_query": search_query
            }
        }
    }
