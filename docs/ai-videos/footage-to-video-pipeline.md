# Footage-to-Video Pipeline

Complete end-to-end video generation from topics. Transform any subject into a professional video with AI script generation, stock footage, narration, and captions.

**Last Updated:** 2025-01-09 (API parameters verified against `app/models.py`)

## Overview

The Footage-to-Video Pipeline is the flagship feature that combines all AI capabilities into a single, powerful endpoint. Input a topic and receive a complete, ready-to-publish video with professional narration, background footage, and modern captions.

## 🎯 **What It Does**

1. **🤖 AI Script Generation**: Creates engaging scripts optimized for viral content
2. **🎵 Text-to-Speech**: Generates high-quality narration audio
3. **🔍 Video Search**: Finds relevant background videos using AI
4. **🎬 Video Composition**: Syncs footage with audio timing
5. **📝 Caption Generation**: Adds modern TikTok-style captions
6. **🎨 Final Rendering**: Produces ready-to-publish MP4 video

## Quick Start

### Basic Video Generation

```bash
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "amazing ocean facts"
  }'
```

### Auto-Generated Topic

```bash
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_topic": true,
    "script_type": "facts"
  }'
```

### Custom Script Mode

```bash
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "custom_script": "Welcome to this amazing video about space exploration. Did you know that there are more stars in the universe than grains of sand on all the beaches on Earth?",
    "voice": "af_bella",
    "tts_provider": "kokoro",
    "media_type": "video",
    "footage_provider": "pexels"
  }'
```

### Image-to-Video Mode

```bash
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "beautiful nature scenes",
    "media_type": "image",
    "effect_type": "ken_burns",
    "zoom_speed": 15,
    "add_captions": true,
    "caption_style": "viral_bounce"
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Progress

```bash
curl "http://localhost:8000/api/v1/ai/footage-to-video/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key"
```

**Response (when completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "final_video_url": "https://s3.amazonaws.com/bucket/videos/final_video_123.mp4",
    "video_with_audio_url": "https://s3.amazonaws.com/bucket/videos/video_no_captions_123.mp4",
    "script_generated": "Amazing ocean facts you didn't know: The ocean contains 99% of Earth's living space...",
    "audio_url": "https://s3.amazonaws.com/bucket/audio/narration_123.wav",
    "background_videos_used": [
      "https://player.vimeo.com/external/ocean_waves.mp4",
      "https://player.vimeo.com/external/deep_sea.mp4"
    ],
    "srt_url": "https://s3.amazonaws.com/bucket/captions/video_123.ass",
    "video_duration": 47.3,
    "processing_time": 182.5,
    "word_count": 134,
    "segments_count": 16
  },
  "error": null
}
```

## API Reference

### POST `/api/v1/ai/footage-to-video`

Generate a complete video from a topic using the end-to-end AI pipeline.

#### Request Body

**Core Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | `null` | Topic for video generation (max 200 chars). Optional if `auto_topic` is true or `custom_script` is provided |
| `sync` | boolean | `false` | If true, return response immediately. If false (default), create async job |
| `custom_script` | string | `null` | Custom script text to use instead of generating from topic (max 10000 chars) |
| `auto_topic` | boolean | `false` | Automatically discovers trending topics based on script_type using web search |

#### Script Generation Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script_provider` | string | `"auto"` | AI provider for script generation: `"openai"`, `"groq"`, `"auto"`, or `"manual"` |
| `script_type` | string | `"facts"` | Type of script: `"facts"`, `"story"`, `"educational"`, `"motivation"`, `"prayer"`, `"pov"`, `"conspiracy"`, `"life_hacks"`, `"would_you_rather"`, `"before_you_die"`, `"dark_psychology"`, `"reddit_stories"`, `"shower_thoughts"`, `"life_wisdom"`, `"daily_news"` |
| `max_duration` | integer | `50` | Maximum video duration in seconds (5-900) |
| `language` | string | `"en"` | Language for script generation and TTS (use language codes like `"en"`, `"fr"`, `"es"`, `"de"`) |

#### Text-to-Speech Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voice` | string | `"af_alloy"` | Voice for text-to-speech narration |
| `tts_provider` | string | `null` | TTS provider: `"kokoro"` or `"edge"` |
| `tts_speed` | float | `1.0` | Speech speed multiplier (0.5-2.0) |
| `enable_voice_over` | boolean | `true` | Enable voice-over narration in the video |
| `enable_built_in_audio` | boolean | `false` | Enable built-in audio from AI video models (e.g., ambient sounds from VEO) |

