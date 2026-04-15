# Video Search Query Alignment Improvements

**Status: ✅ IMPLEMENTED**

## Problem Statement
Videos generated for voiceover content were not always semantically aligned with what's being said, leading to visual-audio mismatch.

**This has been fixed with the enhanced video search query generator.**

## Root Causes Identified

### 1. **Timing Misalignment** ⚠️ HIGH PRIORITY
**Current Behavior:**
- Queries timed based on estimated word count (words ÷ 2.8/sec)
- Doesn't account for actual TTS output duration
- Pauses, emphasis, and speaking rate variations ignored

**Impact:**
- A 5-second script segment might have 3-second or 8-second actual audio
- Videos start/end at wrong times relative to voiceover

**Solution:**
```python
# BEFORE (estimated):
duration = len(script.split()) / 2.8

# AFTER (actual TTS):
duration = await get_tts_audio_duration(script, voice, provider)
```

### 2. **Whole-Script Analysis Loss** ⚠️ HIGH PRIORITY
**Current Behavior:**
- AI analyzes entire script, then segments it
- Loses per-scene context and nuance

**Example:**
```
Script: "In ancient times, merchants traded goods. Today, we use digital payments."

Current Query Generation:
- Segment 1 (0-3s): "businessman office" ❌
- Segment 2 (3-6s): "businessman office" ❌

Better Query Generation:
- Segment 1 (0-3s): "ancient market merchants trading" ✅
- Segment 2 (3-6s): "smartphone payment digital" ✅
```

**Solution:**
- Generate queries PER SENTENCE/SCENE, not for whole script
- Preserve context window for each segment

### 3. **Limited Semantic Understanding** ⚠️ MEDIUM PRIORITY
**Current Behavior:**
- Extracts keywords/nouns only
- No understanding of:
  - Sentiment (positive vs negative)
  - Actions vs objects
  - Time/era context
  - Emotional tone

**Examples:**
```
"Struggling businesses during recession" → "businessman office" ❌
Better: "empty office closed business" ✅

"Revolutionary AI breakthrough" → "hands typing keyboard" ❌
Better: "robot ai technology innovation" ✅

"Peaceful meditation retreat" → "person sitting" ❌
Better: "meditation yoga peaceful nature" ✅
```

**Solution:**
- Add sentiment analysis to query generation
- Include contextual modifiers (time, place, mood)
- Use action verbs when present in script

### 4. **Generic Fallback Overuse** ⚠️ MEDIUM PRIORITY
**Current Behavior:**
When script analysis fails:
```python
fallbacks = [
    "businessman typing laptop",  # Used for EVERYTHING
    "hands typing keyboard",      # Generic tech
    "team meeting office",        # Generic business
]
```

**Impact:**
- Food blog → shows office workers
- Travel vlog → shows business meetings
- Health content → shows people typing

**Solution:**
- Create domain-specific fallback libraries:
  - Food: "chef cooking", "food preparation", "restaurant kitchen"
  - Travel: "airplane travel", "tourist sightseeing", "landscape nature"
  - Health: "doctor patient", "exercise fitness", "healthy food"
- Detect script domain before fallback selection

### 5. **No Iterative Refinement** ⚠️ LOW PRIORITY
**Current Behavior:**
- Generate queries once
- No feedback if videos don't match
- No retry with refined queries

**Solution:**
- Check if video search returned results
- If no/poor results, try alternative query formulations
- Use video tags/metadata to validate relevance

## Proposed Implementation Changes

### Phase 1: Critical Fixes (Week 1)

#### 1.1 Use Actual TTS Duration
```python
async def generate_video_search_queries_v2(self, params: Dict[str, Any]) -> Dict[str, Any]:
    script = params['script']

    # NEW: Get actual TTS duration instead of estimating
    if params.get('voice_provider') and params.get('voice_name'):
        actual_duration = await self._get_tts_duration(
            script,
            params['voice_provider'],
            params['voice_name']
        )
    else:
        actual_duration = self._estimate_script_duration(script)

    # Generate queries with actual timing...
```

#### 1.2 Scene-Level Query Generation
```python
async def _generate_queries_per_scene(self, scenes: List[Dict]) -> List[Dict]:
    """Generate queries for each scene individually to preserve context."""
    queries = []

    for scene in scenes:
        # Analyze THIS scene's content specifically
        scene_context = {
            'text': scene['text'],
            'previous_scene': scenes[scenes.index(scene)-1] if scenes.index(scene) > 0 else None,
            'next_scene': scenes[scenes.index(scene)+1] if scenes.index(scene) < len(scenes)-1 else None
        }

        # Generate query specific to this scene's content
        scene_query = await self._generate_contextual_query(scene_context)
        queries.append(scene_query)

    return queries
```

### Phase 2: Enhanced Understanding (Week 2)

#### 2.1 Semantic Analysis Enhancement
```python
def _analyze_scene_semantics(self, text: str) -> Dict[str, Any]:
    """Extract semantic information from scene text."""
    return {
        'sentiment': self._detect_sentiment(text),  # positive, negative, neutral
        'time_context': self._detect_time_context(text),  # modern, ancient, future, etc.
        'location_type': self._detect_location(text),  # indoor, outdoor, urban, nature
        'action_type': self._detect_primary_action(text),  # working, traveling, eating, etc.
        'mood': self._detect_mood(text),  # professional, casual, energetic, calm
        'domain': self._detect_domain(text)  # business, health, food, travel, tech, etc.
    }
```

