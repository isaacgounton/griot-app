# Environment Variables Configuration

This document lists all environment variables used by the Griot, including the new Together.ai integration for aiimage-to-video functionality.

## 🔑 Required Variables

### Core API
```bash
API_KEY=your_secret_api_key_here
```

### Storage (S3-Compatible)
```bash
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
S3_REGION=your_s3_region
S3_ENDPOINT_URL=your_s3_endpoint  # Optional for AWS S3, required for S3-compatible services
```

### Redis Cache & Job Queue
```bash
REDIS_URL=redis://redis:6379/0
```

### Hugging Face Cache Configuration
```bash
HF_HOME=/path/to/huggingface/cache    # Directory for Hugging Face model cache (replaces deprecated TRANSFORMERS_CACHE)
```

## 🤖 AI Services

### Griot (Primary AI Provider - OpenAI Compatible)
```bash
GRIOT_API_KEY=your_griotai_api_key
GRIOT_BASE_URL=https://ai.etugrand.com    # Your Griot endpoint (without /v1 suffix)
GRIOT_MODEL=your_griotai_model             # Required model name
```

### OpenAI (Fallback Provider)
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=optional_custom_base_url  # For OpenAI-compatible LLMs
OPENAI_MODEL=gpt-4o                       # Default fallback model
```

### Together.ai (Required for aiimage-to-video pipeline)
```bash
TOGETHER_API_KEY=your_together_api_key

# Optional - Configure default image generation settings
TOGETHER_DEFAULT_MODEL=black-forest-labs/FLUX.1-schnell-Free
TOGETHER_DEFAULT_WIDTH=576
TOGETHER_DEFAULT_HEIGHT=1024
TOGETHER_DEFAULT_STEPS=4

# Optional - Rate limiting configuration (recommended for production)
TOGETHER_MAX_RPS=2              # Max requests per second (conservative default)
TOGETHER_MAX_CONCURRENT=3       # Max concurrent requests
TOGETHER_RETRY_ATTEMPTS=3       # Retry attempts on failure
TOGETHER_BASE_DELAY=1.0         # Base delay between retries in seconds
```

### Groq (Optional alternative AI provider)
```bash
GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=optional_custom_base_url
```

## 🎵 Audio & TTS Services

### Kokoro TTS
```bash
KOKORO_API_URL=http://kokoro-tts:8880/v1/audio/speech
```

## 🎬 Video Services

### Pexels (Required for footage-to-video pipeline)
```bash
PEXELS_API_KEY=your_pexels_api_key
```

## 🚀 Application Settings

### Runtime Configuration
```bash
DEBUG=true                    # Enable development mode with reload
LOG_LEVEL=INFO               # Logging level (DEBUG, INFO, WARNING, ERROR)
UVICORN_WORKERS=4            # Number of worker processes in production
```

## 📊 Feature Flags & Defaults

### Video Generation Defaults
```bash
# Default video orientation for pipelines
DEFAULT_VIDEO_ORIENTATION=portrait  # portrait, landscape, square

# Default caption settings
DEFAULT_CAPTION_STYLE=viral_bounce   # classic, viral_bounce, typewriter, fade_in

# Default TTS settings
DEFAULT_TTS_VOICE=af_alloy
DEFAULT_TTS_PROVIDER=kokoro          # kokoro, edge
```

## 🌍 Multi-Language Support
```bash
# Default language for script generation and TTS
DEFAULT_LANGUAGE=en

