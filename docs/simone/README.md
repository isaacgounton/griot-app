# Simone - AI-Powered Video to Content Conversion

Simone is a comprehensive AI-powered service that transforms videos into blog posts, social media content, and visual assets. It provides intelligent video analysis, transcription, content generation, and frame extraction capabilities.

## Overview

Simone takes any video URL (YouTube, social media platforms, direct video links) and automatically:

1. **Downloads** video and audio content
2. **Transcribes** audio using OpenAI Whisper
3. **Generates** AI-powered blog posts from transcripts
4. **Creates** platform-specific social media content
5. **Extracts** and scores key video frames
6. **Produces** screenshots and visual assets
7. **Delivers** content packages ready for publishing

## Key Features

### 🎬 Video Processing
- **Multi-platform support**: YouTube, TikTok, Instagram, Twitter, and direct video URLs
- **Intelligent downloading**: Automatic quality selection and format optimization
- **Audio extraction**: High-quality audio separation for transcription

### 🎤 AI Transcription
- **OpenAI Whisper**: State-of-the-art speech recognition
- **Multiple formats**: Text transcripts and SRT subtitle files
- **Language support**: Automatic language detection and multi-language support

### ✍️ Content Generation
- **Blog posts**: AI-generated articles based on video content
- **Social media posts**: Platform-specific content for X (Twitter), LinkedIn, Instagram
- **Viral threads**: X thread generation with configurable styling
- **Topic identification**: Automatic extraction of key themes and subjects

### 🖼️ Visual Processing
- **Frame extraction**: Intelligent video frame sampling
- **OCR analysis**: Text recognition and relevance scoring
- **Screenshot generation**: Automatic selection of best representative frames
- **Visual asset creation**: Ready-to-use images for content publishing

### ☁️ Storage & Delivery
- **S3 integration**: Automatic upload to cloud storage
- **Local fallback**: Reliable local storage option
- **URL generation**: Direct access links for all generated content
- **Organized output**: Structured file organization by processing job

## Use Cases

### Content Creators
- Transform video content into blog posts and social media campaigns
- Generate multiple content formats from single video source
- Create engaging visual assets and screenshots

### Digital Marketers
- Repurpose video content across multiple platforms
- Generate viral social media threads and posts
- Extract key messaging and topics for campaign development

### Educational Content
- Convert lectures and tutorials into written materials
- Create accessible text alternatives for video content
- Generate study materials and summaries

### Business Communications
- Transform presentations and meetings into documented content
- Create social media announcements from video updates
- Generate executive summaries from video content

## API Endpoints

Simone provides two main processing modes:

### Basic Video to Blog Processing
**`POST /v1/simone/video-to-blog`**
- Core video-to-blog conversion
- Optional social media post generation
- Screenshot extraction and saving

### Enhanced Viral Content Processing
**`POST /v1/simone/enhanced-processing`**
- Advanced content generation with viral optimization
- Multi-platform social media content packages
- Topic identification and thread generation
- Configurable content parameters

## Content Output Types

### Text Content
- **Blog Posts**: Full-length articles with SEO optimization
- **Transcripts**: Complete video transcriptions with timestamps
- **Social Media Posts**: Platform-optimized content for multiple channels
- **Thread Content**: Viral-style X (Twitter) threads with engagement optimization

### Visual Content
- **Screenshots**: Key frame captures with intelligent selection
- **Frame Analysis**: OCR-analyzed images with relevance scoring
- **Visual Assets**: Ready-to-publish image content

### Structured Data
- **Content Packages**: JSON-formatted content collections
- **Topic Analysis**: Extracted themes and subject categorization
- **Metadata**: Processing statistics and content metrics

## Getting Started

1. **Review the [Setup Guide](setup.md)** for environment configuration
2. **Check the [API Reference](api-reference.md)** for detailed endpoint documentation
3. **Explore [Examples](examples.md)** for common use cases
4. **Read [Best Practices](best-practices.md)** for optimal results

## Documentation Structure

- **[Setup Guide](setup.md)** - Environment configuration and dependencies
- **[API Reference](api-reference.md)** - Complete endpoint documentation
- **[Examples](examples.md)** - Code samples and use cases
- **[Best Practices](best-practices.md)** - Tips for optimal content generation
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Quick Example

```bash
# Create a video-to-blog processing job
curl -X POST "http://localhost:8000/v1/simone/video-to-blog" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=example",
    "platform": "linkedin"
  }'

# Response
{
  "job_id": "abc-123-def",
  "status": "pending"
}

# Check job status
curl "http://localhost:8000/v1/simone/video-to-blog/abc-123-def" \
  -H "X-API-Key: your-api-key"
```

## Next Steps

- Set up your environment following the [Setup Guide](setup.md)
- Try the [Examples](examples.md) to see Simone in action
- Review the [API Reference](api-reference.md) for complete documentation
- Explore advanced features in [Best Practices](best-practices.md)