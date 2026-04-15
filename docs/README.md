# Media API Documentation

Welcome to the Media API documentation! This comprehensive guide covers all features including the new AI-powered video generation capabilities.

## 📚 **Documentation Index**

### 🤖 **AI Features (NEW)**
- [AI Script Generation](ai-videos/ai-script-generation.md) - Generate video scripts from topics using GPT-4o/Groq
- [AI Video Search](ai-videos/ai-video-search.md) - Find stock videos and generate search queries with AI
- [Topic-to-Video Pipeline](ai-videos/footage-to-video-pipeline.md) - Complete end-to-end video generation
- [Enhanced Caption Timing](ai-videos/enhanced-caption-timing.md) - Precise word-level timing with Whisper
- [OpenAI-Compatible LLMs](ai-videos/openai-compatible-llms.md) - Use any OpenAI-compatible LLM (Ollama, etc.)
- [**🎬 YouTube Shorts Generator**](yt-shorts/README.md) - **AI-powered YouTube Shorts creation** ⭐
- [**🎨 Pollinations.AI Integration**](pollinations/README.md) - **AI image generation, text completion, and TTS** ⭐
- [**📱 Postiz Social Media**](postiz/README.md) - **Automatic social media scheduling and publishing** ⭐
- [**🎭 ComfyUI Integration**](comfyui/README.md) - **Custom video generation workflows with ComfyUI** ⭐

### 🎵 **Audio Processing**
- [Text-to-Speech](audio/speech.md) - Multi-provider TTS with Kokoro, Edge TTS, and KittenTTS
- [**🐱 KittenTTS Integration**](kitten-tts/README.md) - **Ultra-lightweight 15M parameter TTS with 8 voices** ⭐
- [Music Generation](audio/music.md) - AI music creation with MusicGen
- [Audio Transcription](audio/transcriptions.md) - Whisper-powered audio transcription

### 📄 **Document Processing**
- [Document Conversion](documents/README.md) - Convert PDFs, Word docs, Excel, PowerPoint to Markdown
- [Examples & Use Cases](documents/examples.md) - Practical examples and integration patterns
- [Troubleshooting](documents/troubleshooting.md) - Common issues and solutions

### 🖼️ **Image Processing**
- [Image Generation](images/generate.md) - AI-powered image creation with multiple models
- [Image Enhancement](images/README.md) - Advanced image processing and editing
- [Image Overlay](images/edit.md) - Multi-layer image composition
- [Image-to-Video](videos/generations.md) - Convert images to videos with effects

### 🎬 **Video Processing**
- [Video Overlay](videos/edit.md) - Overlay videos on images
- [Video Concatenation](videos/concatenate.md) - Join multiple videos with transitions
- [Video Merge](videos/merge.md) - Merge videos with background audio in one operation
- [Video Captions](videos/add_captions.md) - Add modern TikTok-style captions
- [Video Audio](videos/add_audio.md) - Add background music and narration
- [Text Overlay](videos/text_overlay.md) - Add styled text to videos
- [LTX Video Generation](videos/ltx_generations.md) - Generate videos from text prompts or images using LTX-Video
- [**🎯 YouTube Shorts**](yt-shorts/README.md) - **Advanced AI-powered short video generation** ⭐

### 🔧 **Advanced Features**
- [FFmpeg Compose](ffmpeg/README.md) - Advanced video processing with custom FFmpeg commands
- [Media Conversions](media/conversions.md) - Convert media formats with file upload support
- [S3 Storage](s3/upload.md) - Cloud storage integration
- [Media Downloads](media/download.md) - Download and convert media
- [Code Execution](code/execute_python.md) - Run Python code for custom processing
- [**📊 Caption Styles Configuration**](caption-styles/README.md) - **Configure caption styling and parameters** ⭐

### 👥 **User & System Management**
- [Admin API](admin/README.md) - User management and system administration
- [Library Management](library/README.md) - Video library and asset management
- [Job Management](jobs/README.md) - Background job monitoring and control
- [Authentication](auth/README.md) - API key management and user authentication

