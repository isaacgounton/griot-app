# 🚀 Griot - Advanced AI Platform for Media Generation & Intelligent Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> **Griot** is not just another media generation API—it's a comprehensive AI platform that combines advanced media processing, intelligent agents, and multi-provider AI services into a unified, production-ready system.

## 🏠 Platform Overview

Griot is a sophisticated **AI-powered platform** built for developers, content creators, and businesses who need more than basic media generation. It combines:

- 🤖 **Multi-Agent AI System** with persistent memory and knowledge integration
- 🎥 **Advanced Media Generation** (video, audio, images, text)
- 🧠 **Multi-Provider AI Services** (OpenAI, Anthropic, Google, Pollinations)
- 🔌 **MCP Server Integration** for seamless agent connectivity
- 📊 **Enterprise-Grade Analytics** and management tools
- 🌐 **Full Web Application** with user management and dashboards

## 💡 Key Features

### 🤖 Advanced AI Agent System

- **6 Pre-built Agent Types**: Research, Finance, Social Media, Sage, Scholar, and Custom agents
- **Persistent Memory**: Long-term conversation history and knowledge retention
- **Knowledge Integration**: Upload and manage knowledge bases for agents
- **Session Management**: Backup, restore, and organize agent conversations
- **Team Operations**: Collaborative workflows with multiple agents

### 🎥 Professional Media Generation

- **AI Video Pipelines**: Topic-to-video, script-to-video, scene-based creation
- **Multi-Provider TTS**: Kokoro, Edge, Piper, and KittenTTS with 8+ expressive voices
- **Image Generation**: Pollinations.AI integration with Flux models
- **Audio Processing**: Professional-grade audio synthesis and enhancement
- **Content Scoring**: AI-powered quality assessment and optimization

### 🧠 Multi-Provider AI Integration

- **AnyLLM Support**: Universal interface for OpenAI, Anthropic, Google, and more
- **Dynamic Provider Selection**: Auto-select best available AI service
- **OpenAI-Compatible API**: Drop-in replacement for existing OpenAI integrations
- **Voice & Vision**: Multi-modal AI capabilities with image analysis

### 📝 Simone AI Content System

- **Video-to-Blog**: Automatic blog post generation from video content
- **Social Media Automation**: Multi-platform content creation and scheduling
- **Intelligent Summarization**: AI-powered content analysis
- **Transcription Services**: Automatic audio/video transcription

### 🔌 Developer & Agent Integration

- **MCP Server**: 40+ tools for AI agent integration
- **FastAPI Backend**: Modern, async Python API
- **Real-time Updates**: Live job tracking and WebSocket connections
- **Comprehensive APIs**: RESTful APIs with OpenAPI documentation

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Admin Panel   │    │ Agent Dashboard │
│   (React/TSX)   │    │  (System Mgmt)  │    │   (AI Agents)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │ (Async Request      │
                    │  Handling & Logic)  │
                    └─────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │   Job Queue     │    │   Redis Cache   │    │ PostgreSQL DB   │
         │  (Async Tasks)  │    │   (Sessions)    │    │ (Persistence)   │
         └─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                    ┌─────────────────────┐
                    │  External Services  │
                    │ OpenAI │ Anthropic │
                    │ Pollinations │ S3   │
                    └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Node.js 18+ (for frontend development)

### One-Click Deployment

```bash
# Clone the repository
git clone https://github.com/isaacgounton/griot.git
cd griot

# Quick deployment (recommended)
./scripts/deploy.sh

# Access the platform
open http://localhost:8000
```

### Docker Development

```bash
# Development with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### Local Development

```bash
# Backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements-web.txt -r requirements-db.txt -r requirements-auth.txt -r requirements-media.txt -r requirements-ai.txt -r requirements-utils.txt -r requirements-ml.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install
npm run build  # Build for production
npm run dev    # Development server
```

## 🌐 Access Points

Once deployed, access the platform at:

- **🏠 Landing Page**: `http://localhost:8000/` - Beautiful modern interface
- **📊 Dashboard**: `http://localhost:8000/dashboard` - User management, analytics & admin
- **📚 API Docs**: `http://localhost:8000/docs` - Interactive API documentation
- **🤖 MCP Server**: `http://localhost:8000/mcp/sse` - AI agent integration
- **🎥 Video Creator**: `http://localhost:8000/ui` - Media creation interface

