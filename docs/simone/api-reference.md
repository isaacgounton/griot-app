# Simone API Reference

This document provides complete API reference for Simone endpoints, including request/response schemas, parameters, and examples.

## Authentication

All Simone endpoints require API key authentication via the `X-API-Key` header:

```http
X-API-Key: your-api-key-here
```

## Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/simone/video-to-blog` | POST | Create basic video-to-blog processing job |
| `/v1/simone/video-to-blog/{job_id}` | GET | Get basic processing job status |
| `/v1/simone/viral-content` | POST | Create viral content generation job |
| `/v1/simone/viral-content/{job_id}` | GET | Get viral content job status |

---

## Basic Video to Blog Processing

### Create Video-to-Blog Job

Convert a video into a blog post with optional social media content and screenshots.

**`POST /v1/simone/video-to-blog`**

#### Request Body

```json
{
  "url": "string",
  "platform": "string (optional)",
  "cookies_content": "string (optional)",
  "cookies_url": "string (optional)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Video URL to process (YouTube, TikTok, Instagram, etc.) |
| `platform` | string | No | Social media platform for post generation (`x`, `linkedin`, `instagram`) |
| `cookies_content` | string | No | Cookie content for authentication (for private videos) |
| `cookies_url` | string | No | Cookie URL for authentication |

#### Example Request

```bash
curl -X POST "http://localhost:8000/v1/simone/video-to-blog" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "platform": "linkedin"
  }'
```

#### Response

```json
{
  "job_id": "abc-123-def-456",
  "status": "pending"
}
```

### Get Video-to-Blog Job Status

Check the status and results of a video-to-blog processing job.

**`GET /v1/simone/video-to-blog/{job_id}`**

#### Example Request

```bash
curl "http://localhost:8000/v1/simone/video-to-blog/abc-123-def-456" \
  -H "X-API-Key: your-api-key"