#### Video Search Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_orientation` | string | `"landscape"` | Video orientation: `"landscape"`, `"portrait"`, or `"square"` |
| `segment_duration` | float | `3.0` | Target duration for each background video segment (2.0-8.0s) |

#### Footage Provider Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `footage_provider` | string | `"pexels"` | Video footage provider for background clips: `"pexels"`, `"unsplash"`, `"pixabay"`, `"ai_generated"` |
| `search_safety` | string | `"moderate"` | Content safety filter level: `"strict"`, `"moderate"`, `"off"` |
| `footage_quality` | string | `"high"` | Background footage quality preference: `"standard"`, `"high"`, `"ultra"` |
| `search_terms_per_scene` | integer | `3` | Number of search terms to generate per video segment (1-10) |

#### Video Search Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_orientation` | string | `"landscape"` | Video orientation: `"landscape"`, `"portrait"`, `"square"` |
| `segment_duration` | float | `3.0` | Target duration per video segment (2.0-8.0s) |
| `search_safety` | string | `"moderate"` | Content safety filter level: `"strict"`, `"moderate"`, `"off"` |
| `footage_quality` | string | `"high"` | Background footage quality: `"standard"`, `"high"`, `"ultra"` |
| `search_terms_per_scene` | integer | `3` | Number of search terms to generate per video segment |

#### Image Generation Options (when `media_type` is `"image"`)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `effect_type` | string | `"zoom"` | Video effect type: `"none"`, `"zoom"`, `"pan"`, `"ken_burns"`, `"fade"`, `"slide"` |
| `zoom_speed` | integer | `25` | Zoom speed for zoom effect (1-100) |
| `pan_direction` | string | `null` | Direction of pan effect when `effect_type` is `"pan"` |
| `ken_burns_keypoints` | array | `null` | Keypoints for Ken Burns effect when `effect_type` is `"ken_burns"` |

#### Background Music Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `background_music` | string | `"none"` | Background music option: `"none"` for no music, `"ai_generate"` for AI-generated music, or a mood name like `"chill"`, `"happy"`, `"dark"` for stock music with that mood |
| `background_music_volume` | float | `0.3` | Background music volume level (0.0-1.0) |
| `music_duration` | integer | `null` | Maximum duration for background music in seconds (10-900). If not specified, uses video duration |

#### Caption Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_captions` | boolean | `true` | Whether to add captions to the video |
| `caption_style` | string | `"viral_bounce"` | Caption style: `"classic"`, `"viral_bounce"`, `"viral_cyan"`, `"viral_yellow"`, `"viral_green"`, `"bounce"`, `"typewriter"`, `"fade_in"`, `"highlight"`, `"underline"`, `"word_by_word"`, `"modern_neon"`, `"cinematic_glow"`, `"social_pop"` |
| `caption_color` | string | `null` | Base text color for captions (e.g., `"#FFFFFF"`). When specified, overrides the style default |

#### Output Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resolution` | string | `null` | Video resolution string (e.g., `"1080x1920"`) |
| `output_width` | integer | `null` | Output video width |
| `output_height` | integer | `null` | Output video height |
| `frame_rate` | integer | `30` | Output frame rate (typically 24, 30, or 60) |

#### Output Options
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `resolution` | string | `null` | Video resolution string (e.g., `"1080x1920"`) |
| `output_width` | integer | `null` | Output video width |
| `output_height` | integer | `null` | Output video height |
| `frame_rate` | integer | `30` | Output frame rate (24-60) |

### GET `/api/v1/ai/footage-to-video/{job_id}`

Get the status and results of a footage-to-video generation job.

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `final_video_url` | string | URL to the final generated video with captions |
| `video_with_audio_url` | string | URL to the video with audio but without captions |
| `script_generated` | string | The AI-generated script text |
| `audio_url` | string | URL to the TTS audio file |
| `background_videos_used` | array | URLs of background videos used |
| `srt_url` | string | URL to ASS caption file with advanced styling (if captions enabled) |
| `video_duration` | float | Duration of final video in seconds |
| `processing_time` | float | Total processing time in seconds |
| `word_count` | integer | Word count of generated script |
| `segments_count` | integer | Number of background video segments |
| `caption_style` | string | Caption style used for the video |

## Script Types

The API supports 14 different script types, each optimized for specific content styles and viral performance on social media platforms:

### **Core Content Types**

**Facts (`"facts"`)** - *Best for viral educational content*
- Optimized for viral fact-based content
- List format with engaging statistics
- Perfect for YouTube Shorts and TikTok
- Example: "5 ocean facts that will blow your mind"

**Story (`"story"`)** - *Best for narrative content*
- Narrative-driven content with character development
- Compelling hooks and emotional engagement
- Great for storytelling channels
- Example: "The mysterious case of the vanishing ship"