# Supported languages (comma-separated)
SUPPORTED_LANGUAGES=en,fr,es,de,it,pt,ru,ja,ko,zh
```

## 🔧 Service-Specific Configuration

### Together.ai Rate Limiting

Together.ai has strict rate limits that vary by plan. Configure these settings based on your plan:

#### Free Tier
```bash
TOGETHER_MAX_RPS=1              # Very conservative
TOGETHER_MAX_CONCURRENT=2       # Limited concurrent requests
TOGETHER_RETRY_ATTEMPTS=5       # More retries due to limits
```

#### Pro Tier
```bash
TOGETHER_MAX_RPS=2              # Default setting
TOGETHER_MAX_CONCURRENT=3       # Balanced concurrency
TOGETHER_RETRY_ATTEMPTS=3       # Standard retries
```

#### Enterprise Tier
```bash
TOGETHER_MAX_RPS=5              # Higher rate limit
TOGETHER_MAX_CONCURRENT=6       # More concurrent requests
TOGETHER_RETRY_ATTEMPTS=2       # Fewer retries needed
```

#### Rate Limiting Features
- **Per-second limiting**: Automatically spaces requests to stay within limits
- **429 Response Handling**: Respects `Retry-After` headers from API
- **Exponential Backoff**: Intelligent retry timing on failures
- **Concurrent Control**: Limits simultaneous requests to prevent overload

### Together.ai Models

Available models you can set as `TOGETHER_DEFAULT_MODEL`:

#### FLUX Models
- `black-forest-labs/FLUX.1-schnell-Free` (Default - Fast, 4 steps, free)
- `black-forest-labs/FLUX.1-schnell` (Fast, 4 steps, paid)
- `black-forest-labs/FLUX.1-dev` (High quality, 8-16 steps)

#### Dimension Presets
Common dimension combinations for `TOGETHER_DEFAULT_WIDTH` and `TOGETHER_DEFAULT_HEIGHT`:

| Use Case | Width | Height | Aspect Ratio |
|----------|-------|--------|--------------|
| Social Media (Portrait) | 576 | 1024 | 9:16 |
| Social Media (Square) | 768 | 768 | 1:1 |
| Social Media (Landscape) | 1024 | 576 | 16:9 |
| YouTube Thumbnail | 1280 | 720 | 16:9 |
| Instagram Post | 1080 | 1080 | 1:1 |
| Instagram Story | 1080 | 1920 | 9:16 |

### S3-Compatible Providers

#### AWS S3 (Standard)
```bash
S3_REGION=us-east-1
# S3_ENDPOINT_URL not needed for AWS
```

#### DigitalOcean Spaces
```bash
S3_REGION=nyc3
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
```

#### MinIO (Self-hosted)
```bash
S3_REGION=us-east-1
S3_ENDPOINT_URL=http://minio:9000
```

## 🤖 Hugging Face Model Caching

## 🔐 API Key Management

### Login & Key Generation
```
# By default login does NOT auto-create API keys. Set to "true" to create a key automatically
# on first login (not recommended for production).
CREATE_LOGIN_KEY_ON_LOGIN=false
```

### API Key Quota & Rate Limits
```
# Maximum number of API keys allowed per user (default 5)
MAX_API_KEYS_PER_USER=5

# Maximum number of API keys created per user per hour (default 5)
CREATE_API_KEY_RATE_LIMIT_PER_HOUR=5
```

### Notes
- Admin created keys (via startup or admin UI) can bypass the rate limits and quotas.
- All API key creation and deletion attempts are logged and audited.

### Stripe (Payments)
```
# Stripe secret API key (server side)
STRIPE_SECRET_KEY=sk_test_and_production_keys

# STRIPE_API_KEY is an alias to STRIPE_SECRET_KEY used by the backend
STRIPE_API_KEY=${STRIPE_SECRET_KEY}

# Publishable key for the frontend (must start with pk_)
STRIPE_PUBLISHABLE_KEY=pk_test_or_pk_live_keys
VITE_STRIPE_PUBLIC_KEY=${STRIPE_PUBLISHABLE_KEY}

# Stripe Price ID for the subscription plan (e.g., $30 / month). Create this on Stripe dashboard or via API.
STRIPE_PRICE_ID=price_XXXXX
```

### Cache Configuration
```bash
HF_HOME=/app/.cache/huggingface    # Directory for Hugging Face model cache
```

### Cache Optimization
- **Default Location**: `~/.cache/huggingface` (when HF_HOME is not set)
- **Docker**: Set to `/app/.cache/huggingface` for persistent storage
- **Migration**: If using `TRANSFORMERS_CACHE`, migrate to `HF_HOME` as it's deprecated
- **Permissions**: Ensure the cache directory is writable by the application user

### Environment Setup
```bash
# For local development
export HF_HOME=/path/to/your/cache

# For Docker containers
HF_HOME=/app/.cache/huggingface