```

#### Response (Pending)

```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "result": null,
  "error": null
}
```

#### Response (Processing)

```json
{
  "job_id": "abc-123-def-456",
  "status": "processing",
  "result": null,
  "error": null
}
```

#### Response (Completed)

```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "result": {
    "blog_post_content": "# Amazing Video Analysis\n\nThis video discusses...",
    "blog_post_url": "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/abc-123/generated_blogpost.txt",
    "screenshots": [
      "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/abc-123/screenshot_001.png",
      "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/abc-123/screenshot_002.png"
    ],
    "social_media_post_content": "🎯 Just watched an amazing video about AI...",
    "transcription_content": "Hello everyone, today we're going to talk about...",
    "transcription_url": "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/abc-123/transcription.txt"
  },
  "error": null
}
```

#### Response (Failed)

```json
{
  "job_id": "abc-123-def-456",
  "status": "failed",
  "result": null,
  "error": "Failed to download video: Video unavailable"
}
```

---

## Viral Content Generation

### Create Viral Content Job

Generate comprehensive viral content packages with advanced features.

**`POST /v1/simone/viral-content`**

#### Request Body

```json
{
  "url": "string",
  "include_topics": "boolean (default: true)",
  "include_x_thread": "boolean (default: true)",
  "platforms": ["string"] (default: ["x", "linkedin", "instagram"]),
  "thread_config": {
    "max_posts": "number (default: 8)",
    "character_limit": "number (default: 280)",
    "thread_style": "string (default: 'viral')"
  },
  "cookies_content": "string (optional)",
  "cookies_url": "string (optional)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | Video URL to process |
| `include_topics` | boolean | No | Include topic identification (default: true) |
| `include_x_thread` | boolean | No | Include X thread generation (default: true) |
| `platforms` | array[string] | No | Social media platforms (default: ["x", "linkedin", "instagram"]) |
| `thread_config` | object | No | Thread generation configuration |
| `thread_config.max_posts` | number | No | Maximum posts in thread (default: 8) |
| `thread_config.character_limit` | number | No | Character limit per post (default: 280) |
| `thread_config.thread_style` | string | No | Thread style: "viral", "professional", "casual" (default: "viral") |
| `cookies_content` | string | No | Cookie content for authentication |
| `cookies_url` | string | No | Cookie URL for authentication |

#### Example Request

```bash
curl -X POST "http://localhost:8000/v1/simone/viral-content" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "include_topics": true,
    "include_x_thread": true,
    "platforms": ["x", "linkedin", "instagram"],
    "thread_config": {
      "max_posts": 10,
      "character_limit": 280,
      "thread_style": "viral"
    }
  }'
```

#### Response

```json
{
  "job_id": "def-456-ghi-789",
  "status": "pending"
}
```

### Get Viral Content Job Status

Check the status and results of a viral content generation job.

**`GET /v1/simone/viral-content/{job_id}`**

#### Example Request

```bash
curl "http://localhost:8000/v1/simone/viral-content/def-456-ghi-789" \
  -H "X-API-Key: your-api-key"
```

#### Response (Completed)

```json
{
  "job_id": "def-456-ghi-789",
  "status": "completed",
  "result": {
    "blog_post_content": "# Revolutionary AI Technology\n\nIn this comprehensive analysis...",
    "blog_post_url": "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/def-456/generated_blogpost.txt",
    "screenshots": [
      "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/def-456/screenshot_001.png",
      "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/def-456/screenshot_002.png",
      "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/def-456/screenshot_003.png"
    ],
    "viral_content_package": {
      "content": {
        "topics": {
          "topics": [
            {
              "topic": "Artificial Intelligence",
              "relevance_score": 0.95,
              "key_points": ["Machine learning", "Neural networks", "Automation"]
            },
            {
              "topic": "Technology Innovation",
              "relevance_score": 0.87,
              "key_points": ["Breakthrough technology", "Future applications", "Industry impact"]
            }
          ]
        },
        "x_thread": {
          "thread": [
            {
              "post_number": 1,
              "content": "🧵 THREAD: Mind-blowing AI breakthrough that will change everything you know about technology! Let me break this down... 1/8",
              "character_count": 134
            },
            {
              "post_number": 2,
              "content": "🤖 This new AI system can process information 100x faster than previous models. But here's the crazy part... 2/8",
              "character_count": 118
            }
          ]
        },
        "posts": {
          "x": "🚀 Just discovered an incredible AI breakthrough! This technology is going to revolutionize how we think about machine learning. The implications are mind-blowing! #AI #Technology #Innovation",
          "linkedin": "Excited to share insights about a groundbreaking AI development that showcases the future of intelligent systems. This advancement represents a significant leap forward in machine learning capabilities and opens new possibilities for industry applications.",
          "instagram": "✨ AI Innovation Alert! ✨\n\nJust explored some amazing new technology that's pushing the boundaries of what's possible. The future is here, and it's incredible! 🤖💫\n\n#AI #Technology #Innovation #Future #TechTrends"
        }
      }
    },
    "content_package_url": "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/def-456/viral_content_package.json",
    "transcription_content": "Hello everyone, today we're diving deep into artificial intelligence...",
    "transcription_url": "https://your-s3-bucket.s3.amazonaws.com/simone_outputs/def-456/transcription.txt",
    "enhanced_features": {
      "topics_included": true,
      "x_thread_included": true,
      "platforms_processed": ["x", "linkedin", "instagram"],
      "thread_config": {
        "max_posts": 10,
        "character_limit": 280,
        "thread_style": "viral"
      }
    },
    "processing_summary": {
      "total_topics": 2,
      "thread_posts": 8,
      "platforms_generated": ["x", "linkedin", "instagram"],
      "screenshots_count": 3
    }
  },
  "error": null
}
```

---

## Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job has been created and is waiting to be processed |
| `processing` | Job is currently being processed |
| `completed` | Job has completed successfully |
| `failed` | Job has failed with an error |

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid video URL format"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid API key"
}
```

### 404 Not Found

```json
{
  "detail": "Job not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Failed to create job: Internal processing error"
}
```

---

## Rate Limits

- **Basic Processing**: 10 requests per minute per API key
- **Viral Content Generation**: 5 requests per minute per API key
- **Status Checks**: 100 requests per minute per API key

---

## Content Formats

### Blog Post Content
- **Format**: Markdown
- **Structure**: Title, introduction, main content, conclusion
- **Length**: 500-2000 words depending on source video length
- **SEO**: Optimized for search engines with proper heading structure

### Social Media Posts
- **X (Twitter)**: 280 characters or less, hashtag optimized
- **LinkedIn**: Professional tone, 1-3 paragraphs, industry focus
- **Instagram**: Visual-first, emoji usage, hashtag heavy

### X Thread Generation
- **Structure**: Numbered posts with thread indicators
- **Engagement**: Hook, value delivery, call-to-action
- **Viral Optimization**: Cliffhangers, emotional triggers, shareability

### Screenshots
- **Format**: PNG
- **Resolution**: Source video resolution maintained
- **Selection**: AI-scored based on visual content and OCR text relevance
- **Naming**: Sequential numbering (screenshot_001.png, screenshot_002.png, etc.)

---

## Best Practices

1. **Video URLs**: Ensure videos are publicly accessible or provide appropriate cookies
2. **Content Length**: Longer videos (10+ minutes) produce richer content
3. **Platform Selection**: Choose platforms that match your content distribution strategy
4. **Thread Configuration**: Adjust character limits and post counts based on platform requirements
5. **Storage**: Configure S3 for production use, local storage for development/testing

---

## Next Steps

- Review [Examples](examples.md) for practical implementation patterns
- Check [Setup Guide](setup.md) for environment configuration
- Explore [Best Practices](best-practices.md) for optimization tips