**Educational (`"educational"`)** - *Best for instructional content*
- Step-by-step instructional content
- Clear learning objectives and takeaways
- Ideal for how-to and tutorial videos
- Example: "How to improve your memory in 5 steps"

### **Viral Social Media Types**

**Motivation (`"motivation"`)** - *Best for inspirational content*
- Powerful inspirational content with high energy
- Personal empowerment messages and success stories
- Perfect for fitness, self-improvement, and success channels
- Example: "Stop making excuses and start living your dream life"

**POV (`"pov"`)** - *Best for TikTok-style content*
- Point-of-view scenarios ("POV: You are...")
- Immersive second-person perspective
- Viral TikTok and Instagram Reels format
- Example: "POV: You discover your roommate is secretly famous"

**Would You Rather (`"would_you_rather"`)** - *Best for engagement*
- Engaging dilemma scenarios with impossible choices
- Drives high viewer engagement and comments
- Perfect for interactive content and polls
- Example: "Would you rather read minds or be invisible?"

**Shower Thoughts (`"shower_thoughts"`)** - *Best for philosophical content*
- Mind-bending observations about everyday life
- Philosophical insights and thought experiments
- Simple but profound realizations
- Example: "If you're waiting for the waiter, aren't you the waiter?"

### **Niche Content Types**

**Prayer (`"prayer"`)** - *Best for spiritual content*
- Spiritual and uplifting content with peaceful tone
- Gratitude, blessing themes, and universal values
- Respectful approach to faith and spirituality
- Example: "A prayer for peace and strength in difficult times"

**Conspiracy (`"conspiracy"`)** - *Best for mystery content*
- Mystery and intrigue with historical focus
- "What they don't want you to know" approach
- Engaging evidence presentation and theories
- Example: "The government document they tried to hide"

**Life Hacks (`"life_hacks"`)** - *Best for practical content*
- Quick, actionable tips and problem-solving
- Money/time saving benefits and clever solutions
- "You'll wish you knew this sooner" format
- Example: "This 30-second trick will change how you cook"

**Before You Die (`"before_you_die"`)** - *Best for bucket-list content*
- Urgent bucket-list experiences and FOMO content
- Life-changing moments and inspirational goals
- Motivates action and life fulfillment
- Example: "5 experiences you must have before you die"

**Dark Psychology (`"dark_psychology"`)** - *Best for educational psychology*
- Educational content about human behavior
- Manipulation awareness and psychological defense
- Ethical approach to influence and persuasion
- Example: "3 psychological tricks people use to control you"

**Reddit Stories (`"reddit_stories"`)** - *Best for dramatic narratives*
- Dramatic personal narratives and confessions
- Plot twists, relationship drama, and moral dilemmas
- Engaging story-driven content with suspense
- Example: "My neighbor has been stealing my packages for months"

**Daily News (`"daily_news"`)** - *Best for current events content*
- Real-time news updates and breaking stories
- Current events and trending topics
- Factual reporting with professional tone
- AI-researched content using Google Search and Perplexity
- Context and background information for better understanding
- Example: "Breaking: Scientists achieve 47% solar panel efficiency breakthrough - here's what this means for your electricity bills"

### **Script Type Selection Guide**

| Platform | Recommended Types | Duration | Style |
|----------|------------------|----------|--------|
| **TikTok** | `pov`, `shower_thoughts`, `would_you_rather` | 15-30s | Fast, engaging |
| **YouTube Shorts** | `facts`, `motivation`, `life_hacks`, `daily_news` | 30-60s | Educational, viral |
| **Instagram Reels** | `story`, `before_you_die`, `motivation` | 30-60s | Inspirational, visual |
| **Spiritual Channels** | `prayer`, `motivation`, `story` | 45-90s | Peaceful, uplifting |
| **Educational** | `educational`, `facts`, `dark_psychology` | 60-120s | Informative, detailed |
| **News Channels** | `daily_news`, `facts` | 30-90s | Professional, informative |

## Advanced Configuration

### Auto Topic Generation

When you don't have a specific topic in mind, you can use the `auto_topic` parameter to let AI generate an engaging topic for you:

```json
{
  "auto_topic": true,
  "script_type": "facts",
  "max_duration": 45,
  "video_orientation": "portrait"
}
```

**How Auto Topic Works:**
1. **AI Analysis**: The system analyzes current trends and popular content types
2. **Topic Generation**: Creates an engaging, viral-optimized topic based on the selected script type
3. **Content Creation**: Proceeds with normal video generation using the AI-generated topic

