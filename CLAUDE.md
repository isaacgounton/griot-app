# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Always check the AGNO.md whenever you need help with anything related to AGNO framework.
And always use gpt-g-mini for openai model

**Run the application with Docker:**

```bash
# Quick deployment (recommended)
./scripts/deploy.sh

# Development build with hot reload and frontend mounting
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production build (optimized for deployment)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

**Start services individually:**

```bash
# Start Redis cache
docker-compose up redis -d

# Start the main API (includes internal Kokoro TTS)
docker-compose up api
```

**Local development (Python 3.12+):**

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-web.txt -r requirements-db.txt -r requirements-auth.txt -r requirements-media.txt -r requirements-ai.txt -r requirements-utils.txt -r requirements-ml.txt

# Run with live reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Development mode (single worker with reload):**
Set `DEBUG=true` in environment variables, then the app runs with `uvicorn --reload`

**Build and serve the web frontend:**

```bash
# Build the React frontend (required for web UI)
cd frontend
npm install
npm run build

# The frontend will be served at http://localhost:8000/dashboard
```

**View API documentation and interfaces:**

- Landing Page: <http://localhost:8000/> (beautiful modern landing page)
- Interactive docs: <http://localhost:48000/docs> (when running via docker-compose)
- Local development: <http://localhost:8000/docs>  
- Dashboard: <http://localhost:8000/dashboard> (after building frontend, includes admin)
- API Base: <http://localhost:8000/api> (all API endpoints)
- MCP Server: <http://localhost:8000/api/mcp/sse> (for AI agents)

**Testing:**

```bash
# Test Python 3.12 compatibility
python test_python312.py

# Test Docker build
./test_build.sh

# Test Redis connectivity
python test_redis.py

# Test S3 connectivity
python test_s3.py
```

## Architecture Overview

This is **Griot** - a FastAPI-based media processing API that handles asynchronous media generation tasks. The system uses a **job queue architecture** with the following key components:

### Core Architecture

- **FastAPI** web framework with async request handling
- **PostgreSQL Database** - primary data persistence with full web app schema (users, projects, API usage tracking)
- **Job Queue System** (`app/services/job_queue.py`) - manages async tasks with database persistence and status tracking
- **Redis Service** (`app/services/redis_service.py`) - high-performance caching and session management
- **Service Layer Pattern** - business logic in `app/services/` separated from routes
- **Docker Compose** setup with PostgreSQL, Redis, internal Kokoro TTS service and external S3-compatible storage

### Key Components

1. **Job Management**: All operations are asynchronous jobs with UUID tracking and database persistence
2. **Media Processing**: FFmpeg-based video/audio processing via `ffmpeg-python`
3. **Storage**: S3-compatible storage (AWS S3, DigitalOcean Spaces, etc.)
4. **Caching**: Redis for session management, job status, and data caching
5. **Authentication**: API key authentication via `X-API-Key` header with user management
6. **Web Application**: Full-featured dashboard with user management, project organization, and API usage analytics

### Directory Structure

```
app/
├── main.py              # FastAPI app initialization & routing
├── models.py            # Pydantic models (Job, JobStatus, JobType)
├── routes/              # API endpoints by domain
│   ├── image/           # Image processing routes
│   ├── audio/           # Audio processing routes
│   ├── media/           # Media transcription
│   └── video/           # Video processing routes
├── services/            # Business logic layer
│   ├── job_queue.py     # Async job management
│   ├── redis_service.py # Redis caching and data persistence
│   ├── s3.py            # S3 storage operations
│   └── [domain]/        # Service implementations
└── utils/               # Utility functions
    ├── auth.py          # API key authentication
    └── [domain]/        # Domain-specific utilities
```

### Key Patterns

- **Routes create jobs** → **Services process jobs** → **Results stored in S3**
- All media operations are async with job status polling
- Utilities handle complex processing logic (video generation, audio mixing)
- Each domain (image, audio, video) has parallel route/service/util structure

## Environment Configuration

Required environment variables:

```bash
# API Authentication
API_KEY=your_secret_api_key_here

# Dashboard Authentication (for /auth/login and admin features)
ADMIN_USERNAME=admin  # Default: 'admin'
ADMIN_PASSWORD=admin123  # Default: 'admin123'
JWT_SECRET_KEY=your_jwt_secret_key  # For session security
DEFAULT_USERNAME=admin  # Default: 'admin'  
DEFAULT_PASSWORD=admin  # Default: 'admin'