## ⚙️ Configuration

Create a `.env` file with your configuration:

```bash
# Core Authentication
API_KEY=your_secret_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_admin_password
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=admin

# AI Services (choose one or more)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_AI_API_KEY=your_google_ai_api_key
POLLINATIONS_API_KEY=your_pollinations_api_key

# Database & Storage
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/griot
REDIS_URL=redis://:password@redis:6379/0
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_BUCKET_NAME=your_bucket_name
S3_REGION=your_region

# Optional Services
POSTIZ_API_KEY=your_postiz_api_key  # Social media scheduling
COMFYUI_URL=https://your-comfyui.com  # Custom video workflows
```

## 💻 Usage Examples

### 🤖 AI Agent Integration

```python
import asyncio
from mcp import ClientSession, StdioServerParameters

async def create_ai_content():
    # Connect to Griot MCP server
    client = ClientSession("http://localhost:8000/mcp/sse")

    # Use Research Agent
    result = await client.call_tool("agent_research", {
        "topic": "AI trends 2024",
        "depth": "comprehensive"
    })

    # Generate video from research
    video_result = await client.call_tool("create-short-video", {
        "script": result.content,
        "voice_provider": "kokoro",
        "resolution": "1080x1920"
    })

    return video_result
```

### 🎥 Media Generation API

```bash
# Generate AI video from topic
curl -X POST "http://localhost:8000/api/video/topic-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The Future of Artificial Intelligence",
    "duration": 60,
    "voice_provider": "kokoro",
    "voice_name": "af_bella",
    "resolution": "1080x1920"
  }'

# Generate content with Research Agent
curl -X POST "http://localhost:8000/api/agents/research/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Machine Learning trends",
    "output_format": "detailed_report",
    "session_id": "research_session_123"
  }'
```

### 🎵 Audio Processing

```bash
# High-quality text-to-speech
curl -X POST "http://localhost:8000/api/audio/tts" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to Griot, the future of intelligent content creation",
    "voice_provider": "kokoro",
    "voice_name": "af_bella",
    "speed": 1.0,
    "format": "mp3"
  }'
```

### 🖼️ AI Image Generation

```bash
# Generate images with Pollinations.AI
curl -X POST "http://localhost:8000/api/pollinations/image/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Futuristic AI assistant helping humans create content",
    "width": 1920,
    "height": 1080,
    "model": "flux",
    "enhance": true
  }'
```

## 🎯 Use Cases

### 📝 Content Creators & Influencers

- **Automated Video Production**: Generate videos from topics with AI scripting
- **Social Media Automation**: Schedule and generate content across platforms
- **Voice Content Creation**: Professional TTS for podcasts and videos
- **Intelligent Research**: AI agents for content research and trend analysis

### 🏢 Businesses & Enterprises

- **Marketing Content**: AI-generated promotional materials and videos
- **Training Materials**: Automated creation of educational content
- **Customer Support**: AI agents for intelligent customer interactions
- **Data Analysis**: Research agents for market intelligence

### 🏫 Developers & Tech Companies

- **AI Integration**: MCP server for custom AI agent development
- **Media Processing APIs**: Comprehensive media manipulation services
- **Workflow Automation**: Integrations with existing development pipelines
- **Custom Agent Development**: Build specialized AI agents

### 🎓 Educational Institutions

- **Content Creation**: Automated educational video and material generation
- **Research Assistance**: AI agents for academic research and analysis
- **Language Learning**: TTS services for pronunciation and language tools
- **Interactive Learning**: AI-powered educational experiences

## 🔌 Integrations

### AI Service Providers

- **OpenAI**: GPT-3.5, GPT-4, GPT-5-mini
- **Anthropic**: Claude models
- **Google AI**: Gemini models
- **Pollinations.AI**: Image, text, and audio generation

### Storage & Infrastructure

