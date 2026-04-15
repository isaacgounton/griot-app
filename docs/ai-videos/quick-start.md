# Quick Start Guide

Get up and running with the Media API in 5 minutes. This guide covers the essential setup and your first AI-powered video generation.

## 🚀 **1. Environment Setup**

### Docker (Recommended)

```bash
# Clone or navigate to your project directory
cd /path/to/media-api

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (see below)

# Start all services
docker-compose up --build
```

### Local Development

```bash
# Install Python 3.12+
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-web.txt -r requirements-db.txt -r requirements-auth.txt -r requirements-media.txt -r requirements-ai.txt -r requirements-utils.txt -r requirements-ml.txt

# Start the API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔑 **2. Required API Keys**

Add these to your `.env` file:

```bash
# Basic API authentication
API_KEY=your_secret_api_key_here

# AI Features (at least one required)
OPENAI_API_KEY=sk-proj-...                    # For OpenAI or compatible LLMs
OPENAI_BASE_URL=https://api.openai.com/v1     # Optional: Custom OpenAI-compatible endpoint
OPENAI_MODEL=gpt-4o                          # Optional: Custom model name
GROQ_API_KEY=gsk_...                         # Alternative to OpenAI (faster)
GROQ_MODEL=mixtral-8x7b-32768                # Optional: Custom Groq model

# Stock Videos
PEXELS_API_KEY=your_pexels_api_key           # For background videos

# Storage (required)
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
S3_REGION=us-east-1

# Optional
REDIS_URL=redis://redis:6379/0               # For job persistence
```

### Where to Get API Keys

1. **OpenAI**: [platform.openai.com](https://platform.openai.com/api-keys)
2. **Groq**: [console.groq.com](https://console.groq.com/keys) (free tier available)
3. **Pexels**: [pexels.com/api](https://www.pexels.com/api/new/) (free)
4. **AWS S3**: [aws.amazon.com/s3](https://aws.amazon.com/s3/)

## 📖 **3. Test the API**

### Check API Status

```bash
curl http://localhost:8000/
```

**Expected Response:**

```json
{
  "message": "Welcome to Media Master API",
  "authentication": "Please include your API key in the X-API-Key header for all requests"
}
```

### View Interactive Documentation

Visit: `http://localhost:8000/docs`

## 🎬 **4. Generate Your First Video**

### Create a Complete Video from Topic

```bash
curl -X POST "http://localhost:8000/v1/ai/footage-to-video" \
  -H "X-API-Key: your_secret_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "amazing ocean facts",
    "max_duration": 45,
    "video_orientation": "portrait"
  }'
```

**Response:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Processing Status

```bash
curl "http://localhost:8000/v1/ai/footage-to-video/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_secret_api_key_here"
```

**Response (when completed):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "final_video_url": "https://s3.../final_video.mp4",
    "script_generated": "Amazing ocean facts you didn't know...",
    "video_duration": 43.2,
    "processing_time": 167.3
  }
}
```

## 🎯 **5. Quick Examples**

### Generate Just a Script

```bash
curl -X POST "http://localhost:8000/v1/ai/script/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"topic": "space exploration facts"}'
```

### Text-to-Speech

```bash
curl -X POST "http://localhost:8000/v1/audio/speech" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to our amazing video!",
    "voice": "af_alloy"
  }'
```

### Search Stock Videos

```bash
curl -X POST "http://localhost:8000/v1/ai/video-search/stock-videos" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ocean waves",
    "orientation": "landscape"
  }'
