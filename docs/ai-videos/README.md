# AI Video Generation Documentation

This directory contains comprehensive documentation for AI-powered video generation features in the Griot.

## 📚 Available Guides

### Core Features

- **[Quick Start Guide](quick-start.md)** - Get started with AI video generation in minutes
- **[Topic-to-Video Pipeline](footage-to-video-pipeline.md)** - Complete pipeline using stock videos
- **[Script-to-Video Pipeline](aiimage-to-video-pipeline.md)** - New pipeline with AI-generated images
- **[AI Script Generation](ai-script-generation.md)** - Intelligent script creation
- **[AI Video Search](ai-video-search.md)** - Smart video discovery

### Advanced Features

- **[Enhanced Caption Timing](enhanced-caption-timing.md)** - Precise caption synchronization
- **[OpenAI Compatible LLMs](openai-compatible-llms.md)** - Use alternative AI providers

## 🎯 Pipeline Comparison

Choose the right pipeline for your needs:

| Feature | Topic-to-Video | Script-to-Video |
|---------|----------------|-----------------|
| **Video Source** | Pexels stock videos | AI-generated images |
| **Visual Style** | Real footage | Artistic/custom imagery |
| **Processing Time** | 2-5 minutes | 3-8 minutes |
| **Uniqueness** | Stock footage (may repeat) | 100% unique visuals |
| **Cost** | Lower | Higher (image generation) |
| **Quality** | Professional stock | AI art quality |
| **Customization** | Limited by stock availability | Unlimited creative control |

## 🚀 Getting Started

### 1. Choose Your Pipeline

**For realistic content with real footage:**

```bash
POST /v1/ai/footage-to-video
```

**For unique content with AI-generated visuals:**

```bash
POST /v1/ai/aiimage-to-video
```

### 2. Basic Request

```json
{
  "topic": "amazing space facts",
  "script_type": "facts",
  "language": "en",
  "video_orientation": "portrait",
  "add_captions": true
}
```

### 3. Monitor Progress

```bash
GET /v1/ai/{pipeline-type}/{job_id}
```

## 🎬 Pipeline Features

### Topic-to-Video Pipeline

✅ **Mature & Stable**

- Uses Pexels stock video database
- Fast processing (2-5 minutes)
- High-quality professional footage
- Reliable and battle-tested

**Best for:**

- News content
- Educational videos
- Documentary-style content
- Quick content creation

### Script-to-Video Pipeline

🆕 **New & Innovative**

- Uses Together.ai FLUX for image generation
- Unique visuals for every video
- Creative control over imagery
- Advanced video effects

**Best for:**

- Artistic content
- Storytelling
- Branded content
- Creative projects

## 🛠 Configuration

### Environment Variables

```bash
# Core Services
OPENAI_API_KEY=your_openai_key
REDIS_URL=redis://redis:6379/0
S3_ACCESS_KEY=your_s3_key
S3_SECRET_KEY=your_s3_secret

# Script-to-Video (New)
TOGETHER_API_KEY=your_together_key
TOGETHER_DEFAULT_MODEL=black-forest-labs/FLUX.1-schnell
TOGETHER_DEFAULT_WIDTH=576
TOGETHER_DEFAULT_HEIGHT=1024
TOGETHER_DEFAULT_STEPS=4

# Topic-to-Video (Existing)
PEXELS_API_KEY=your_pexels_key
```

### Service Dependencies

| Service | Topic-to-Video | Script-to-Video | Purpose |
|---------|----------------|-----------------|---------|
| OpenAI | ✅ | ✅ | Script generation, image prompts |
| Pexels | ✅ | ❌ | Stock video search |
| Together.ai | ❌ | ✅ | AI image generation |
| Kokoro TTS | ✅ | ✅ | Voice synthesis |
| Redis | ✅ | ✅ | Job queuing |
| S3 | ✅ | ✅ | File storage |

## 📊 Performance Guidelines

### Processing Times

| Pipeline | 30s Video | 60s Video | 120s Video |
|----------|-----------|-----------|------------|
| Topic-to-Video | 2-3 min | 3-4 min | 4-6 min |
| Script-to-Video | 3-5 min | 5-8 min | 8-12 min |

### Resource Usage

| Pipeline | CPU | Memory | Network | Storage |
|----------|-----|--------|---------|---------|
| Topic-to-Video | Medium | Medium | High | Medium |
| Script-to-Video | High | High | High | High |

### Cost Considerations

**Topic-to-Video:**

- Pexels API calls
- TTS generation
- Video processing

**Script-to-Video:**

- AI image generation (primary cost)
- TTS generation  
- Video processing
- Additional AI model calls

## 🎯 Use Case Recommendations

### Content Type Matrix

