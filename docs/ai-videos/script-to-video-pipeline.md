# Script-to-Video Pipeline with AI-Generated Images

The Script-to-Video Pipeline is an advanced AI-powered system that creates complete videos from topics using AI-generated images instead of stock footage. This pipeline combines multiple AI services to produce unique, engaging video content with custom visuals.

## 🎯 Overview

Unlike the traditional footage-to-video pipeline that uses Pexels stock videos, the aiimage-to-video pipeline generates unique images for each segment using Together.ai's FLUX model, creating completely original visual content.

**Pipeline Flow:**
1. **Script Generation** → AI creates engaging script from topic
2. **Audio Synthesis** → Text-to-speech conversion
3. **Audio Transcription** → Extract precise timing segments
4. **Image Prompt Generation** → AI creates visual prompts for each segment
5. **Image Generation** → Together.ai FLUX creates high-quality images
6. **Video Creation** → Convert images to videos with dynamic effects
7. **Background Music** → Optional AI-generated music
8. **Video Composition** → Sync everything with perfect timing
9. **Caption Addition** → Modern animated captions
10. **Final Rendering** → Ready-to-publish video

## 🚀 Quick Start

### Basic Request

```bash
curl -X POST "http://localhost:8000/v1/ai/aiimage-to-video" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "amazing ocean facts",
    "script_type": "facts",
    "language": "en",
    "video_orientation": "portrait",
    "add_captions": true
  }'
```

### Response

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Check Status

```bash
curl -X GET "http://localhost:8000/v1/ai/aiimage-to-video/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your-api-key"
```

## 📋 API Reference

### Endpoint

```
POST /v1/ai/aiimage-to-video
GET /v1/ai/aiimage-to-video/{job_id}
```

### Request Parameters

#### Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | null | The topic for video generation (required if auto_topic is false) |
| `auto_topic` | boolean | false | Automatically discover trending topics |
| `language` | string | "en" | Language code for script and TTS |
| `max_duration` | integer | 50 | Maximum video duration in seconds (20-600) |

#### Script Generation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script_provider` | string | "auto" | AI provider: "openai", "groq", or "auto" |
| `script_type` | string | "facts" | Type of script (see Script Types below) |

#### Image Generation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_provider` | string | "together" | Image provider (currently only "together") |
| `image_model` | string | env/auto | Model to use (uses TOGETHER_DEFAULT_MODEL) |
| `image_width` | integer | env/576 | Image width in pixels (uses TOGETHER_DEFAULT_WIDTH) |
| `image_height` | integer | env/1024 | Image height in pixels (uses TOGETHER_DEFAULT_HEIGHT) |
| `image_steps` | integer | env/4 | Inference steps (uses TOGETHER_DEFAULT_STEPS) |

#### Video Effects

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `effect_type` | string | "zoom" | Video effect: "zoom", "pan", "ken_burns", "fade" |
| `zoom_speed` | integer | 25 | Zoom speed for zoom effect (1-100) |
| `frame_rate` | integer | 50 | Video frame rate (24-60) |
| `segment_duration` | float | 3.0 | Duration per segment in seconds (2.0-8.0) |

#### Audio & Music

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voice` | string | "af_alloy" | TTS voice identifier |
| `tts_provider` | string | null | TTS provider: "kokoro" or "edge" |
| `tts_speed` | float | 1.0 | Speech speed multiplier (0.5-2.0) |
| `generate_background_music` | boolean | true | Whether to generate background music |
| `music_prompt` | string | null | Custom music prompt (AI-generated if null) |
| `background_music_volume` | float | 0.2 | Background music volume (0.0-1.0) |

#### Captions & Output

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `add_captions` | boolean | true | Whether to add captions |
| `caption_style` | string | "viral_bounce" | Caption style |
| `video_orientation` | string | "portrait" | "landscape", "portrait", or "square" |
| `output_width` | integer | auto | Output width (determined by orientation) |
| `output_height` | integer | auto | Output height (determined by orientation) |

### Response Format (Completed)

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "final_video_url": "https://s3.../final_video.mp4",
    "video_with_audio_url": "https://s3.../video_no_captions.mp4",
    "script_generated": "Did you know that the ocean contains...",
    "audio_url": "https://s3.../narration.wav",
    "generated_images": [
      {
        "url": "https://s3.../image_1.png",
        "prompt": "Majestic underwater coral reef with colorful fish...",
        "index": 0
      }
    ],
    "background_music_url": "https://s3.../music.wav",
    "music_prompt_generated": "Uplifting ambient ocean music...",
    "srt_url": "https://s3.../captions.srt",
    "video_duration": 45.2,
    "processing_time": 420.5,
    "word_count": 142,
    "segments_count": 8,
    "segments_data": [
      {
        "start_time": 0.0,
        "end_time": 5.2,
        "text": "Did you know that the ocean...",
        "prompt": "Vast ocean surface with sunlight..."
      }
    ]
  }
}
```

