# KittenTTS Integration

KittenTTS is an ultra-lightweight, high-quality text-to-speech (TTS) service integrated into the Griot. With only 15 million parameters (~25MB total), it delivers expressive speech synthesis with CPU-only inference.

## Overview

KittenTTS provides:
- **Ultra-lightweight**: 15M parameter model, ~25MB total size
- **CPU-only inference**: No GPU required, runs on any hardware
- **8 expressive voices**: Male and female variants across 4 voice styles
- **Real-time generation**: Optimized for fast speech synthesis
- **High-quality output**: 24kHz WAV files with natural speech
- **Automatic model download**: Models downloaded from Hugging Face Hub on first use

## Features

- **Real ONNX Implementation**: Uses actual KittenML models, not mock/placeholder
- **Automatic Fallback**: Falls back to mock if dependencies unavailable
- **Voice Variety**: 8 distinct voices with different characteristics
- **Speed Control**: Adjustable speech rate (0.5x to 2.0x)
- **Integration Ready**: Works seamlessly with job queue and S3 storage

## Available Voices

KittenTTS includes 8 expressive voices:

| Voice ID | Gender | Description |
|----------|--------|-------------|
| `expr-voice-2-m` | Male | Expressive Male Voice 2 - Clear and professional |
| `expr-voice-2-f` | Female | Expressive Female Voice 2 - Warm and engaging |
| `expr-voice-3-m` | Male | Expressive Male Voice 3 - Deep and authoritative |
| `expr-voice-3-f` | Female | Expressive Female Voice 3 - Bright and energetic |
| `expr-voice-4-m` | Male | Expressive Male Voice 4 - Smooth and conversational |
| `expr-voice-4-f` | Female | Expressive Female Voice 4 - Natural and friendly |
| `expr-voice-5-m` | Male | Expressive Male Voice 5 - Rich and expressive |
| `expr-voice-5-f` | Female | Expressive Female Voice 5 - Clear and articulate |

## Installation

KittenTTS requires additional dependencies for full functionality:

```bash
# Install required dependencies
pip install onnxruntime numpy huggingface_hub soundfile

# Or install all optional dependencies
pip install -r requirements-full.txt
```

## Configuration

No additional configuration is required. KittenTTS will:
1. Auto-download models from Hugging Face Hub on first use
2. Cache models in `/tmp/kitten_cache` (configurable via `KITTEN_CACHE_DIR`)
3. Fall back to mock implementation if dependencies are missing

### Environment Variables

```bash
# Optional: Custom cache directory for models
KITTEN_CACHE_DIR=/path/to/model/cache
```

## API Usage

### Direct TTS Generation

KittenTTS is available through the standard audio TTS endpoints:

```bash
curl -X POST "http://localhost:8000/api/v1/audio/speech" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! This is KittenTTS speaking with natural, expressive voice synthesis.",
    "voice": "expr-voice-5-f",
    "provider": "kitten",
    "speed": 1.0
  }'
```

### List Available Voices

```bash
curl -X GET "http://localhost:8000/api/v1/audio/providers" \
  -H "X-API-Key: your_api_key"
```

Response includes KittenTTS voices:
```json
{
  "kitten": {
    "voices": [
      {
        "name": "expr-voice-2-m",
        "language": "en-US", 
        "description": "Expressive Male Voice 2",
        "gender": "male",
        "provider": "kitten"
      },
      {
        "name": "expr-voice-5-f",
        "language": "en-US",
        "description": "Expressive Female Voice 5", 
        "gender": "female",
        "provider": "kitten"
      }
    ]
  }
}
```

## Integration Examples

### Video Generation with KittenTTS

```bash
# Generate video with KittenTTS narration
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The wonders of space exploration",
    "voice_provider": "kitten",
    "voice_name": "expr-voice-4-m",
    "duration": 60
  }'
```

### YouTube Shorts with KittenTTS

```bash
# Create YouTube Short with KittenTTS voice
curl -X POST "http://localhost:8000/api/v1/yt-shorts/" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://youtube.com/watch?v=example",
    "voice_provider": "kitten",
    "voice_name": "expr-voice-3-f",
    "max_duration": 60
  }'
```

### Scenes-to-Video with KittenTTS