# For production with persistent volumes
HF_HOME=/persistent/cache/huggingface
```

## 🐳 Docker Compose Example

```yaml
version: '3.8'

services:
  api:
    image: griot
    environment:
      # Core
      - API_KEY=your_secret_key
      
      # Storage
      - S3_ACCESS_KEY=your_s3_key
      - S3_SECRET_KEY=your_s3_secret
      - S3_BUCKET_NAME=your_bucket
      - S3_REGION=us-east-1
      
      # AI Services
      - GRIOT_API_KEY=your_griotai_key
      - GRIOT_MODEL=your_griotai_model
      - OPENAI_API_KEY=your_openai_key
      - TOGETHER_API_KEY=your_together_key
      - PEXELS_API_KEY=your_pexels_key
      
      # Together.ai Defaults
      - TOGETHER_DEFAULT_MODEL=black-forest-labs/FLUX.1-schnell-Free
      - TOGETHER_DEFAULT_WIDTH=576
      - TOGETHER_DEFAULT_HEIGHT=1024
      - TOGETHER_DEFAULT_STEPS=4
      
      # Redis
      - REDIS_URL=redis://redis:6379/0
      
      # Runtime
      - DEBUG=false
      - LOG_LEVEL=INFO
    
  redis:
    image: redis:7-alpine
    
  kokoro-tts:
    image: ghcr.io/remsky/kokoro-fastapi-cpu
    ports:
      - "8880:8880"
```

## 🔄 Environment-Specific Configurations

### Development
```bash
DEBUG=true
LOG_LEVEL=DEBUG
UVICORN_WORKERS=1
TOGETHER_DEFAULT_STEPS=4        # Fast generation for testing
```

### Staging
```bash
DEBUG=false
LOG_LEVEL=INFO
UVICORN_WORKERS=2
TOGETHER_DEFAULT_STEPS=6        # Balanced quality/speed
```

### Production
```bash
DEBUG=false
LOG_LEVEL=WARNING
UVICORN_WORKERS=4
TOGETHER_DEFAULT_STEPS=4        # Optimized for speed
```

## 🚨 Security Considerations

### API Keys
- Store all API keys securely (environment variables, secrets management)
- Rotate API keys regularly
- Use different keys for different environments
- Monitor API key usage and set up alerts

### Access Control
```bash
# Restrict API access
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

## 📝 Configuration Validation

The application automatically validates required environment variables on startup. Missing required variables will cause startup failures with clear error messages.

### Validation Example
```python
# Check required variables
required_vars = ['API_KEY', 'S3_ACCESS_KEY', 'S3_SECRET_KEY', 'S3_BUCKET_NAME']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}")
```

## 🔍 Troubleshooting

### Common Issues

#### Script-to-Video Pipeline Fails
```bash
# Check Together.ai configuration
TOGETHER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Required for image prompts
```

#### Image Generation Errors
```bash
# Verify Together.ai settings
TOGETHER_DEFAULT_MODEL=black-forest-labs/FLUX.1-schnell-Free
TOGETHER_DEFAULT_WIDTH=576    # Must be 256-2048
TOGETHER_DEFAULT_HEIGHT=1024  # Must be 256-2048
TOGETHER_DEFAULT_STEPS=4      # Must be 1-50
```

#### Storage Upload Failures
```bash
# Check S3 configuration
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=existing_bucket_name
S3_REGION=correct_region
```

### Environment Testing
```bash
# Test configuration
python -c "
import os
from app.services.ai.together_ai_service import together_ai_service
from app.services.s3 import s3_service

print('Together.ai available:', together_ai_service.is_available())
print('S3 configured:', bool(os.getenv('S3_ACCESS_KEY')))
print('Redis URL:', os.getenv('REDIS_URL'))
"
```

## 📚 Additional Resources

- [Script-to-Video Pipeline Documentation](./docs/ai-videos/aiimage-to-video-pipeline.md)
- [Image Generation Documentation](./docs/images/generate.md)
- [Topic-to-Video Pipeline Documentation](./docs/ai-videos/footage-to-video-pipeline.md)
- [Docker Deployment Guide](./docs/deployment/docker.md)

---

*Keep this document updated when adding new environment variables or changing defaults.*