## 🎬 Script Types

Available script types for content generation:

- `facts` - Interesting facts and trivia
- `story` - Narrative storytelling
- `educational` - Educational content
- `motivation` - Motivational content with deep emotional resonance
- `life_wisdom` - Profound philosophical insights about life, relationships, and human nature
- `prayer` - Spiritual/religious content with biblical truth and comfort
- `pov` - Point of view scenarios
- `conspiracy` - Conspiracy theories
- `life_hacks` - Practical life tips
- `would_you_rather` - Choice scenarios
- `before_you_die` - Bucket list content
- `dark_psychology` - Psychological insights
- `reddit_stories` - Reddit-style stories
- `shower_thoughts` - Random thoughts/observations

## 🎨 Video Effects

### Zoom Effect
Progressive zoom into the image during playback.
```json
{
  "effect_type": "zoom",
  "zoom_speed": 25
}
```

### Pan Effect
Smooth horizontal panning across the image.
```json
{
  "effect_type": "pan"
}
```

### Ken Burns Effect
Classic documentary-style zoom with slight movement.
```json
{
  "effect_type": "ken_burns"
}
```

### Fade Effect
Fade in/out transitions.
```json
{
  "effect_type": "fade"
}
```

## 🔧 Environment Configuration

### Required Variables

```bash
# Together.ai Configuration (Required)
TOGETHER_API_KEY=your_together_api_key

# OpenAI Configuration (Required for image prompts)
OPENAI_API_KEY=your_openai_api_key

# Together.ai Defaults (Optional)
TOGETHER_DEFAULT_MODEL=black-forest-labs/FLUX.1-schnell
TOGETHER_DEFAULT_WIDTH=576
TOGETHER_DEFAULT_HEIGHT=1024
TOGETHER_DEFAULT_STEPS=4

# Together.ai Rate Limiting (Optional but recommended)
TOGETHER_MAX_RPS=2              # Max requests per second
TOGETHER_MAX_CONCURRENT=3       # Max concurrent requests
TOGETHER_RETRY_ATTEMPTS=3       # Retry attempts on failure
TOGETHER_BASE_DELAY=1.0         # Base delay between retries

# Redis & S3 (Required for core functionality)
REDIS_URL=redis://redis:6379/0
S3_ACCESS_KEY=your_s3_key
S3_SECRET_KEY=your_s3_secret
S3_BUCKET_NAME=your_bucket
S3_REGION=your_region
```

### Service Dependencies

The pipeline integrates with:
- **Together.ai**: FLUX image generation
- **OpenAI**: Script generation and image prompts
- **Kokoro TTS**: Voice synthesis
- **Meta MusicGen**: Background music
- **Whisper**: Audio transcription
- **Redis**: Job queuing and caching
- **S3**: File storage and CDN

## 📊 Processing Times

Typical processing times by video length:

| Duration | Images | Processing Time |
|----------|--------|----------------|
| 30s | 5-8 images | 3-5 minutes |
| 60s | 10-15 images | 5-8 minutes |
| 120s | 20-25 images | 8-12 minutes |

Processing time depends on:
- Number of script segments
- Image generation complexity
- Background music generation
- Video effects complexity

## 🎯 Use Cases

### Content Creation
- **YouTube Shorts**: Vertical videos with trending topics
- **Social Media**: Instagram Reels, TikTok content
- **Educational Content**: Custom visuals for learning
- **Marketing**: Branded content with unique imagery

### Automation
- **News Summaries**: Auto-generated visual news content
- **Fact Videos**: Educational fact compilation
- **Storytelling**: Visual narratives with AI art
- **Product Demos**: Custom visuals for explanations

## 🔍 Advanced Examples

### Educational Content with Custom Music

```json
{
  "topic": "ancient Roman engineering marvels",
  "script_type": "educational",
  "language": "en",
  "image_width": 1024,
  "image_height": 576,
  "video_orientation": "landscape",
  "effect_type": "ken_burns",
  "generate_background_music": true,
  "music_prompt": "Epic orchestral music with historical grandeur",
  "background_music_volume": 0.15,
  "caption_style": "classic"
}
```

### Viral Social Media Content

```json
{
  "auto_topic": true,
  "script_type": "facts",
  "language": "en",
  "video_orientation": "portrait",
  "effect_type": "zoom",
  "zoom_speed": 35,
  "frame_rate": 60,
  "caption_style": "viral_bounce",
  "generate_background_music": true
}
```

### Multi-Language Content

```json
{
  "topic": "cuisine française traditionnelle",
  "language": "fr",
  "script_type": "educational",
  "voice": "fr-FR-DeniseNeural",
  "tts_provider": "edge",
  "image_width": 768,
  "image_height": 768,
  "video_orientation": "square"
}
```

## 🚨 Error Handling

### Common Errors