# S3 Storage Configuration (used by all services including Simone)
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
S3_REGION=your_s3_region
S3_ENDPOINT_URL=your_s3_endpoint  # Optional for AWS S3, required for S3-compatible services

# AI Services Configuration
OPENAI_API_KEY=your_openai_api_key  # Required for Simone AI content generation
POLLINATIONS_API_KEY=your_pollinations_api_key  # Optional: Enables higher rate limits and premium features

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/griot
POSTGRES_DB=griot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_postgres_password

# Redis Configuration (for caching)
REDIS_URL=redis://:your_redis_password@redis:6379/0
REDIS_PASSWORD=your_secure_redis_password

# Postiz Integration (for social media scheduling)
POSTIZ_API_KEY=your_postiz_api_key  # Get from your Postiz account
POSTIZ_API_URL=https://api.postiz.com/public/v1  # Default: Postiz cloud API

# ComfyUI Integration (for custom video generation workflows)
COMFYUI_URL=https://your-comfyui-instance.com/  # ComfyUI server URL
COMFYUI_USERNAME=your_username  # Optional: HTTP Basic Auth username
COMFYUI_PASSWORD=your_password  # Optional: HTTP Basic Auth password
COMFYUI_API_KEY=your_api_key    # Optional: Bearer token authentication