- **AWS S3**: Cloud storage
- **DigitalOcean Spaces**: S3-compatible storage
- **Redis**: Caching and session management
- **PostgreSQL**: Database and analytics

### Social Media Platforms

- **Facebook**: Automated posting and content creation
- **Instagram**: Visual content generation and scheduling
- **Twitter/X**: Real-time content and engagement
- **LinkedIn**: Professional content and networking

## 🏗️ API Architecture

### Core Endpoints

```bash
# AI Agents
POST   /api/agents/{agent_type}/generate      # Generate content with agents
GET    /api/agents/sessions                   # List agent sessions
POST   /api/agents/sessions                   # Create new session
PUT    /api/agents/sessions/{session_id}      # Update session

# Media Generation
POST   /api/video/topic-to-video              # Generate video from topic
POST   /api/video/script-to-video             # Generate video from script
POST   /api/audio/tts                         # Text-to-speech
POST   /api/pollinations/image/generate       # AI image generation

# Content Processing
POST   /api/simone/video-to-blog              # Video to blog conversion
POST   /api/simone/social-content             # Social media content
GET    /api/jobs/{job_id}                     # Check job status

# MCP Server
GET    /mcp/sse                               # Server-sent events for agents
```

## 📊 Monitoring & Analytics

### Dashboard Features

- **Real-time Job Tracking**: Monitor media generation progress
- **API Usage Analytics**: Track endpoint usage and performance
- **User Management**: Multi-user support with role-based access
- **Resource Monitoring**: System health and performance metrics
- **Agent Session Management**: Track AI agent interactions

### Admin Tools

- **System Diagnostics**: Health checks and troubleshooting
- **API Key Management**: Generate and monitor API keys
- **User Administration**: Manage user accounts and permissions
- **Configuration Management**: System parameter tuning

## 🧠 Development & Testing

```bash
# Run test suite
python test_python312.py      # Python 3.12 compatibility
./test_build.sh               # Docker build testing
python test_redis.py          # Redis connectivity
python test_s3.py             # S3 storage testing

# Development mode
DEBUG=true uvicorn app.main:app --reload
```

## 🛡️ Security Features

- **Multi-Level Authentication**: API keys, JWT tokens, session-based auth
- **Role-Based Access Control**: Admin, user, viewer roles
- **Rate Limiting**: Configurable API rate limiting
- **Input Validation**: Comprehensive request validation
- **Secure Storage**: Encrypted configuration and credentials

## ⚡ Performance & Scaling

- **Async Architecture**: FastAPI with async/await for high concurrency
- **Job Queue System**: Background processing with Redis
- **Caching Layer**: Redis for performance optimization
- **Docker Support**: Containerized deployment
- **Database Optimization**: PostgreSQL with connection pooling

## 📚 Documentation

- **📚 API Documentation**: `http://localhost:8000/docs`
- **🤖 MCP Server Guide**: Check `mcp_server/README.md` for agent integration
- **⚙️ Configuration Guide**: See `CLAUDE.md` for development details
- **🔧 Troubleshooting**: Check `docs/` directory for guides

## ❤️ Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ⭐ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework for building APIs
- **Pollinations.AI** - AI-powered content generation services
- **Kokoro TTS** - High-quality text-to-speech synthesis
- **React & TypeScript** - Modern frontend development
- **Docker** - Containerization platform

---

## ❓ Why Griot?

While there are many media generation APIs, Griot is different because it's:

✅ **A Complete AI Platform** - Not just media generation, but a full AI ecosystem
✅ **Multi-Agent Intelligence** - Collaborative AI agents with memory and knowledge
✅ **Production-Ready** - Enterprise-grade features, monitoring, and security
✅ **Developer-Friendly** - Comprehensive APIs, MCP integration, and documentation
✅ **Scalable Architecture** - Built for high-performance, large-scale deployments
✅ **User-Focused** - Both powerful APIs and intuitive web interfaces

**Griot is the future of intelligent content creation - where advanced AI meets human creativity.**

---

🚀 **[Get Started Now](#quick-start)** • [📚 View Documentation](http://localhost:8000/docs) • [💬 Join Our Community](https://github.com/isaacgounton/griot/discussions)