**Best Practices for Auto Topic:**
- Specify a `script_type` to guide topic generation (e.g., "facts", "motivation", "pov")
- Use with trending script types like "facts" or "would_you_rather" for viral content
- Combine with appropriate video orientation for your target platform
- Perfect for content creators who need fresh ideas regularly

**Example Auto-Generated Topics:**
- Script type "facts": "Mind-blowing facts about the human brain that will shock you"
- Script type "motivation": "Why your biggest failure is actually your greatest opportunity"
- Script type "pov": "POV: You discover your best friend has been lying about everything"

### MoviePy Composition (Recommended)

**New in v2.0**: MoviePy composition is now the default for better timing precision and quality. The system uses a hybrid approach:

1. **FFmpeg preprocessing** for excellent orientation handling
2. **MoviePy composition** for precise timing control 
3. **Automatic fallback** to FFmpeg if MoviePy fails

```json
{
  "topic": "amazing facts about the brain",
  "use_moviepy": true,  // Default: true
  "video_orientation": "portrait"
}
```

**Benefits of MoviePy:**
- ✅ **Perfect timing sync** between audio and video
- ✅ **Seamless transitions** between video segments
- ✅ **Better quality** output with precise frame control
- ✅ **Automatic fallback** to FFmpeg if needed

### Multi-Language Support

Generate content in any language by setting the `language` parameter:

```json
{
  "topic": "Faits incroyables sur l'océan",
  "language": "french",
  "voice": "fr-FR-DeniseNeural",
  "tts_provider": "edge"
}
```

**Supported Languages:**
- `"en"` - English (default)
- `"french"` - French
- `"spanish"` - Spanish  
- `"german"` - German
- `"italian"` - Italian
- `"portuguese"` - Portuguese
- And many more...

**Language Flow:**
1. **Script generation** - Created in specified language
2. **TTS audio** - Matches script language automatically
3. **Video search** - Always in English for better results
4. **Captions** - Auto-detect from script content

### YouTube Shorts Optimization

```json
{
  "topic": "mind-blowing space facts",
  "script_type": "facts",
  "max_duration": 45,
  "video_orientation": "portrait",
  "output_width": 1080,
  "output_height": 1920,
  "caption_style": "viral_bounce",
  "voice": "af_alloy",
  "tts_speed": 1.1,
  "use_moviepy": true,
  "language": "en"
}
```

### TikTok-Style POV Content

```json
{
  "topic": "first day at your dream job",
  "script_type": "pov",
  "max_duration": 30,
  "video_orientation": "portrait",
  "caption_style": "typewriter",
  "voice": "en-US-AvaNeural",
  "tts_provider": "edge",
  "tts_speed": 1.2,
  "use_moviepy": true,
  "language": "en"
}
```

### Motivational Content

```json
{
  "topic": "overcoming fear of failure",
  "script_type": "motivation",
  "max_duration": 60,
  "video_orientation": "portrait",
  "caption_style": "viral_bounce",
  "voice": "af_alloy",
  "tts_speed": 1.0,
  "segment_duration": 3.5,
  "use_moviepy": true,
  "language": "en"
}
```

### Spiritual/Prayer Content

```json
{
  "topic": "finding peace in difficult times",
  "script_type": "prayer",
  "max_duration": 75,
  "video_orientation": "square",
  "output_width": 1080,
  "output_height": 1080,
  "caption_style": "fade_in",
  "voice": "en-US-AriaNeural",
  "tts_provider": "edge",
  "tts_speed": 0.9
}
```

### Interactive Engagement Content

```json
{
  "topic": "impossible life choices",
  "script_type": "would_you_rather",
  "max_duration": 40,
  "video_orientation": "portrait",
  "caption_style": "viral_bounce",
  "voice": "af_echo",
  "add_captions": true,
  "segment_duration": 3.0
}
```

### Educational Psychology

```json
{
  "topic": "how to read body language",
  "script_type": "dark_psychology",
  "max_duration": 90,
  "video_orientation": "landscape",
  "caption_style": "fade_in",
  "voice": "en-US-AriaNeural",
  "tts_provider": "edge",
  "segment_duration": 4.0
}
```

### Daily News Content

```json
{
  "topic": "renewable energy breakthrough",
  "script_type": "daily_news",
  "max_duration": 60,
  "video_orientation": "portrait",
  "caption_style": "fade_in",
  "voice": "en-US-AriaNeural",
  "tts_provider": "edge",
  "tts_speed": 1.0,
  "segment_duration": 3.5
}
```

### Custom Caption Styling

