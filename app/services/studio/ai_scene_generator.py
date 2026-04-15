"""AI Scene Generator: Generate scenes from a topic or script using LLM."""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


async def generate_scenes_from_topic(
    topic: str | None = None,
    script: str | None = None,
    scene_count: int = 5,
    language: str = "en",
    settings: dict | None = None,
) -> list[dict]:
    """Generate scene descriptions from a topic or script.

    Returns list of dicts: [{"text": str, "search_terms": [str], "duration": float}]
    """
    if script:
        return _split_script_into_scenes(script, scene_count)

    if not topic:
        raise ValueError("Either topic or script is required")

    # Use the existing script generator to create a script, then split into scenes
    try:
        from app.services.text.script_generator import script_generator

        # generate_script expects a single params dict, not keyword args
        result = await script_generator.generate_script({
            "topic": topic,
            "script_type": "facts",
            "max_duration": scene_count * 6,  # ~6 seconds per scene
            "language": language,
        })

        script_text = result if isinstance(result, str) else result.get("script", str(result))

        if script_text:
            return _split_script_into_scenes(script_text, scene_count)

    except Exception as e:
        logger.warning(f"Script generation failed, creating placeholder scenes: {e}")

    # Fallback: create simple scenes (not ideal, but better than nothing)
    return [
        {
            "text": f"Scene {i+1} about {topic}",
            "search_terms": _extract_search_terms_simple(topic),
            "duration": 5.0,
        }
        for i in range(scene_count)
    ]


def _split_script_into_scenes(script: str, target_count: int) -> list[dict]:
    """Split a script into scenes by sentences."""
    import re

    # Split by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [{"text": script, "search_terms": _extract_search_terms_simple(script), "duration": 5.0}]

    # Group sentences into target_count scenes
    scenes = []
    per_scene = max(1, len(sentences) // target_count)

    for i in range(0, len(sentences), per_scene):
        chunk = sentences[i:i + per_scene]
        text = " ".join(chunk)

        # Estimate duration: ~2.5 words per second for TTS
        word_count = len(text.split())
        duration = max(2.0, round(word_count / 2.5, 1))

        scenes.append({
            "text": text,
            "search_terms": _extract_search_terms_simple(text),
            "duration": duration,
        })

    return scenes[:target_count]


# ── Common stop words to filter from search terms ───────────────────
_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "must", "need", "dare",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "about", "like", "through", "after", "over", "between",
    "out", "against", "during", "without", "before", "under", "around",
    "among", "and", "but", "or", "nor", "not", "so", "yet", "both",
    "either", "neither", "each", "every", "all", "any", "few", "more",
    "most", "other", "some", "such", "no", "only", "own", "same", "than",
    "too", "very", "just", "because", "this", "that", "these", "those",
    "it", "its", "they", "them", "their", "we", "us", "our", "you",
    "your", "he", "she", "him", "her", "his", "my", "me", "i",
    "what", "which", "who", "whom", "when", "where", "why", "how",
    "here", "there", "then", "now", "also", "still", "already", "even",
    "don", "doesn", "didn", "won", "wouldn", "couldn", "shouldn",
})


def _extract_search_terms_simple(text: str) -> list[str]:
    """Extract meaningful search terms from text by filtering stop words."""
    import re
    words = re.findall(r'[a-zA-Z]+', text.lower())
    # Keep meaningful words (not stop words, length > 2)
    meaningful = [w for w in words if w not in _STOP_WORDS and len(w) > 2]
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for w in meaningful:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:5]