### 🔌 **System Integration**
- [**🤖 MCP Server**](mcp/README.md) - **Model Context Protocol for AI agent integration** ⭐
- [**📈 API Analytics**](api-analytics/README.md) - **Comprehensive API monitoring and analytics** ⭐
- [**🌐 Web UI**](web/README.md) - **Web interface for video creation and management** ⭐

### 🤖 **AI Agent Integration**
- [MCP Server](mcp/README.md) - Model Context Protocol for AI agents
- [OpenAI Compatibility](openai-compat/README.md) - OpenAI-compatible endpoints

## 🌟 **Latest Major Features**

The Media API has been significantly expanded with powerful new integrations and capabilities:

### **🎨 Pollinations.AI Integration**
Complete AI content generation suite with:
- **Image Generation**: Text-to-image with Flux and advanced models
- **Text Generation**: OpenAI-compatible chat completions and text generation
- **Vision Analysis**: Analyze images and answer questions about visual content  
- **Text-to-Speech**: Premium voices for natural narration
- **High Rate Limits**: No cooldowns with API key authentication
- **Async Processing**: Background job queue integration with S3 storage

### **📱 Postiz Social Media Automation**
Seamlessly schedule generated content to social media:
- **Multi-Platform**: Twitter, LinkedIn, Instagram, TikTok, Facebook
- **Smart Scheduling**: Post now, schedule later, or save as drafts
- **Job Integration**: Auto-schedule from completed video/image/audio jobs
- **Media Support**: Videos, images, and audio attachments
- **Content Suggestions**: AI-generated post content based on your media

### **🐱 KittenTTS Ultra-Lightweight TTS**
Revolutionary 15M parameter TTS with real voice synthesis:
- **Ultra-Small**: Only ~25MB total model size
- **CPU-Only**: No GPU required, runs anywhere
- **8 Expressive Voices**: Male and female variants with distinct personalities
- **Real-Time**: Fast generation optimized for production use
- **High Quality**: 24kHz natural speech output
- **Auto-Download**: Models fetch from Hugging Face Hub automatically

### **🎯 Enhanced Video Provider Selection**
Improved stock video sourcing with multiple providers:
- **Pexels + Pixabay**: Dual provider integration with automatic fallback
- **Smart Matching**: AI-powered video selection based on content
- **Provider Comparison**: Choose best results from multiple sources
- **Quality Optimization**: Automatic resolution and format selection
- **Usage Tracking**: Monitor API usage across providers

## 🌟 **AI-Powered Video Creation Pipeline**

The Media API now includes powerful AI capabilities that enable complete automation of video content creation:

### **🎯 Topic-to-Video Generation**
Transform any topic into a complete video with:
- AI script generation optimized for viral content
- Automatic background video sourcing from Pexels
- High-quality text-to-speech narration
- Modern caption styling with animations
- Professional video composition and rendering

### **🤖 Intelligent Automation**
- **Dual AI Providers**: OpenAI GPT-4o and Groq Mixtral-8x7b support
- **Smart Video Matching**: AI finds visually relevant background footage
- **Precise Timing**: Word-level caption synchronization
- **Quality Optimization**: Automatic resolution and format selection

### **📈 Production Ready**
- **Async Job Processing**: Handle multiple video generations simultaneously
- **S3 Storage**: Scalable cloud storage for all generated content
- **Error Recovery**: Robust fallback mechanisms
- **API-First Design**: RESTful endpoints for easy integration

## 🔗 **Quick Links**

- **Interactive API Docs**: `http://localhost:8000/docs` (when running locally)
- **Authentication**: All endpoints require `X-API-Key` header
- **Base URL**: `http://localhost:8000` (development) or your deployed URL
- **Status Polling**: All operations are async - poll job status endpoints for results

## 💡 **Common Use Cases**

1. **🎬 YouTube Shorts Generation**: AI-powered short video creation from long-form content
2. **📱 Social Media Automation**: Create TikTok, Instagram Reels, and YouTube Shorts
3. **🎯 Content Repurposing**: Transform long videos into engaging short clips
4. **🔊 Speaker-Focused Content**: Dynamic face tracking and audio-visual correlation
5. **📈 Viral Content Creation**: AI-powered highlight detection for maximum engagement
6. **🎪 Educational Shorts**: Convert educational content into digestible short videos
7. **🎵 Podcast Highlights**: Transform audio content into visual shorts