```json
{
  "topic": "fitness motivation tips",
  "caption_properties": {
    "style": "viral_bounce",
    "font_family": "Arial Black",
    "font_size": 36,
    "bold": true,
    "line_color": "#FFFFFF",
    "word_color": "#00FFFF",
    "outline_color": "black",
    "outline_width": 3,
    "position": "bottom_center",
    "max_words_per_line": 3,
    "all_caps": true
  }
}
```

**Available Caption Styles:**
- `viral_bounce` - Enhanced bounce effect with single-layer rendering
- `viral_cyan` - Cyan-colored bouncing captions
- `viral_yellow` - Yellow-colored bouncing captions
- `viral_green` - Green-colored bouncing captions
- `bounce` - Standard bounce animation
- `highlight` - Word-by-word highlighting with color transitions
- `karaoke` - Karaoke-style progressive word reveal
- `typewriter` - Character-by-character typing effect
- `fade_in` - Smooth fade-in animation for each line
- `classic` - Simple, clean text display
- `underline` - Underline effect for active words
- `word_by_word` - Individual word animations
- `modern_neon` - Neon glow effects
- `cinematic_glow` - Cinematic lighting effects
- `social_pop` - Social media trending effects

**Caption Positioning:**
- Automatically adjusts margins based on video dimensions
- Bottom positions: 180px from edge (avoids player controls)
- Top positions: 150px from edge (prevents cutoff)
- Left/Right/Center: 80px margins for title-safe area

## Enhanced Caption System (v2.0)

The Footage-to-Video Pipeline now uses the **Unified Caption System** - the same reliable engine powering all caption endpoints across the platform. This ensures consistent, high-quality caption rendering with modern effects.

### Key Improvements

**✅ Single-Layer Rendering**
- Fixed the dual caption display bug
- Clean, professional output without overlay issues
- Proper bounce effects without text duplication

**✅ Better Positioning**
- Captions positioned 180px from bottom edge
- No more captions hidden by video player controls
- Responsive margins for all video orientations

**✅ Advanced Styling**
- Support for all modern caption styles
- Word-level timing synchronization
- Embedded animations in ASS format
- Professional typography and effects

**✅ Reliable Fallback**
- Primary: Uses unified caption system
- Fallback: Original custom implementation as backup
- Automatic error handling and recovery

### Technical Details

The pipeline now:
1. **Creates word timestamps** from the generated script text
2. **Uses the unified caption engine** for consistent rendering
3. **Applies responsive properties** based on video dimensions
4. **Generates ASS files** with embedded animations
5. **Falls back gracefully** if needed

This ensures that captions generated by the Footage-to-Video Pipeline are identical in quality and behavior to those created through the dedicated `/add-captions` endpoint.

## Processing Pipeline Details

The Footage-to-Video Pipeline processes videos through several stages to create professional content:

### Stage 1: Script Generation (5-15 seconds)
- Analyzes topic for content type and audience
- Generates viral-optimized script using AI
- Calculates target word count based on duration
- Provides fallback content if AI fails

### Stage 2: Audio Generation (10-30 seconds)
- Converts script to high-quality speech
- Supports multiple TTS providers
- Optimizes audio for video synchronization
- Generates timing metadata for captions

### Stage 3: Video Query Generation (3-8 seconds)
- Analyzes script for visual concepts
- Generates timing-aware search queries
- Ensures visual concreteness for stock footage
- Creates segment timeline for video composition

### Stage 4: Background Video Search (15-45 seconds)
- Multi-provider search: Pexels and Pixabay
- Enhanced search queries for news content (daily_news script type)
- Filters by resolution, duration, and orientation
- Avoids duplicate videos within project
- Downloads and prepares video segments
- Intelligent fallback between providers

### Stage 5: Video Composition (30-90 seconds)
- Syncs background videos with audio timing
- Handles video trimming and looping
- Ensures consistent quality and format
- Creates seamless transitions between segments

### Stage 6: Caption Addition (15-30 seconds)
- **Uses Unified Caption System**: Now powered by the same reliable caption engine used across all endpoints
- **Word-Level Timing**: Creates artificial word timestamps from script text for perfect synchronization
- **Modern Styling**: Supports all caption styles including viral_bounce, highlight, karaoke, typewriter, fade_in
- **Fixed Positioning**: Captions positioned 180px from bottom edge to avoid player controls
- **Single-Layer Rendering**: No more dual caption display bugs - clean, professional output
- **ASS Format Generation**: Creates advanced subtitle files with embedded animations and effects
- **Fallback Support**: Maintains original custom implementation as backup if needed

### Stage 7: Final Rendering (20-60 seconds)
- Combines all elements into final video
- Applies quality optimization
- Uploads to S3 storage
- Generates preview thumbnails

