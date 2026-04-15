# Simone Setup Guide

This guide walks you through setting up Simone for video-to-content conversion in your Media Master API environment.

## Prerequisites

### System Requirements

- **Python**: 3.12 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space for video processing
- **Network**: High-speed internet for video downloads

### Required Services

1. **OpenAI API Access**: For content generation
2. **S3-Compatible Storage** (optional): AWS S3, DigitalOcean Spaces, etc.
3. **Tesseract OCR**: For image text recognition
4. **FFmpeg**: For video processing
5. **Redis**: For job queue management

---

## Installation

### 1. Install Python Dependencies

The required dependencies are already included in the grouped requirements files:

```bash
# Core Simone dependencies
pip install openai-whisper>=20250625
pip install opencv-python>=4.8.0
pip install pytesseract>=0.3.10
pip install yt-dlp>=2025.6.30
pip install openai>=1.0.0
```

Or install all dependencies:

```bash
pip install -r requirements-web.txt -r requirements-db.txt -r requirements-auth.txt -r requirements-media.txt -r requirements-ai.txt -r requirements-utils.txt -r requirements-ml.txt
```

### 2. Install System Dependencies

#### Ubuntu/Debian

```bash
# Install Tesseract OCR
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng

# Install FFmpeg (if not already installed)
sudo apt install ffmpeg

# Verify installations
tesseract --version
ffmpeg -version
```

#### macOS

```bash
# Using Homebrew
brew install tesseract ffmpeg

# Verify installations
tesseract --version
ffmpeg -version
```

#### Windows

1. **Tesseract**: Download and install from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### 3. Verify Whisper Installation

```bash
# Test Whisper installation
python -c "import whisper; print('Whisper installed successfully')"

# Download base model (optional, happens automatically on first use)
python -c "import whisper; whisper.load_model('base')"
```

---

## Environment Configuration

### Required Environment Variables

Create a `.env` file or set the following environment variables:

```bash
# OpenAI API Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Optional OpenAI Configuration
OPENAI_MODEL=gpt-4                           # Default: gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1   # Default: OpenAI API

# Tesseract Configuration (Optional)
TESSERACT_PATH=/usr/bin/tesseract            # Default: /usr/bin/tesseract

# S3 Storage Configuration (Optional but Recommended)
# Simone automatically uses S3 when configured (same as other services)
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
S3_REGION=your_s3_region
S3_ENDPOINT_URL=your_s3_endpoint             # Optional for AWS S3, required for others

# Redis Configuration (Usually handled by main app)
REDIS_URL=redis://localhost:6379/0
```

### Environment Variable Details

#### OpenAI Configuration

```bash
# Required: Your OpenAI API key
OPENAI_API_KEY=sk-your-actual-api-key-here

# Optional: Custom model (if using OpenRouter or other providers)
OPENAI_MODEL=gpt-4                           # or gpt-3.5-turbo, claude-3-haiku, etc.
OPENAI_BASE_URL=https://openrouter.ai/api/v1 # for OpenRouter

# For other providers
OPENAI_BASE_URL=https://api.anthropic.com/v1 # for Claude direct
OPENAI_BASE_URL=https://api.groq.com/openai/v1 # for Groq
```

#### S3 Storage Configuration

**AWS S3:**

```bash
S3_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
S3_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET_NAME=my-simone-bucket
S3_REGION=us-east-1
# S3_ENDPOINT_URL not needed for AWS S3
```

**DigitalOcean Spaces:**

```bash
S3_ACCESS_KEY=your_spaces_key
S3_SECRET_KEY=your_spaces_secret
S3_BUCKET_NAME=my-simone-space
S3_REGION=nyc3
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
```

**Other S3-Compatible Services:**

```bash
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket
S3_REGION=your_region
S3_ENDPOINT_URL=https://your-s3-compatible-endpoint.com
```

#### Tesseract Configuration

```bash
# Default paths by OS
TESSERACT_PATH=/usr/bin/tesseract           # Linux/macOS
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows

# Find your Tesseract path
which tesseract    # Linux/macOS
where tesseract    # Windows
```

---

## Docker Setup

### Using Docker Compose (Recommended)

Add Tesseract to your existing Docker setup:

```dockerfile
# Add to your existing Dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*
```

### Docker Compose Override

Create `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  api:
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME}
      - S3_REGION=${S3_REGION}
      - S3_ENDPOINT_URL=${S3_ENDPOINT_URL}
      - TESSERACT_PATH=/usr/bin/tesseract
```

---

## Storage Setup

### S3 Bucket Configuration

#### AWS S3 Setup

1. **Create S3 Bucket:**

```bash
aws s3 mb s3://my-simone-bucket --region us-east-1
```

