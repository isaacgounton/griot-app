"""
Enhanced Video Search Query Generator with Scene-Level Analysis.

Key improvements:
1. Scene-level query generation (preserves context)
2. Semantic analysis (sentiment, time, domain, mood)
3. Domain-specific fallbacks
4. TTS duration support
5. Query validation and refinement
"""
import os
import json
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from app.utils.ai_context import get_current_context
from app.services.ai.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)


class VideoSearchQueryGenerator:
    """Enhanced service for generating context-aware video search queries."""

    # Domain-specific fallback libraries
    DOMAIN_FALLBACKS = {
        'food': [
            "chef cooking kitchen",
            "food preparation ingredients",
            "restaurant dining experience",
            "fresh produce market",
            "baking pastry chef"
        ],
        'travel': [
            "airplane flight travel",
            "tourist exploring city",
            "landscape scenic view",
            "hotel vacation resort",
            "backpacker hiking mountain"
        ],
        'health': [
            "doctor patient consultation",
            "exercise fitness workout",
            "healthy food nutrition",
            "meditation wellness yoga",
            "running outdoor fitness"
        ],
        'technology': [
            "developer coding laptop",
            "smartphone app technology",
            "data analytics screen",
            "robot ai automation",
            "hands typing keyboard"
        ],
        'business': [
            "businessman meeting office",
            "team collaboration workspace",
            "presentation conference room",
            "entrepreneur startup office",
            "businessman typing laptop"
        ],
        'education': [
            "teacher explaining classroom",
            "student studying library",
            "university lecture hall",
            "books reading education",
            "online learning computer"
        ],
        'nature': [
            "forest trees nature",
            "ocean waves beach",
            "mountain landscape hiking",
            "sunset sky clouds",
            "wildlife animals nature"
        ],
        'finance': [
            "stock market trading",
            "businessman meeting office",
            "calculator finance accounting",
            "money cash currency",
            "graph chart analytics"
        ],
        'personal': [
            "friends embracing warmly",
            "couple romantic moment",
            "family celebrating together",
            "best friends laughing",
            "lovers holding hands",
            "happy couple smiling"
        ]
    }

    def __init__(self):
        self.unified_service = unified_ai_service

    def _detect_sentiment(self, text: str) -> str:
        """Detect sentiment from text: positive, negative, or neutral."""
        text_lower = text.lower()

        positive_words = {
            'success', 'growth', 'innovation', 'excellent', 'amazing', 'wonderful',
            'happy', 'joy', 'celebration', 'achievement', 'breakthrough', 'victory',
            'win', 'triumph', 'progress', 'improvement', 'advance', 'thrive', 'boom',
            'love', 'best', 'friend', 'family', 'together', 'embrace', 'romantic'
        }

        negative_words = {
            'fail', 'loss', 'decline', 'struggle', 'crisis', 'problem', 'issue',
            'sad', 'difficult', 'challenge', 'bankrupt', 'closed', 'recession',
            'worry', 'concern', 'risk', 'threat', 'collapse', 'disaster', 'crash'
        }

        words = set(text_lower.split())
        positive_count = len(words & positive_words)
        negative_count = len(words & negative_words)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'

    def _detect_time_context(self, text: str) -> str:
        """Detect time period: modern, historical, future, or timeless."""
        text_lower = text.lower()

        if any(word in text_lower for word in ['ancient', 'medieval', 'century', 'historical', 'past', 'traditional', 'vintage', 'old']):
            return 'historical'
        elif any(word in text_lower for word in ['future', 'tomorrow', 'upcoming', 'next', 'will be', 'forecast', 'prediction']):
            return 'future'
        elif any(word in text_lower for word in ['today', 'modern', 'current', 'contemporary', 'digital', 'smartphone', 'app', 'internet']):
            return 'modern'
        return 'timeless'

    def _detect_location(self, text: str) -> str:
        """Detect location type: office, outdoor, urban, nature, etc."""
        text_lower = text.lower()

        if any(word in text_lower for word in ['office', 'workplace', 'desk', 'meeting', 'conference']):
            return 'office'
        elif any(word in text_lower for word in ['forest', 'mountain', 'ocean', 'beach', 'nature', 'outdoor', 'park']):
            return 'nature'
        elif any(word in text_lower for word in ['city', 'urban', 'street', 'building', 'downtown']):
            return 'urban'
        elif any(word in text_lower for word in ['home', 'house', 'living room', 'kitchen', 'bedroom']):
            return 'home'
        elif any(word in text_lower for word in ['school', 'classroom', 'university', 'library']):
            return 'educational'
        elif any(word in text_lower for word in ['hospital', 'clinic', 'medical', 'doctor']):
            return 'medical'
        return 'generic'

    def _detect_domain(self, text: str) -> str:
        """Detect content domain for fallback selection."""
        text_lower = text.lower()

        domain_keywords = {
            'food': ['food', 'cooking', 'chef', 'restaurant', 'meal', 'recipe', 'kitchen', 'dining', 'cuisine'],
            'travel': ['travel', 'trip', 'vacation', 'tourist', 'flight', 'hotel', 'destination', 'journey', 'explore'],
            'health': ['health', 'fitness', 'exercise', 'wellness', 'medical', 'doctor', 'patient', 'nutrition', 'yoga'],
            'technology': ['technology', 'tech', 'software', 'app', 'digital', 'computer', 'internet', 'data', 'ai', 'code'],
            'business': ['business', 'company', 'market', 'entrepreneur', 'startup', 'professional', 'corporate', 'commerce'],
            'education': ['education', 'school', 'university', 'student', 'teacher', 'learn', 'study', 'class', 'training'],
            'nature': ['nature', 'wildlife', 'animal', 'forest', 'ocean', 'mountain', 'landscape', 'environment'],
            'finance': ['finance', 'money', 'investment', 'stock', 'banking', 'economy', 'financial', 'trading'],
            'personal': ['love', 'friend', 'best', 'family', 'relationship', 'couple', 'romantic', 'embrace', 'hug', 'together', 'happy', 'celebration', 'birthday', 'wedding', 'marriage', 'relationship', 'partner', 'bff', 'companion']
        }

        domain_scores = {}
        words = set(text_lower.split())

        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        return 'business'  # Default fallback

    def _detect_primary_action(self, text: str) -> str:
        """Detect primary action in the scene."""
        text_lower = text.lower()

        actions = {
            'working': ['working', 'typing', 'computing', 'analyzing'],
            'meeting': ['meeting', 'discussing', 'presenting', 'conferencing'],
            'learning': ['learning', 'studying', 'reading', 'researching'],
            'cooking': ['cooking', 'preparing', 'baking', 'serving'],
            'traveling': ['traveling', 'flying', 'driving', 'exploring'],
            'exercising': ['exercising', 'running', 'training', 'workout'],
            'creating': ['creating', 'designing', 'building', 'developing']
        }

        for action, verbs in actions.items():
            if any(verb in text_lower for verb in verbs):
                return action
        return 'general'

    def _analyze_scene_semantics(self, text: str) -> Dict[str, Any]:
        """Comprehensive semantic analysis of scene text."""
        return {
            'sentiment': self._detect_sentiment(text),
            'time_context': self._detect_time_context(text),
            'location_type': self._detect_location(text),
            'action_type': self._detect_primary_action(text),
            'domain': self._detect_domain(text)
        }

    def _get_contextual_prompt(self, scene_text: str, semantics: Dict[str, Any]) -> str:
        """Generate AI prompt with semantic context."""
        return f"""# Generate ONE Video Search Query - Scene-Specific

{get_current_context()}

Scene Text: "{scene_text}"

Scene Analysis:
- Sentiment: {semantics['sentiment']}
- Time Period: {semantics['time_context']}
- Location: {semantics['location_type']}
- Primary Action: {semantics['action_type']}
- Content Domain: {semantics['domain']}

## CRITICAL RULES

1. **Match the SENTIMENT**:
   - Positive → Use uplifting, success-oriented visuals
   - Negative → Use struggle, challenge, somber visuals
   - Neutral → Use professional, standard visuals

2. **Match the TIME PERIOD**:
   - Historical → Use period-appropriate visuals (no modern tech)
   - Modern → Use contemporary settings, current technology
   - Future → Use futuristic, advanced technology
   - Timeless → Use universal, timeless visuals

3. **Use CONCRETE Visual Patterns**:
   [WHO/WHAT] + [ACTION] + [CONTEXT]

   Examples by domain:
   - Food: "chef cooking kitchen" or "fresh ingredients preparation"
   - Travel: "tourist exploring city" or "airplane flight travel"
   - Health: "doctor patient consultation" or "exercise fitness workout"
   - Tech: "developer coding laptop" or "smartphone app interface"
   - Business: "businessman meeting office" or "team collaboration workspace"
   - Personal: "friends embracing warmly" or "couple romantic moment"

4. **AVOID Abstract Terms**:
   ❌ "innovation" → ✅ "scientist laboratory research"
   ❌ "success" → ✅ "team celebrating achievement"
   ❌ "technology" → ✅ "hands typing keyboard"

5. **Query Format**:
   - 2-4 words only
   - All concrete, searchable terms
   - Match scene content exactly

Return ONLY the query, nothing else. No JSON, no explanation, just the 2-4 word query."""

    def _create_domain_fallback_query(self, semantics: Dict[str, Any]) -> str:
        """Create intelligent fallback based on detected domain and semantics."""
        domain = semantics.get('domain', 'business')
        sentiment = semantics.get('sentiment', 'neutral')

        fallbacks = self.DOMAIN_FALLBACKS.get(domain, self.DOMAIN_FALLBACKS['business'])

        # Try to match sentiment
        if sentiment == 'negative' and domain == 'business':
            return "worried businessman stressed office"
        elif sentiment == 'positive' and domain == 'business':
            return "team celebrating success office"
        elif sentiment == 'positive' and domain == 'personal':
            return "friends embracing warmly"
        elif sentiment == 'negative' and domain == 'personal':
            return "person alone sad reflection"

        # Return first fallback for domain
        return fallbacks[0]

    async def generate_scene_query(
        self,
        scene_text: str,
        scene_duration: float,
        provider: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Generate a video search query for a SINGLE scene.

        This is the core improvement - analyze each scene independently.
        """
        # Analyze scene semantics
        semantics = self._analyze_scene_semantics(scene_text)
        logger.info(f"Scene semantics: {semantics}")

        # Try AI query generation
        try:
            if self.unified_service.is_available():
                prompt = self._get_contextual_prompt(scene_text, semantics)

                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Generate video query for: {scene_text[:200]}"}
                ]

                response = await self.unified_service.create_chat_completion(
                    messages=messages,
                    provider=provider,
                    temperature=0.3,
                    max_tokens=50
                )

                content = response.get('content')
                if not content:
                    raise Exception("Empty response from AI")

                query = content.strip()

                # Validate query
                if query and 2 <= len(query.split()) <= 4 and len(query) < 50:
                    logger.info(f"Generated AI query: '{query}' for scene: '{scene_text[:50]}...'")
                    return {
                        'query': query,
                        'duration': scene_duration,
                        'semantics': semantics,
                        'source': 'ai'
                    }
        except Exception as e:
            logger.warning(f"AI query generation failed: {e}")

        # Fallback to domain-specific query
        fallback_query = self._create_domain_fallback_query(semantics)
        logger.info(f"Using domain fallback: '{fallback_query}' for scene: '{scene_text[:50]}...'")

        return {
            'query': fallback_query,
            'duration': scene_duration,
            'semantics': semantics,
            'source': 'fallback'
        }

    async def generate_video_search_queries(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate video search queries with scene-level analysis.

        Supports:
        1. Scene-based analysis (preserves context)
        2. Actual TTS duration (if provided)
        3. Semantic understanding
        """
        # Support both scene-based and script-based input
        if 'scenes' in params:
            # Scene-based approach (recommended)
            scenes = params['scenes']
            queries = []

            # Build full script from all scenes for context
            full_script = ' '.join([scene.get('text', '') for scene in scenes])

            for idx, scene in enumerate(scenes):
                scene_text = scene.get('text', '')
                scene_duration = scene.get('duration', 3.0)

                query_data = await self.generate_scene_query(
                    scene_text=scene_text,
                    scene_duration=scene_duration,
                    provider=params.get('provider', 'auto')
                )

                queries.append({
                    'query': query_data['query'],
                    'duration': query_data['duration'],
                    'semantics': query_data['semantics'],
                    'source': query_data['source'],
                    'script_text': scene_text,  # Full narration text for this segment
                    'index': idx,  # Position in sequence
                    'total_segments': len(scenes),  # Total number of segments
                    'full_script': full_script  # Complete script for context
                })

            total_duration = sum(q['duration'] for q in queries)

            return {
                'queries': queries,
                'total_duration': total_duration,
                'total_segments': len(queries),
                'provider_used': 'scene-based',
                'improvements': {
                    'scene_level_analysis': True,
                    'semantic_understanding': True,
                    'domain_specific_fallbacks': True
                }
            }

        else:
            # Script-based approach (backward compatibility)
            script = params.get('script', '')
            segment_duration = params.get('segment_duration', 3.0)

            # Split script into sentences for better analysis
            sentences = re.split(r'[.!?]+', script)
            sentences = [s.strip() for s in sentences if s.strip()]

            queries = []
            for idx, sentence in enumerate(sentences):
                query_data = await self.generate_scene_query(
                    scene_text=sentence,
                    scene_duration=segment_duration,
                    provider=params.get('provider', 'auto')
                )

                queries.append({
                    'query': query_data['query'],
                    'duration': segment_duration,
                    'semantics': query_data['semantics'],
                    'source': query_data['source'],
                    'script_text': sentence,  # Full sentence text for this segment
                    'index': idx,  # Position in sequence
                    'total_segments': len(sentences),  # Total number of segments
                    'full_script': script  # Complete script for context
                })

            return {
                'queries': queries,
                'total_duration': segment_duration * len(queries),
                'total_segments': len(queries),
                'provider_used': 'sentence-based'
            }


# Singleton instance
video_search_query_generator = VideoSearchQueryGenerator()