#### 2.2 Domain-Specific Fallbacks
```python
DOMAIN_FALLBACKS = {
    'food': [
        "chef cooking kitchen",
        "food preparation ingredients",
        "restaurant dining experience",
        "fresh produce market"
    ],
    'travel': [
        "airplane flight travel",
        "tourist exploring city",
        "landscape scenic view",
        "hotel vacation resort"
    ],
    'health': [
        "doctor patient consultation",
        "exercise fitness workout",
        "healthy food nutrition",
        "meditation wellness yoga"
    ],
    'technology': [
        "developer coding laptop",
        "smartphone app technology",
        "data analytics screen",
        "robot ai automation"
    ],
    'business': [
        "businessman meeting office",
        "team collaboration workspace",
        "presentation conference room",
        "entrepreneur startup office"
    ]
}
```

### Phase 3: Quality Improvements (Week 3)

#### 3.1 Query Validation & Refinement
```python
async def _validate_and_refine_query(
    self,
    query: str,
    scene_text: str
) -> str:
    """Validate query returns relevant videos, refine if needed."""

    # Test query with video search
    test_results = await multi_video_search_service.search_videos(
        query=query,
        max_results=3
    )

    # If no results or poor quality, try alternative
    if not test_results or self._calculate_avg_relevance(test_results) < 0.5:
        logger.warning(f"Query '{query}' yielded poor results, trying alternative")

        # Generate alternative query
        alternative = await self._generate_alternative_query(scene_text, avoid_terms=[query])
        return alternative

    return query
```

#### 3.2 Enhanced AI Prompt with Context
```python
def _get_contextual_prompt(self, scene_semantics: Dict) -> str:
    return f"""Generate a video search query for this SPECIFIC scene.

Scene Context:
- Sentiment: {scene_semantics['sentiment']}
- Time Period: {scene_semantics['time_context']}
- Location: {scene_semantics['location_type']}
- Primary Action: {scene_semantics['action_type']}
- Mood: {scene_semantics['mood']}
- Domain: {scene_semantics['domain']}

Rules:
1. Query MUST match the sentiment (don't show happy videos for sad content)
2. Query MUST match time period (no modern tech for historical content)
3. Query MUST match the action type
4. Use 2-4 concrete, searchable words
5. Follow pattern: [WHO/WHAT] + [ACTION] + [CONTEXT]

Examples based on sentiment:
- Positive/Success: "team celebrating success office"
- Negative/Struggle: "worried businessman stressed office"
- Neutral/Work: "professional working computer office"

Scene Text: {scene_text}

Generate ONE query (2-4 words):"""
```

## Testing Strategy

### Test Cases

#### Test 1: Time Period Alignment
```python
# Input
scene_text = "In medieval times, knights fought battles"

# Expected
query = "knight medieval battle" or "armor sword warrior"

# NOT
query = "businessman office"  # ❌ Wrong era
```

#### Test 2: Sentiment Alignment
```python
# Input
scene_text = "The company went bankrupt and workers lost their jobs"

# Expected
query = "empty office closed business" or "unemployed worker sad"

# NOT
query = "businessman working laptop"  # ❌ Wrong sentiment
```

#### Test 3: Domain Alignment
```python
# Input
scene_text = "The chef prepared a delicious Italian meal"

# Expected
query = "chef cooking italian kitchen" or "pasta preparation cooking"

# NOT
query = "businessman office"  # ❌ Wrong domain
```

### Metrics to Track
1. **Alignment Score**: Human rating of video-voiceover match (1-5 scale)
2. **Timing Accuracy**: % of videos that match actual TTS duration ±10%
3. **Fallback Rate**: % of queries using generic fallbacks vs content-specific
4. **Search Success Rate**: % of queries returning >5 relevant videos
5. **Domain Detection Accuracy**: % correct domain classification

## Implementation Priority

### Must Have (This Week)
- [x] Document current issues
- [ ] Implement scene-level query generation
- [ ] Add semantic analysis (sentiment, time, domain)
- [ ] Use actual TTS duration for timing

### Should Have (Next Week)
- [ ] Domain-specific fallback libraries
- [ ] Enhanced AI prompts with context
- [ ] Query validation and refinement logic

### Nice to Have (Future)
- [ ] Video quality feedback loop
- [ ] A/B testing of different query strategies
- [ ] User feedback on video-voiceover alignment

## Success Criteria

After implementation, we should see:
- ✅ 80%+ alignment score (human evaluation)
- ✅ <20% generic fallback usage
- ✅ 90%+ timing accuracy
- ✅ 95%+ search success rate
- ✅ 85%+ domain detection accuracy

## Migration Plan

1. **Create v2 endpoint** (`/api/v1/video/search-queries-v2`) with improvements
2. **A/B test** v1 vs v2 with sample videos
3. **Collect feedback** from 50+ test videos
4. **Gradual rollout** to production
5. **Deprecate v1** after 2 weeks of successful v2 usage