## 🛠️ **Development**

```bash
# Start the development server
docker-compose up --build

# Or run locally
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📞 **Getting Started**

1. **Set up Environment Variables**:
   ```bash
   # Core API Configuration
   API_KEY=your_secret_api_key_here
   
   # AI Services Configuration
   OPENAI_API_KEY=your_openai_key                 # For AI script generation
   OPENAI_BASE_URL=https://api.openai.com/v1      # Optional: For OpenAI-compatible LLMs
   OPENAI_MODEL=gpt-4o                           # Optional: Custom model name
   GROQ_API_KEY=your_groq_key                    # Optional alternative to OpenAI
   GROQ_BASE_URL=http://localhost:8080/v1        # Optional: For Groq-compatible LLMs (NOT needed for official Groq)
   GROQ_MODEL=mixtral-8x7b-32768                 # Optional: Custom Groq model
   
   # NEW: Pollinations.AI Integration
   POLLINATIONS_API_KEY=your_pollinations_api_key  # For premium features and higher rate limits
   
   # NEW: Social Media Integration
   POSTIZ_API_KEY=your_postiz_api_key             # For social media scheduling
   POSTIZ_API_URL=https://api.postiz.com/public/v1 # Default: Postiz cloud API
   
   # Video Provider APIs
   PEXELS_API_KEY=your_pexels_key                # For stock video search
   PIXABAY_API_KEY=your_pixabay_key              # Optional: Additional video provider
   
   # NEW: KittenTTS Configuration
   KITTEN_CACHE_DIR=/path/to/model/cache         # Optional: Custom model cache directory
   
   # Storage Configuration
   S3_ACCESS_KEY=your_s3_access_key
   S3_SECRET_KEY=your_s3_secret_key
   S3_BUCKET_NAME=your_s3_bucket_name
   S3_REGION=your_s3_region
   S3_ENDPOINT_URL=your_s3_endpoint              # Optional for AWS S3, required for S3-compatible services
   
   # Database Configuration (PostgreSQL)
   DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/griot
   POSTGRES_DB=griot
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_secure_postgres_password
   
   # Redis Configuration (for caching)
   REDIS_URL=redis://:your_redis_password@redis:6379/0
   REDIS_PASSWORD=your_secure_redis_password
   
   # Admin Panel Authentication
   ADMIN_USERNAME=admin                          # Admin panel username
   ADMIN_PASSWORD=admin123                       # Admin panel password
   JWT_SECRET_KEY=your_jwt_secret_key           # For admin session security
   
   # Dashboard Authentication
   DEFAULT_USERNAME=admin                        # Dashboard default username
   DEFAULT_PASSWORD=admin                        # Dashboard default password
   ```

2. **Start the API**:
   ```bash
   docker-compose up --build
   ```

3. **Make your first request**:
   ```bash
   # Generate AI image with Pollinations.AI
   curl -X POST "http://localhost:8000/api/pollinations/image/generate" \
     -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A beautiful sunset over the ocean", "width": 1920, "height": 1080}'
   
   # Create video with KittenTTS narration
   curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
     -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"topic": "amazing ocean facts", "voice_provider": "kitten", "voice_name": "expr-voice-5-f"}'
   
   # Schedule content to social media
   curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
     -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"content": "Check out my latest AI creation! 🚀", "integrations": ["twitter_123"], "post_type": "now"}'
   
   # Search videos with multiple providers
   curl -X POST "http://localhost:8000/api/v1/ai/video-browse" \
     -H "X-API-Key: your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"query": "ocean waves", "provider": "pexels", "orientation": "landscape"}'
   ```

## 📋 **Common Response Formats**

### Job Creation Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Job Status Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "final_video_url": "https://s3.../video.mp4",
    "script_generated": "Amazing ocean facts you didn't know...",
    "processing_time": 180.5
  },
  "error": null
}
```

---

*Last updated: January 2025 - Version 2.0 with AI Features* 