## Performance Characteristics

### Processing Time by Duration

| Video Length | Typical Processing Time | Peak Time |
|--------------|------------------------|-----------|
| 20-30 seconds | 90-150 seconds | 180 seconds |
| 30-45 seconds | 120-180 seconds | 240 seconds |
| 45-60 seconds | 150-240 seconds | 300 seconds |
| 60+ seconds | 180-300 seconds | 360 seconds |

### Resource Usage

- **CPU**: High during video composition and rendering
- **Memory**: 2-4GB peak during processing
- **Storage**: ~100MB per generated video
- **Network**: High bandwidth for stock video downloads

### Optimization Tips

1. **Shorter Videos**: Process faster and work better for social media
2. **Portrait Orientation**: Better for TikTok and Instagram Reels
3. **Groq Provider**: Faster script generation than OpenAI
4. **Edge TTS**: Faster than Kokoro for simple voices
5. **Lower Resolution**: Use 720p for faster processing if quality allows

## Error Handling

### Common Failures and Solutions

**Script Generation Failure:**
```json
{
  "status": "failed",
  "error": "Pipeline failed: Script generation failed: No AI provider available"
}
```
*Solution: Ensure OPENAI_API_KEY or GROQ_API_KEY is set*

**Video Search Failure:**
```json
{
  "status": "failed", 
  "error": "Pipeline failed: No suitable videos found for topic"
}
```
*Solution: Try a more general topic or different video orientation*

**TTS Failure:**
```json
{
  "status": "failed",
  "error": "Pipeline failed: Audio generation failed: TTS service unavailable"
}
```
*Solution: Check TTS service status or try different provider*

**S3 Upload Failure:**
```json
{
  "status": "failed",
  "error": "Pipeline failed: S3 upload failed: Invalid credentials"
}
```
*Solution: Verify S3 credentials and bucket permissions*

### Retry Strategy

```python
import time
import requests

def generate_video_with_retry(topic, api_key, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Create job
            response = requests.post(
                "http://localhost:8000/api/v1/ai/footage-to-video",
                headers={"X-API-Key": api_key},
                json={"topic": topic}
            )
            job_id = response.json()["job_id"]
            
            # Poll for completion
            while True:
                status_response = requests.get(
                    f"http://localhost:8000/api/v1/ai/footage-to-video/{job_id}",
                    headers={"X-API-Key": api_key}
                )
                status = status_response.json()
                
                if status["status"] == "completed":
                    return status["result"]
                elif status["status"] == "failed":
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} failed: {status['error']}")
                        break  # Retry
                    else:
                        raise Exception(status["error"])
                
                time.sleep(5)  # Check every 5 seconds
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(10)  # Wait before retry

# Usage
result = generate_video_with_retry("amazing science facts", "your_api_key")
print(f"Video generated: {result['final_video_url']}")
```

## Integration Examples

### Python: Batch Video Generation

```python
import asyncio
import aiohttp
import time

class BatchVideoGenerator:
    def __init__(self, api_key, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    async def generate_video(self, session, topic, config=None):
        config = config or {}
        payload = {"topic": topic, **config}
        
        # Create job
        async with session.post(
            f"{self.base_url}/api/v1/ai/footage-to-video",
            headers=self.headers,
            json=payload
        ) as response:
            job_data = await response.json()
            job_id = job_data["job_id"]
        
        # Poll for completion
        while True:
            async with session.get(
                f"{self.base_url}/api/v1/ai/footage-to-video/{job_id}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                status = await response.json()
                
                if status["status"] == "completed":
                    return status["result"]
                elif status["status"] == "failed":
                    raise Exception(f"Video generation failed: {status['error']}")
                
                await asyncio.sleep(5)
    
    async def generate_batch(self, topics_config):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for topic, config in topics_config.items():
                task = self.generate_video(session, topic, config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return dict(zip(topics_config.keys(), results))

# Usage
generator = BatchVideoGenerator("your_api_key")

topics = {
    "ocean mysteries": {
        "script_type": "facts",
        "video_orientation": "portrait",
        "caption_style": "viral_bounce"
    },
    "space exploration": {
        "script_type": "educational",
        "max_duration": 60,
        "voice": "en-US-AriaNeural"
    },
    "cooking basics": {
        "script_type": "educational",
        "segment_duration": 4.0,
        "caption_style": "fade_in"
    },
    "auto_generated_facts": {
        "auto_topic": True,
        "script_type": "facts",
        "video_orientation": "portrait",
        "caption_style": "viral_bounce"
    },
    "auto_generated_motivation": {
        "auto_topic": True,
        "script_type": "motivation",
        "max_duration": 60,
        "voice": "af_alloy"
    }
}

results = asyncio.run(generator.generate_batch(topics))

for topic, result in results.items():
    if isinstance(result, Exception):
        print(f"Failed to generate video for '{topic}': {result}")
    else:
        print(f"Generated video for '{topic}': {result['final_video_url']}")
```