| Content Type | Recommended Pipeline | Reasoning |
|--------------|---------------------|-----------|
| News/Current Events | Topic-to-Video | Real footage adds credibility |
| Educational/Facts | Both | Choose based on visual preference |
| Storytelling | Script-to-Video | Custom imagery enhances narrative |
| Product Marketing | Script-to-Video | Brand-specific visuals |
| Documentary | Topic-to-Video | Professional stock footage |
| Creative/Artistic | Script-to-Video | Unlimited visual creativity |
| Quick Prototypes | Topic-to-Video | Faster processing |
| Premium Content | Script-to-Video | Unique, high-value visuals |

### Target Platform Optimization

**YouTube Shorts:**

```json
{
  "video_orientation": "portrait",
  "max_duration": 60,
  "caption_style": "viral_bounce",
  "frame_rate": 30
}
```

**Instagram Reels:**

```json
{
  "video_orientation": "portrait", 
  "max_duration": 30,
  "output_width": 1080,
  "output_height": 1920
}
```

**TikTok:**

```json
{
  "video_orientation": "portrait",
  "max_duration": 60,
  "caption_style": "viral_bounce",
  "effect_type": "zoom"
}
```

**YouTube Standard:**

```json
{
  "video_orientation": "landscape",
  "max_duration": 300,
  "output_width": 1920,
  "output_height": 1080
}
```

## 🔧 Development Workflow

### Testing New Features

1. **Start with Topic-to-Video** for baseline functionality
2. **Migrate to Script-to-Video** for enhanced visuals
3. **A/B test** different pipelines for your use case
4. **Monitor performance** and cost metrics

### Integration Patterns

```python
# Factory pattern for pipeline selection
def create_video_pipeline(content_type, budget, timeline):
    if budget == "low" or timeline == "urgent":
        return FootageToVideoPipeline()
    elif content_type in ["creative", "branded", "storytelling"]:
        return AiimageToVideoPipeline()
    else:
        return FootageToVideoPipeline()  # Safe default
```

### Error Handling

```python
async def robust_video_generation(params):
    try:
        # Try aiimage-to-video first
        result = await aiimage_to_video_pipeline.process(params)
        return result
    except TogetherAIException:
        # Fallback to footage-to-video
        logger.warning("Script-to-video failed, falling back to footage-to-video")
        return await footage_to_video_pipeline.process(params)
    except Exception as e:
        logger.error(f"All pipelines failed: {e}")
        raise
```

## 📈 Scaling Considerations

### High-Volume Processing

- **Load Balance**: Distribute between pipelines based on capacity
- **Queue Management**: Prioritize urgent vs. background jobs
- **Resource Monitoring**: Track API quotas and costs
- **Caching**: Cache frequently used assets

### Multi-Tenant Architecture

```python
# Tenant-specific configuration
TENANT_CONFIGS = {
    "premium": {
        "default_pipeline": "aiimage-to-video",
        "image_steps": 8,
        "enable_background_music": True
    },
    "standard": {
        "default_pipeline": "footage-to-video", 
        "image_steps": 4,
        "enable_background_music": False
    }
}
```

## 🤝 Contributing

### Adding New Features

1. **Pipeline Extensions**: Add new video effects or AI models
2. **Provider Integration**: Support additional AI services
3. **Quality Improvements**: Enhance image/video quality
4. **Performance Optimization**: Reduce processing times

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/griot

# Install dependencies
pip install -r requirements-web.txt -r requirements-db.txt -r requirements-auth.txt -r requirements-media.txt -r requirements-ai.txt -r requirements-utils.txt -r requirements-ml.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run development server
uvicorn app.main:app --reload
```

### Testing Guidelines

```python
# Test both pipelines
async def test_video_generation():
    # Test footage-to-video
    result1 = await test_footage_to_video({
        "topic": "test topic",
        "max_duration": 30
    })
    
    # Test aiimage-to-video
    result2 = await test_aiimage_to_video({
        "topic": "test topic", 
        "max_duration": 30
    })
    
    # Compare results
    assert result1["video_duration"] > 0
    assert result2["video_duration"] > 0
    assert len(result2["generated_images"]) > 0
```

## 📞 Support & Community

### Getting Help

1. **Documentation**: Start with these guides
2. **Examples**: Check the examples in each guide
3. **GitHub Issues**: Report bugs and feature requests
4. **Discord Community**: Join discussions with other developers

### Feedback & Improvements

We're continuously improving both pipelines. Share your feedback:

- **Performance Issues**: Report slow processing times
- **Quality Concerns**: Share examples of poor output
- **Feature Requests**: Suggest new capabilities
- **Cost Optimization**: Help us reduce processing costs

### Roadmap

**Short Term:**

- Additional video effects
- More AI model options
- Performance optimizations
- Better error handling

**Long Term:**

- Real-time video generation
- Interactive video editing
- Multi-language improvements
- Advanced AI features

---

*Last updated: January 2025*
*For the latest updates, check the [changelog](../CHANGELOG.md)*