```bash
curl -X POST "http://localhost:8000/api/v1/ai/scenes-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "text": "Welcome to our amazing presentation",
        "duration": 3.0,
        "searchTerms": ["welcome", "presentation"]
      },
      {
        "text": "Let me show you something incredible", 
        "duration": 4.0,
        "searchTerms": ["incredible", "amazing"]
      }
    ],
    "voice_provider": "kitten",
    "voice_name": "expr-voice-2-f"
  }'
```

## Technical Implementation

### Model Architecture

KittenTTS uses:
- **ONNX Runtime**: Optimized inference engine
- **Hugging Face Hub**: Automatic model downloading
- **15M Parameter Model**: Efficient neural TTS architecture
- **Voice Embeddings**: 8 pre-trained speaker embeddings
- **24kHz Output**: High-quality audio generation

### Processing Pipeline

1. **Text Processing**: Basic tokenization and phonemization
2. **Model Inference**: ONNX session runs TTS model
3. **Audio Generation**: 24kHz WAV output with silence trimming
4. **File Storage**: Temporary files with unique naming

### Performance Characteristics

- **Model Size**: ~25MB total (model + voice embeddings)
- **Generation Speed**: Real-time on CPU
- **Memory Usage**: <100MB during inference
- **Initialization Time**: 2-5 seconds for first use
- **Audio Quality**: Natural, expressive speech

## Voice Comparison

### Male Voices

- **`expr-voice-2-m`**: Professional, clear delivery
- **`expr-voice-3-m`**: Deep, authoritative tone
- **`expr-voice-4-m`**: Smooth, conversational style
- **`expr-voice-5-m`**: Rich, highly expressive

### Female Voices

- **`expr-voice-2-f`**: Warm, engaging personality
- **`expr-voice-3-f`**: Bright, energetic delivery
- **`expr-voice-4-f`**: Natural, friendly tone
- **`expr-voice-5-f`**: Clear, articulate speech

## Advantages Over Other TTS Providers

### vs. Kokoro TTS
- **Smaller Model**: 15M vs 82M parameters
- **Faster Loading**: Quicker model initialization
- **Multiple Voices**: 8 voices vs 1

### vs. Edge TTS
- **Privacy**: No external API calls
- **Reliability**: No network dependencies
- **Cost**: No usage limits or costs

### vs. Pollinations TTS
- **Speed**: No API latency
- **Consistency**: Guaranteed availability
- **Control**: Full local processing

## Error Handling

### Common Issues

**Missing Dependencies:**
```bash
pip install onnxruntime numpy huggingface_hub soundfile
```

**Model Download Failures:**
- Check internet connection
- Verify Hugging Face Hub access
- Clear cache directory if corrupted

**Audio Generation Errors:**
- Text may contain unsupported characters
- Voice name might be invalid
- Speed parameter out of range (0.1-3.0)

### Fallback Behavior

If KittenTTS dependencies are missing, the service automatically falls back to a mock implementation that:
- Generates silent WAV files for testing
- Maintains API compatibility
- Logs warnings about missing functionality

## Performance Tuning

### Memory Optimization
```bash
# Set custom cache directory for better disk management
export KITTEN_CACHE_DIR="/opt/kitten_models"
```

### Speed vs Quality
- **Speed 0.5-0.8**: Slower, more deliberate speech
- **Speed 1.0**: Normal conversational pace
- **Speed 1.2-1.5**: Faster delivery for information-dense content
- **Speed 1.6-2.0**: Rapid speech for time-constrained content

## Troubleshooting

### Model Loading Issues

```bash
# Check model cache
ls -la /tmp/kitten_cache/

# Clear corrupted cache
rm -rf /tmp/kitten_cache/
```

### Audio Quality Issues

1. **Choppy audio**: Reduce speed parameter
2. **Robotic speech**: Try different voice (expr-voice-5-* recommended)
3. **Silent output**: Check text contains supported characters
4. **File size too small**: Text might be empty or invalid

### Integration Issues

1. **Service unavailable**: Check dependency installation
2. **Voice not found**: Verify voice name from available list
3. **Slow generation**: Model downloading on first use (one-time delay)

## Future Enhancements

Planned improvements include:
- **More Voice Styles**: Additional speaker embeddings
- **Language Support**: Multi-language model variants
- **Emotion Control**: Adjustable emotional expression
- **SSML Support**: Speech Synthesis Markup Language
- **Real-time Streaming**: Streaming audio generation

---

*KittenTTS is developed by KittenML and integrated into Griot for ultra-lightweight, high-quality speech synthesis.*