### JavaScript: Real-time Progress Tracking

```javascript
class VideoGenerator {
  constructor(apiKey, baseUrl = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.headers = {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    };
  }

  async generateVideoWithProgress(topic, config = {}, onProgress) {
    // Create job
    const response = await fetch(`${this.baseUrl}/api/v1/ai/footage-to-video`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ topic, ...config })
    });
    
    const { job_id } = await response.json();
    
    // Track progress
    const stages = [
      'Script Generation',
      'Audio Generation', 
      'Video Search',
      'Video Composition',
      'Caption Addition',
      'Final Rendering'
    ];
    
    let currentStage = 0;
    const startTime = Date.now();
    
    while (true) {
      const statusResponse = await fetch(
        `${this.baseUrl}/api/v1/ai/footage-to-video/${job_id}`,
        { headers: { 'X-API-Key': this.apiKey } }
      );
      
      const status = await statusResponse.json();
      
      if (status.status === 'processing') {
        // Estimate progress based on time elapsed
        const elapsed = (Date.now() - startTime) / 1000;
        const estimatedStage = Math.min(
          Math.floor(elapsed / 30), 
          stages.length - 1
        );
        
        if (estimatedStage > currentStage) {
          currentStage = estimatedStage;
        }
        
        if (onProgress) {
          onProgress({
            stage: stages[currentStage],
            progress: (currentStage + 1) / stages.length,
            elapsed: elapsed
          });
        }
      } else if (status.status === 'completed') {
        if (onProgress) {
          onProgress({
            stage: 'Completed',
            progress: 1.0,
            elapsed: (Date.now() - startTime) / 1000
          });
        }
        return status.result;
      } else if (status.status === 'failed') {
        throw new Error(status.error);
      }
      
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
}

// Usage with progress tracking
const generator = new VideoGenerator('your_api_key');

// Generate video with specific topic
const result = await generator.generateVideoWithProgress(
  'incredible animal abilities',
  {
    script_type: 'facts',
    video_orientation: 'portrait',
    caption_style: 'viral_bounce'
  },
  (progress) => {
    console.log(`${progress.stage}: ${Math.round(progress.progress * 100)}% (${Math.round(progress.elapsed)}s)`);
  }
);

console.log('Video completed:', result.final_video_url);

// Generate video with auto-generated topic
const autoResult = await generator.generateVideoWithProgress(
  null, // No topic needed when using auto_topic
  {
    auto_topic: true,
    script_type: 'motivation',
    video_orientation: 'portrait',
    caption_style: 'viral_bounce',
    max_duration: 45
  },
  (progress) => {
    console.log(`Auto-topic video - ${progress.stage}: ${Math.round(progress.progress * 100)}%`);
  }
);

console.log('Auto-generated video completed:', autoResult.final_video_url);
console.log('Generated topic was:', autoResult.script_generated.substring(0, 50) + '...');
```

### React: Video Generation Dashboard