2. **Set Bucket Policy** (for public read access to generated content):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::my-simone-bucket/simone_outputs/*"
        }
    ]
}
```

3. **Create IAM User** with programmatic access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::my-simone-bucket/*"
        }
    ]
}
```

#### DigitalOcean Spaces Setup

1. **Create Space** in DigitalOcean control panel
2. **Generate API Keys** in API section
3. **Set CORS Policy** (if needed for web access):

```xml
<CORSConfiguration>
    <CORSRule>
        <AllowedOrigin>*</AllowedOrigin>
        <AllowedMethod>GET</AllowedMethod>
        <AllowedHeader>*</AllowedHeader>
    </CORSRule>
</CORSConfiguration>
```

### Local Storage Setup

If not using S3, ensure local storage directories exist:

```bash
# Create local output directories
mkdir -p public/simone_outputs
chmod 755 public/simone_outputs

# S3 will be used automatically if configured
```

---

## Testing Installation

### 1. Test Core Dependencies

```bash
# Test Python imports
python -c "
import whisper
import cv2
import pytesseract
import yt_dlp
print('All core dependencies imported successfully')
"
```

### 2. Test Tesseract OCR

```bash
# Test Tesseract with a simple image
python -c "
import pytesseract
from PIL import Image
import numpy as np

# Create a simple test image with text
img = Image.new('RGB', (200, 50), color='white')
from PIL import ImageDraw, ImageFont
draw = ImageDraw.Draw(img)
draw.text((10, 10), 'Hello World', fill='black')

# Test OCR
text = pytesseract.image_to_string(img)
print(f'OCR Result: {text.strip()}')
if 'Hello World' in text:
    print('✓ Tesseract working correctly')
else:
    print('✗ Tesseract not working properly')
"
```

### 3. Test Whisper

```bash
# Test Whisper model loading
python -c "
import whisper
model = whisper.load_model('base')
print('✓ Whisper model loaded successfully')
print(f'Model type: {type(model)}')
"
```

### 4. Test yt-dlp

```bash
# Test video URL extraction (without downloading)
python -c "
import yt_dlp

with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
    try:
        info = ydl.extract_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ', download=False)
        print('✓ yt-dlp working correctly')
        print(f'Video title: {info.get(\"title\", \"Unknown\")}')
    except Exception as e:
        print(f'✗ yt-dlp error: {e}')
"
```

### 5. Test S3 Connection

```bash
python -c "
from app.services.s3 import S3Service

try:
    s3_service = S3Service()
    print('✓ S3 service initialized successfully')
except Exception as e:
    print(f'✗ S3 connection error: {e}')
"
```

### 6. Full Integration Test

```bash
# Test Simone endpoints
curl -X POST "http://localhost:8000/v1/simone/video-to-blog" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }'
```

---

## Troubleshooting

### Common Issues

#### Tesseract Not Found

```bash
# Error: "TesseractNotFoundError"
# Solution: Install Tesseract and set correct path

# Find Tesseract installation
which tesseract        # Linux/macOS
where tesseract        # Windows

# Set environment variable
export TESSERACT_PATH=/usr/bin/tesseract
```

#### Whisper Model Download Issues

```bash
# Error: "Model download failed"
# Solution: Pre-download models

python -c "
import whisper
models = ['tiny', 'base', 'small']
for model_name in models:
    print(f'Downloading {model_name} model...')
    whisper.load_model(model_name)
    print(f'✓ {model_name} model ready')
"
```

#### FFmpeg Issues

```bash
# Error: "ffmpeg not found"
# Solution: Install FFmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Test FFmpeg
ffmpeg -version
```

#### S3 Permission Issues

```bash
# Error: "Access Denied"
# Solution: Check IAM permissions and bucket policy

# Test S3 access with AWS CLI
aws s3 ls s3://your-bucket-name --region your-region
```

### Performance Optimization

#### Memory Usage

```bash
# For large videos, increase memory limits
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Monitor memory usage
python -c "
import psutil
print(f'Available memory: {psutil.virtual_memory().available / 1024**3:.1f} GB')
"
```

#### Whisper Model Selection

```bash
# Choose appropriate model size based on requirements
# tiny: fastest, lowest quality
# base: good balance (default)
# small: better quality, slower
# medium: high quality, much slower
# large: best quality, very slow

export WHISPER_MODEL=base  # Adjust as needed
```

---

## Security Considerations

### API Key Management

```bash
# Never commit API keys to code
# Use environment variables or secret management

# Good practices:
echo "OPENAI_API_KEY=sk-..." >> .env
echo ".env" >> .gitignore

# For production, use secret managers:
# - AWS Secrets Manager
# - Azure Key Vault
# - Google Secret Manager
# - HashiCorp Vault
```

### S3 Security

```bash
# Use least privilege principle
# Only grant necessary S3 permissions
# Enable S3 bucket encryption
# Use VPC endpoints for internal access
```

### Network Security

```bash
# For production deployments:
# - Use HTTPS only
# - Implement rate limiting
# - Use API gateways
# - Monitor for abuse
```

---

## Next Steps

Once setup is complete:

1. **Review [API Reference](api-reference.md)** for endpoint details
2. **Try [Examples](examples.md)** to test functionality
3. **Read [Best Practices](best-practices.md)** for optimization
4. **Check [Troubleshooting](troubleshooting.md)** for common issues

## Production Checklist

- [ ] All dependencies installed and tested
- [ ] Environment variables configured
- [ ] S3 storage configured and tested
- [ ] Tesseract OCR working
- [ ] Whisper models downloaded
- [ ] API key authentication working
- [ ] Redis connection established
- [ ] Storage permissions verified
- [ ] Network security configured
- [ ] Monitoring and logging setup