```

## 📱 **6. Platform-Specific Setups**

### YouTube Shorts

```json
{
  "topic": "tech facts that will blow your mind",
  "video_orientation": "portrait",
  "output_width": 1080,
  "output_height": 1920,
  "max_duration": 50,
  "caption_style": "viral_bounce"
}
```

### TikTok Videos

```json
{
  "topic": "life hacks everyone should know",
  "video_orientation": "portrait", 
  "max_duration": 30,
  "caption_style": "viral_bounce",
  "tts_speed": 1.2
}
```

### Instagram Reels

```json
{
  "topic": "travel destinations",
  "video_orientation": "portrait",
  "max_duration": 60,
  "caption_style": "fade_in",
  "segment_duration": 4.0
}
```

## 💡 **7. Best Practices**

### Topic Selection

- **Be specific**: "deep sea creatures" > "animals"
- **Use engaging words**: "shocking", "incredible", "secret"
- **Target trending topics**: Current events, viral subjects

### Performance Tips

- **Use Groq**: Faster script generation than OpenAI
- **Portrait videos**: Better for social media
- **Shorter durations**: Process faster, better engagement

### Content Strategy

- **Hook first 3 seconds**: Use attention-grabbing topics
- **List format**: "5 facts about...", "10 secrets of..."
- **Question format**: "Did you know...?", "What if...?"

## 🔧 **8. Troubleshooting**

### Common Issues

**API Key Error:**

```
"detail": "Invalid API key"
```

*Check your X-API-Key header and .env file*

**No AI Provider:**

```
"detail": "No AI provider available"
```

*Add OPENAI_API_KEY or GROQ_API_KEY to .env*

**Video Generation Fails:**

```
"status": "failed",
"error": "No suitable videos found"
```

*Try a more general topic or different orientation*

**Slow Processing:**

- Check network connection
- Verify S3 upload speed
- Try shorter video durations

### Getting Help

1. **Check logs**: `docker-compose logs api`
2. **Test individual services**: Use `/docs` interactive testing
3. **Verify environment**: Ensure all required keys are set
4. **Check service status**: `curl http://localhost:8000/health`

## 📚 **9. Next Steps**

### Learn More

- [AI Script Generation](ai-script-generation.md) - Standalone script creation
- [AI Video Search](ai-video-search.md) - Custom video sourcing
- [Topic-to-Video Pipeline](footage-to-video-pipeline.md) - Complete automation
- [Video Processing](videos/README.md) - Advanced video editing

### Advanced Features

- **Custom Captions**: [Enhanced Caption Timing](enhanced-caption-timing.md)
- **Music Generation**: [Audio Processing](audio/README.md)
- **FFmpeg Operations**: [FFmpeg Compose](ffmpeg/README.md)
- **Batch Processing**: [API Reference](api-reference.md)

### Integration Examples

- **Python Client**: See [examples/python/](examples/python/)
- **JavaScript/React**: See [examples/javascript/](examples/javascript/)
- **Webhook Integration**: [Webhook Setup Guide](webhooks.md)

## 🎉 **10. Success!**

You should now have:
✅ API running on `localhost:8000`  
✅ Generated your first AI video  
✅ Understanding of basic endpoints  
✅ Ready for advanced features  

**Your generated video is ready to:**

- Upload to YouTube Shorts
- Post on TikTok or Instagram Reels
- Share on social media
- Edit further if needed

## 📊 **Example Workflow**

Here's a complete workflow for creating viral content:

```bash
#!/bin/bash

API_KEY="your_api_key_here"
BASE_URL="http://localhost:8000"

# 1. Generate video from topic
echo "Creating video..."
JOB_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/ai/footage-to-video" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "mindblowing psychology facts",
    "video_orientation": "portrait",
    "max_duration": 45,
    "caption_style": "viral_bounce"
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job created: $JOB_ID"

# 2. Poll for completion
while true; do
  STATUS_RESPONSE=$(curl -s "$BASE_URL/v1/ai/footage-to-video/$JOB_ID" \
    -H "X-API-Key: $API_KEY")
  
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  
  if [ "$STATUS" = "completed" ]; then
    VIDEO_URL=$(echo $STATUS_RESPONSE | jq -r '.result.final_video_url')
    echo "Video completed: $VIDEO_URL"
    break
  elif [ "$STATUS" = "failed" ]; then
    ERROR=$(echo $STATUS_RESPONSE | jq -r '.error')
    echo "Video generation failed: $ERROR"
    exit 1
  else
    echo "Status: $STATUS - waiting..."
    sleep 10
  fi
done

# 3. Download the video
curl -o "viral_video.mp4" "$VIDEO_URL"
echo "Video downloaded: viral_video.mp4"
```

Ready to create amazing content! 🚀

---

*Need help? Check the [troubleshooting guide](troubleshooting.md) or see [API examples](examples/) for more use cases.*