# API Analytics Integration (for monitoring and analytics)
API_ANALYTICS_KEY=your_api_analytics_key  # Get from apianalytics.dev - optional
```

**Storage Provider Support:**

- **AWS S3**: Standard S3 service (leave S3_ENDPOINT_URL empty)
- **DigitalOcean Spaces**: Set S3_ENDPOINT_URL to your Spaces endpoint
- **Other S3-compatible**: Any S3-compatible storage service
- **Auto-detection**: Bucket and region can be auto-extracted from DigitalOcean URLs

**Authentication Methods:**

- **Dashboard** (`/dashboard`): Uses `DEFAULT_USERNAME`/`DEFAULT_PASSWORD` to log in; admin features at `/dashboard/admin/*`
- **API Access**: Uses `API_KEY` (via `X-API-Key` header) for all API endpoints
- **Auth Routes** (`/auth/login`): Returns an API key for dashboard access

**Redis Features:**

- **Caching**: Store frequently accessed data and API responses
- **Job Queues**: Queue management for background processing
- **Session Management**: User session and temporary data storage
- **Auto-reconnection**: Graceful handling of connection failures

## Job Processing Flow

1. **POST** endpoint creates job → returns `job_id`
2. **GET** `{endpoint}/{job_id}` polls status
3. Job states: `pending` → `processing` → `completed`/`failed`
4. Results include S3 URLs for generated media

Usage Examples:

  from app.services.redis_service import redis_service

# Basic caching

  await redis_service.set("user:123", {"name": "John"}, expire=3600)
  user_data = await redis_service.get("user:123")

# Job queues

  await redis_service.enqueue_job("video_processing", {
      "job_id": "abc-123",
      "operation": "video_generation"
  })
  job = await redis_service.dequeue_job("video_processing")
  
## External Dependencies

- **Python 3.12+**: Latest Python version with improved performance and features
- **Redis**: In-memory data store for caching and queues (redis:7-alpine)
- **Kokoro TTS**: Internal ONNX-based high-quality text-to-speech service
- **KittenTTS**: Ultra-lightweight 15M parameter TTS with CPU-only inference
- **Pollinations.AI**: External AI service for image generation, text generation, and TTS
- **S3-Compatible Storage**: External cloud storage (AWS S3, DigitalOcean Spaces, etc.)
- **FFmpeg**: Video/audio processing (via ffmpeg-python)
- **Whisper**: Audio transcription (openai-whisper)
- **yt-dlp**: YouTube media download support

## Python 3.12 Features

The application now leverages Python 3.12 features including:

- **Improved Performance**: Better async/await performance and memory usage
- **Enhanced Type System**: Support for modern union types (`str | None`)
- **Better Error Messages**: More descriptive error messages and tracebacks
- **Match Statements**: Pattern matching for cleaner conditional logic
- **F-String Improvements**: Enhanced f-string functionality

## Configuration Management

### Caption Styles Configuration

Caption styling parameters are stored in `app/config/caption_styles.json`. This file contains:

- **Optimal Caption Parameters**: Pre-configured styles for different use cases (viral_bounce, standard_bottom, mobile_optimized, etc.)
- **Best Practices Guidelines**: Font size recommendations, positioning margins, readability rules
- **Viral Content Tips**: Guidelines for creating engaging captions

**Usage Example:**

```python
from app.config import get_caption_style, get_available_caption_styles

# Get a specific caption style
viral_style = get_caption_style("viral_bounce")

# List all available styles
available_styles = get_available_caption_styles()
```

### Font Management

The `/app/static/fonts/` directory contains various TTF fonts for text rendering in videos and images. These are used by the video generation and overlay utilities.

### API Analytics Integration

The application includes integration with [API Analytics](https://github.com/tom-draper/api-analytics) for comprehensive monitoring and analytics of API usage.

**Features Available:**

- **Request Tracking**: Monitor all API requests, response times, and error rates
- **Dashboard Analytics**: Beautiful analytics dashboard at apianalytics.dev
- **Performance Monitoring**: Track API performance and identify bottlenecks
- **Usage Analytics**: Understand API usage patterns and popular endpoints
- **Minimal Overhead**: Lightweight middleware with minimal performance impact

**Configuration:**

Set the `API_ANALYTICS_KEY` environment variable to enable analytics:

```bash
API_ANALYTICS_KEY=your_api_analytics_key  # Get from apianalytics.dev
```

**Endpoints:**

- `GET /analytics/info` - Get analytics configuration and status (requires API key)
- **Dashboard**: [https://apianalytics.dev/dashboard](https://apianalytics.dev/dashboard) - View analytics when API key is configured

**Usage:**

```python
from app.services.analytics import analytics_service

# Get analytics info
analytics_info = analytics_service.get_analytics_info()

# Track custom events (if supported by library)
analytics_service.track_custom_event("video_generation_completed", {
    "duration": 45.2,
    "resolution": "1080x1920"
})
```

**What Gets Tracked:**

- Request counts per endpoint
- Response times and latency
- Error rates and status codes
- User agent information
- Geographic data (anonymized)
- Usage patterns over time

## Common Development Patterns

### Job Queue Integration Pattern

When creating new endpoints that use the job queue system, always use this pattern to avoid type checking issues:

**❌ WRONG - This will cause type errors:**

```python
await job_queue.add_job(
    job_id=job_id,
    job_type=JobType.SOME_JOB,
    process_func=some_service.process_method,  # Service methods expect only (params)
    data=job_data
)
```

**✅ CORRECT - Always use wrapper functions:**

```python
# Create a wrapper function that matches job queue signature
async def process_wrapper(_job_id: str, data: dict[str, Any]) -> dict[str, Any]:
    return await some_service.process_method(data)

await job_queue.add_job(
    job_id=job_id,
    job_type=JobType.SOME_JOB,
    process_func=process_wrapper,  # Wrapper has correct (job_id, data) signature
    data=job_data
)
```

**Key Points:**

- Job queue expects: `process_func(job_id: str, data: dict[str, Any]) -> dict[str, Any]`
- Most service methods expect: `process_method(params: dict) -> dict`
- Always create wrapper functions to bridge this signature mismatch
- Use `_job_id` parameter name for unused job_id to avoid linting warnings
- Import `from typing import Any` for type annotations

**Alternative Pattern - Modify Service Method Signature:**
If the service method can be modified to match job queue expectations directly:

```python
# Change service method signature from:
async def process_clips_job(self, job_id: str, params: Dict[str, Any]) -> None:
    # ... process logic ...
    await job_queue.update_job_status(job_id, JobStatus.COMPLETED, result=result.dict())

# To:
async def process_clips_job(self, job_id: str, params: Dict[str, Any]) -> dict[str, Any]:
    # ... process logic ...
    await job_queue.update_job_status(job_id, JobStatus.COMPLETED, result=result.dict())
    return result.dict()  # Add return statement
```

This eliminates the need for wrapper functions when the service method can be modified.

### Python 3.12 Type Annotations

Use modern Python 3.12 syntax for type hints:

**✅ CORRECT:**

```python
from typing import Any  # Only import what's needed

def my_function(data: dict[str, Any]) -> list[str]:
    param: str | None = data.get("optional_param")  # Modern union syntax
    return []
```

**❌ AVOID (Old Python versions):**

```python
from typing import Dict, List, Optional, Any

def my_function(data: Dict[str, Any]) -> List[str]:
    param: Optional[str] = data.get("optional_param")
    return []
```

### JobStatus Response Pattern

When returning job status, always use the enum directly:

**✅ CORRECT:**

```python
return JobStatusResponse(
    job_id=job_id,
    status=job_info.status,  # Use enum directly
    result=job_info.result,
    error=job_info.error
)
```

**❌ WRONG:**

```python
return JobStatusResponse(
    job_id=job_id,
    status=job_info.status.value,  # Don't use .value
    result=job_info.result,
    error=job_info.error
)
```

## Pollinations.AI Integration

The Griot now includes full integration with Pollinations.AI, providing access to powerful AI-driven content generation capabilities including image generation, text generation, vision analysis, and text-to-speech.

**API Version:** The integration uses the latest Pollinations API v0.3.0 with the unified base URL `https://gen.pollinations.ai` and Bearer token authentication for improved security and reliability.

**API Endpoints Structure:**
- **Base URL**: `https://gen.pollinations.ai` (unified for all operations)
- **Image Generation**: `/image/{prompt}` (supports both text-to-image and image-to-image)
- **Text Generation**: `/text/{prompt}` (simple GET-based text generation)
- **Chat Completions**: `/v1/chat/completions` (OpenAI-compatible POST endpoint)
- **Model Discovery**: `/v1/models` (text), `/image/models`, `/text/models`

### Features Available

**Image Generation:**

- **Text-to-Image**: Generate high-quality images from text descriptions
- **Multiple Models**: Support for Flux and other advanced models
- **Customizable Parameters**: Control dimensions, seed, enhancement, safety filters
- **Image-to-Image**: Transform existing images with new prompts
- **Transparent Backgrounds**: Generate images with transparency (select models)

**Text Generation:**

- **Simple Text Generation**: Generate text from prompts using GET API
- **Advanced Chat Completions**: Full OpenAI-compatible chat API with multimodal support
- **Vision Capabilities**: Analyze images and answer questions about visual content
- **Function Calling**: Enable AI to call external tools and functions
- **Multiple Models**: Access to OpenAI, Mistral, and other text models

**Audio Generation:**

- **Text-to-Speech**: Convert text to natural-sounding speech
- **Multiple Voices**: Choose from 6+ premium voices (alloy, echo, fable, onyx, nova, shimmer)
- **Speech-to-Text**: Transcribe audio files to text
- **High-Quality Output**: MP3 format audio generation

### API Endpoints

**Image Generation:**

- `POST /api/pollinations/image/generate` - Generate images (async job)
- `GET /api/pollinations/image/generate/{job_id}` - Check generation status
- `POST /api/pollinations/vision/analyze` - Analyze images with AI vision
- `POST /api/pollinations/vision/analyze-upload` - Analyze uploaded image files
- `GET /api/pollinations/models/image` - List available image models

**Text Generation:**

- `POST /api/pollinations/text/generate` - Generate text (async job)
- `POST /api/pollinations/chat/completions` - Create chat completions (async job)
- `POST /api/pollinations/text/generate/sync` - Immediate text generation
- `POST /api/pollinations/chat/completions/sync` - Immediate chat completion
- `GET /api/pollinations/models/text` - List available text models and voices

**Audio Generation:**

- `POST /api/pollinations/audio/tts` - Text-to-speech generation (async job)
- `POST /api/pollinations/audio/transcribe` - Audio transcription (async job)
- `POST /api/pollinations/audio/tts/sync` - Immediate TTS generation
- `GET /api/pollinations/voices` - List available TTS voices

### Job Queue Integration

All Pollinations operations are integrated with the Griot job queue system:

- **Async Processing**: Long-running operations processed in background
- **Status Tracking**: Real-time job status monitoring
- **S3 Storage**: Generated content automatically saved to S3
- **Error Handling**: Comprehensive error reporting and recovery
- **Result Persistence**: All results stored with metadata

### Authentication

The service uses Bearer token authentication as per the latest API specification:

**Environment Variable:**
```bash
POLLINATIONS_API_KEY=your_secret_key  # Get from enter.pollinations.ai
```

**Authentication Method:**
- **Preferred**: Bearer token in `Authorization` header (`Authorization: Bearer YOUR_API_KEY`)
- **Fallback**: Query parameter (`?key=YOUR_API_KEY`)

**Key Types:**
- **Secret Keys (`sk_`)**: For server-side use, no rate limits, can spend Pollen
- **Publishable Keys (`pk_`)**: For client-side use, IP rate-limited (1 pollen/hour per IP+key)

**Benefits with API Key:**
- **Higher Rate Limits**: No 15-second cooldowns between requests
- **Premium Features**: Automatic logo removal on generated images
- **Priority Processing**: Faster queue processing
- **Advanced Models**: Access to state-of-the-art model tiers

### Usage Examples

**Generate Image:**

```bash
curl -X POST "http://localhost:8000/api/pollinations/image/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "width": 1920,
    "height": 1080,
    "model": "flux",
    "enhance": true
  }'
```

**Generate Text:**

```bash
curl -X POST "http://localhost:8000/api/pollinations/text/generate/sync" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a creative story about AI",
    "model": "openai",
    "temperature": 0.8
  }'
```

**Text-to-Speech:**

```bash
curl -X POST "http://localhost:8000/api/pollinations/audio/tts/sync" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of text to speech",
    "voice": "nova"
  }'
```

### Integration with Existing Features

The Pollinations integration seamlessly works with existing Griot features:

- **Video Generation**: Use Pollinations for script generation and voice synthesis
- **Image Processing**: Generate backgrounds and overlays for video content  
- **AI Workflows**: Combine with existing AI pipelines for enhanced content creation
- **Dashboard**: All endpoints accessible through the admin dashboard
- **Job Management**: Unified job tracking across all services

## Short Video Creation Features

This API now includes comprehensive short video creation capabilities with both web UI and MCP server integration, adapted from the short-video-maker project.

### Web UI Interface

Access the web frontend at `http://localhost:8000/ui` for:

- **Manual Video Creation**: Create videos with custom scenes, text, and timing
- **AI Research Mode**: Generate videos from topics with automated script generation  
- **Real-time Job Tracking**: Monitor video processing with live status updates
- **Video Library**: Manage and download all created videos
- **TTS Voice Selection**: Choose from Kokoro and Edge TTS providers

### MCP Server for AI Agents

Connect AI agents (like Claude) to create videos programmatically:

**Available MCP Tools:**

- `create-short-video` - Create videos from scenes and configuration
- `get-video-status` - Check processing status of video jobs
- `list-tts-voices` - Get available voices by provider and language
- `validate-voice-combination` - Validate voice/provider compatibility

**MCP Connection:**

- **Endpoint**: `http://localhost:8000/mcp/sse`
- **Protocol**: Server-Sent Events with JSON-RPC 2.0
- **Authentication**: X-API-Key header required

### API Integration Points

The system integrates with existing Griot services:

- **Job Queue**: Uses Redis-based async job processing
- **TTS Services**: Integrates Kokoro and Edge TTS providers
- **Topic-to-Video**: Leverages existing AI script generation pipeline
- **S3 Storage**: All videos stored in S3-compatible storage
- **Authentication**: Uses existing X-API-Key system

### Usage Examples

**Manual Video Creation (Web UI):**

1. Navigate to `/ui` and authenticate with API key
2. Use VideoCreator for scene-by-scene video building
3. Configure voice, resolution, and caption styling
4. Monitor progress in real-time

**AI Agent Integration (MCP):**

```python
# Example MCP tool call for video creation
{
  "name": "create-short-video",
  "arguments": {
    "scenes": [
      {
        "text": "Welcome to this amazing video",
        "duration": 3.0,
        "searchTerms": ["welcome", "introduction"]
      }
    ],
    "voice_provider": "kokoro",
    "voice_name": "af_bella",
    "language": "en",
    "resolution": "1080x1920"
  }
}
```

## Web Application Features

The application is designed as a full-featured web platform with comprehensive user management and analytics:

### Database Schema

- **Users**: User accounts with roles (admin, user, viewer)
- **Projects**: Organization of media generation tasks
- **API Keys**: User-specific API key management with usage limits and expiration
- **Jobs**: Enhanced job tracking with project association, priority, and resource monitoring
- **API Usage**: Detailed analytics on endpoint usage, response times, and success rates
- **Sessions**: Secure user session management with activity tracking
- **Endpoints**: Catalog of all API endpoints with usage statistics

### Dashboard Features (Implementation Ready)

- **Landing Page**: Welcome and overview of platform capabilities
- **User Management**: Registration, authentication, profile management
- **Project Dashboard**: Organize and manage media generation projects
- **Job Monitoring**: Real-time job status with progress tracking and resource usage
- **API Management**: Create, manage, and monitor API keys with usage analytics
- **Usage Analytics**: Detailed charts and metrics on API usage patterns
- **Admin Panel**: System administration and user management
- **Endpoint Explorer**: Interactive API documentation with testing capabilities

### Security Features

- **Role-based Access Control**: Admin, user, and viewer roles
- **API Key Management**: Secure key generation with rate limiting and quotas
- **Session Security**: Secure session handling with expiration
- **Usage Tracking**: Comprehensive logging of all API interactions

## KittenTTS Integration

The application includes KittenTTS as a fully integrated TTS provider with real voice synthesis capabilities.

**Features:**

- **Ultra-lightweight**: 15M parameter model (~25MB total size)
- **CPU-only inference**: No GPU required, runs on any hardware
- **8 expressive voices**: Male and female variants across 4 voice types
- **Fast generation**: Optimized for real-time speech synthesis
- **Automatic model download**: Models downloaded from Hugging Face Hub on first use

**Technical Implementation:**

- **Real ONNX model**: Direct integration with KittenML's official model
- **Hugging Face Hub**: Automatic model and voice embedding downloads
- **Text processing**: Built-in tokenization and phoneme processing
- **Audio output**: High-quality 24kHz WAV files

**Current Status:**

- ✅ **Real TTS Integration**: Actual voice synthesis with KittenML model
- ✅ **Full API Integration**: `/api/v1/audio/providers` includes `kitten`
- ✅ **Frontend Integration**: KittenTTS available in all voice selectors
- ✅ **8 Voice Options**: `expr-voice-2-m/f` through `expr-voice-5-m/f`
- ✅ **Automatic Fallback**: Falls back to mock if dependencies unavailable
- ✅ **Production Ready**: Full integration with job queue and S3 storage

**Voice Quality Examples:**

- `expr-voice-2-m/f`: Expressive male/female voice (style 2)
- `expr-voice-3-m/f`: Expressive male/female voice (style 3)  
- `expr-voice-4-m/f`: Expressive male/female voice (style 4)
- `expr-voice-5-m/f`: Expressive male/female voice (style 5)

## Development Practices

- **Always update the documentation after a major edit (news additions)**

## Documentation Practices

**CRITICAL: Documentation must stay in sync with code changes.**

### When to Update Documentation

You MUST update documentation in `/docs/` when you:
- ✅ Add new API endpoints (new routes, new parameters)
- ✅ Modify existing endpoint signatures or behavior
- ✅ Add new features or capabilities
- ✅ Change configuration (environment variables, settings)
- ✅ Deprecate or remove functionality
- ✅ Fix significant bugs that affect documented behavior

### Documentation Files to Update

| Code Change | Documentation to Update |
|-------------|------------------------|
| New API endpoint | Add to relevant section in `/docs/README.md` and create/update endpoint-specific docs |
| Modified endpoint parameters | Update existing documentation with new parameters |
| New environment variable | Update `/docs/ENVIRONMENT_VARIABLES.md` |
| New feature or integration | Create dedicated documentation in `/docs/` |
| Changed behavior | Update affected documentation files |

### Documentation Update Workflow

1. **Before** making changes: Identify which documentation files are affected
2. **While** implementing changes: Note documentation requirements
3. **After** implementing changes: **Immediately update the documentation**
4. **Verify**: Check that documentation accurately reflects the new code

### Common Documentation Locations

- **API Endpoints**: `/docs/README.md` (index) + feature-specific docs
- **Environment Variables**: `/docs/ENVIRONMENT_VARIABLES.md`
- **AI Video Features**: `/docs/ai-videos/`
- **New Features**: Create new directory in `/docs/`
- **Configuration**: Feature-specific README files

### Documentation Quality Standards

- ✅ All API parameters documented with types and defaults
- ✅ Usage examples provided for new features
- ✅ Environment variables listed with descriptions
- ✅ Breaking changes clearly noted
- ✅ Code examples match actual implementation
- ✅ Update dates included at the bottom of files

### Quick Documentation Checklist

Before considering a feature "complete":
- [ ] Are new endpoints documented?
- [ ] Are parameter changes reflected?
- [ ] Are environment variables added to ENVIRONMENT_VARIABLES.md?
- [ ] Are usage examples provided?
- [ ] Is the main README.md updated?
- [ ] Are breaking changes documented?

**Remember: Outdated documentation is worse than no documentation.**