```jsx
import React, { useState } from 'react';

function VideoGenerationDashboard() {
  const [topic, setTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState({ stage: '', progress: 0 });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const generateVideo = async () => {
    setIsGenerating(true);
    setError(null);
    setResult(null);
    
    try {
      const generator = new VideoGenerator('your_api_key');
      const videoResult = await generator.generateVideoWithProgress(
        topic,
        {
          script_type: 'facts',
          video_orientation: 'portrait'
        },
        setProgress
      );
      
      setResult(videoResult);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="video-dashboard">
      <h1>AI Video Generator</h1>
      
      <div className="input-section">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter video topic (e.g., 'amazing space facts')"
          disabled={isGenerating}
        />
        <button 
          onClick={generateVideo}
          disabled={isGenerating || !topic.trim()}
        >
          {isGenerating ? 'Generating...' : 'Generate Video'}
        </button>
      </div>

      {isGenerating && (
        <div className="progress-section">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progress.progress * 100}%` }}
            />
          </div>
          <p>{progress.stage} ({Math.round(progress.progress * 100)}%)</p>
        </div>
      )}

      {result && (
        <div className="result-section">
          <h2>Video Generated Successfully!</h2>
          <video controls width="400">
            <source src={result.final_video_url} type="video/mp4" />
          </video>
          <div className="metadata">
            <p><strong>Duration:</strong> {result.video_duration}s</p>
            <p><strong>Word Count:</strong> {result.word_count}</p>
            <p><strong>Processing Time:</strong> {Math.round(result.processing_time)}s</p>
          </div>
          <div className="downloads">
            <a href={result.final_video_url} download>Download Video</a>
            <a href={result.audio_url} download>Download Audio</a>
            {result.srt_url && <a href={result.srt_url} download>Download Captions</a>}
          </div>
        </div>
      )}

      {error && (
        <div className="error-section">
          <h2>Generation Failed</h2>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}

export default VideoGenerationDashboard;
```

## Environment Variables

```bash
# Required for complete functionality
API_KEY=your_secret_api_key_here

# AI Script Generation (at least one required)
OPENAI_API_KEY=sk-...                      # OpenAI API key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: Custom OpenAI-compatible endpoint
OPENAI_MODEL=gpt-4o                        # Optional: Custom model name
GROQ_API_KEY=gsk_...                       # Groq API key (alternative)
GROQ_BASE_URL=http://localhost:8080/v1     # Optional: Custom Groq-compatible endpoint
GROQ_MODEL=mixtral-8x7b-32768              # Optional: Custom Groq model

# Stock Video Search
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key

# News Research (for daily_news script type)
GOOGLE_SEARCH_API_KEY=your_google_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
PERPLEXITY_API_KEY=your_perplexity_api_key
PERPLEXITY_MODEL=llama-3.1-sonar-small-127k-online  # Optional: Custom Perplexity model

# S3 Storage
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
S3_REGION=your_s3_region

# TTS Services (optional)
KOKORO_API_URL=http://kokoro-tts:8880/v1/audio/speech

# Redis (optional, for job persistence)
REDIS_URL=redis://redis:6379/0
```

## Best Practices

### Topic Selection

**Manual Topic Selection:**
1. **Be Specific**: "deep sea creatures" > "animals"
2. **Use Engaging Words**: "shocking", "incredible", "mind-blowing"
3. **Target Audience**: Consider who will watch the video
4. **Trending Topics**: Research current interests and trends

**Auto Topic Generation:**
1. **Use When**: You need fresh content ideas or want to explore trending topics
2. **Combine with Script Types**: Pair `auto_topic: true` with specific script types for targeted content
3. **Perfect for**: Content creators, social media managers, or automated content pipelines
4. **Best Script Types**: "facts", "motivation", "pov", "would_you_rather" work well with auto-generation
5. **Quality Assurance**: Auto-generated topics are optimized for viral potential and engagement

### Content Strategy

1. **Hook in First 3 Seconds**: Topics that start with impact
2. **List-Based Content**: "10 facts about...", "5 ways to..."
3. **Question Format**: "Did you know that...?", "What if..."
4. **Emotional Triggers**: Curiosity, surprise, amazement

### Platform Optimization

**YouTube Shorts:**
- Portrait orientation (1080x1920)
- 45-60 second duration
- Viral bounce captions
- Fast-paced content

**TikTok:**
- Portrait orientation
- 15-30 second duration  
- Strong visual elements
- Trending topics

**Instagram Reels:**
- Square or portrait orientation
- 30-60 second duration
- High-quality visuals
- Educational content performs well

### Quality Optimization

1. **Voice Selection**: Match voice to content tone
2. **Caption Style**: Modern effects for social media
3. **Background Videos**: Ensure visual relevance
4. **Script Quality**: Let AI optimize for engagement

## Troubleshooting

### Performance Issues

**Slow Processing:**
- Check network connection for video downloads
- Verify S3 upload speed
- Monitor system resources during processing

**High Memory Usage:**
- Close other applications during video generation
- Use lower resolution for testing
- Process videos sequentially instead of in parallel

**Timeout Errors:**
- Increase request timeout in client
- Use shorter videos for testing
- Check service health status

### Quality Issues

**Poor Video Matching:**
- Try more specific topics
- Use better visual language in topics
- Consider manual video selection

**Audio-Video Sync:**
- Check TTS speed settings
- Verify video segment durations
- Review caption timing

**Low-Quality Output:**
- Use higher resolution settings
- Select "large" size for stock videos
- Check S3 video quality

## Next Steps

- Explore [AI Script Generation](ai-script-generation.md) for standalone script creation
- Use [AI Video Search](ai-video-search.md) for custom video curation
- Enhance with [Video Processing](videos/README.md) for advanced editing
- Integrate with [Audio Processing](audio/README.md) for custom soundtracks

---

*For more examples and advanced usage, see the [examples directory](examples/).*