#### Service Unavailable (503)
```json
{
  "detail": "Together.ai service is not available (TOGETHER_API_KEY required)"
}
```
**Solution**: Set the `TOGETHER_API_KEY` environment variable.

#### Bad Request (400)
```json
{
  "detail": "Either 'topic' must be provided or 'auto_topic' must be set to true"
}
```
**Solution**: Provide either a topic or enable auto_topic.

#### Processing Failed
```json
{
  "status": "failed",
  "error": "Pipeline failed: No segments found in transcription"
}
```
**Solution**: Check audio quality and TTS settings.

### Monitoring

Monitor job progress through status polling:

```python
import time
import requests

def wait_for_completion(job_id, api_key):
    while True:
        response = requests.get(
            f"http://localhost:8000/v1/ai/aiimage-to-video/{job_id}",
            headers={"X-API-Key": api_key}
        )
        status = response.json()["status"]
        
        if status == "completed":
            return response.json()["result"]
        elif status == "failed":
            raise Exception(response.json()["error"])
        
        time.sleep(10)  # Poll every 10 seconds
```

## 🎉 Best Practices

### Image Quality
- Use descriptive topics for better image prompts
- Higher steps (6-8) for better quality, slower generation
- Portrait orientation (576x1024) works best for social media

### Performance
- Keep segments under 5 seconds for smooth playback
- Use auto_topic for trending content discovery
- Enable background music for better engagement

### Content Strategy
- Match script_type to your audience
- Use appropriate languages for global reach
- Experiment with different video effects for variety

## 🔄 Migration from Topic-to-Video

If migrating from the footage-to-video pipeline:

### Key Differences
- Uses AI-generated images instead of stock videos
- Longer processing times due to image generation
- Unique visuals for every video
- More customization options for image generation

### Parameter Mapping
| Topic-to-Video | Script-to-Video | Notes |
|----------------|-----------------|-------|
| `video_orientation` | `video_orientation` | Same |
| `segment_duration` | `segment_duration` | Same |
| N/A | `image_model` | New: AI model selection |
| N/A | `effect_type` | New: Video effects |
| N/A | `zoom_speed` | New: Effect intensity |

### Migration Example

**Old (Topic-to-Video):**
```json
{
  "topic": "space facts",
  "video_orientation": "portrait",
  "segment_duration": 3.0
}
```

**New (Script-to-Video):**
```json
{
  "topic": "space facts",
  "video_orientation": "portrait",
  "segment_duration": 3.0,
  "effect_type": "zoom",
  "image_width": 576,
  "image_height": 1024
}
```

## 📈 Scaling & Performance

### Advanced Rate Limiting

The service implements intelligent rate limiting for Together.ai:

#### Automatic Rate Management
- **Per-Second Limiting**: Enforces max requests per second (configurable)
- **Concurrent Control**: Limits simultaneous requests to prevent overload
- **429 Response Handling**: Automatically respects `Retry-After` headers
- **Exponential Backoff**: Smart retry timing with increasing delays
- **Request Queueing**: Queues requests to stay within API limits

#### Rate Limit Configuration

Configure based on your Together.ai plan:

```bash
# Free Tier (Conservative)
TOGETHER_MAX_RPS=1
TOGETHER_MAX_CONCURRENT=2
TOGETHER_RETRY_ATTEMPTS=5

# Pro Tier (Balanced - Default)
TOGETHER_MAX_RPS=2
TOGETHER_MAX_CONCURRENT=3
TOGETHER_RETRY_ATTEMPTS=3

# Enterprise Tier (Aggressive)
TOGETHER_MAX_RPS=5
TOGETHER_MAX_CONCURRENT=6
TOGETHER_RETRY_ATTEMPTS=2
```

#### Processing Time Impact

Rate limiting affects processing times:

| Plan | Images/Video | Processing Time |
|------|--------------|----------------|
| Free Tier | 8 images | 8-12 minutes |
| Pro Tier | 8 images | 5-8 minutes |
| Enterprise | 8 images | 3-5 minutes |

#### Monitoring Rate Limits

The service logs rate limiting activity:

```
INFO - Rate limiting: 2 req/s, max 3 concurrent
DEBUG - Rate limit hit, waiting 0.5s
WARNING - Rate limited (429), waiting 2s before retry 1/3
```

### Cost Optimization
- Use environment defaults for consistent sizing
- Cache frequently used prompts
- Monitor API usage through logging

### Production Deployment
```bash
# Set production environment
export TOGETHER_API_KEY=prod_key
export TOGETHER_DEFAULT_STEPS=4  # Balance quality/speed
export REDIS_URL=redis://production-redis:6379/0

# Start with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🤝 Contributing

To extend the aiimage-to-video pipeline:

1. **Add new video effects** in `MoviePyVideoComposer`
2. **Support new image providers** in the service layer
3. **Enhance prompt generation** in `ImagePromptGenerator`
4. **Add new script types** in the script generator

See the [development guide](../README.md) for more information.