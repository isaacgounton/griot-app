# Postiz Integration

Postiz integration allows you to automatically schedule and publish your generated content to multiple social media platforms directly from the Griot.

## Overview

The Postiz integration enables seamless social media scheduling for:
- Generated videos (topic-to-video, YouTube Shorts, etc.)
- Created images (AI-generated, edited, etc.)
- Audio content (TTS, music, etc.)
- Custom text posts with media attachments

## Features

- **Multi-Platform Support**: Post to Twitter, LinkedIn, Instagram, Facebook, TikTok, and more
- **Flexible Scheduling**: Post now, schedule for later, or save as draft
- **Job Integration**: Automatically schedule content from completed jobs
- **Media Support**: Handle videos, images, and audio attachments
- **AI Content Generation**: Generate engaging social media posts with full context awareness
- **Tag Auto-Generation**: Automatically extract and generate relevant tags/hashtags
- **Smart Content Suggestions**: AI-generated post content based on your media

## Prerequisites

1. **Postiz Account**: Sign up at [postiz.com](https://postiz.com)
2. **API Key**: Get your Postiz API key from your account settings
3. **Social Media Integrations**: Connect your social media accounts in Postiz

## Environment Configuration

```bash
# Postiz API Configuration
POSTIZ_API_KEY=your_postiz_api_key_here
POSTIZ_API_URL=https://api.postiz.com/public/v1  # Default: Postiz cloud API
```

## API Endpoints

### Base URL
All Postiz endpoints are prefixed with `/api/v1/postiz`

### Authentication
All endpoints require the `X-API-Key` header with your Griot key.

## Quick Start

### 1. Get Available Integrations

```bash
curl -X GET "http://localhost:8000/api/v1/postiz/integrations" \
  -H "X-API-Key: your_api_key"
```

**Response:**
```json
[
  {
    "id": "twitter_123",
    "name": "@your_twitter",
    "provider": "twitter"
  },
  {
    "id": "linkedin_456",
    "name": "Your LinkedIn",
    "provider": "linkedin"
  }
]
```

### 2. Schedule a Simple Post

```bash
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Check out this amazing AI-generated content! 🚀",
    "integrations": ["twitter_123", "linkedin_456"],
    "post_type": "now"
  }'
```

### 3. Schedule a Post with Media Attachments

```bash
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Check out this amazing image! 🖼️",
    "integrations": ["twitter_123", "instagram_456"],
    "post_type": "now",
    "media_urls": ["https://example.com/image.jpg"],
    "tags": ["AI", "media"]
  }'
```

**Multiple Media Files:**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Multiple images in one post! 📸",
    "integrations": ["twitter_123"],
    "post_type": "now",
    "media_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.png"
    ]
  }'
```

### 4. Schedule Content from a Completed Job

```bash
# First, create a video
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"topic": "amazing ocean facts"}'

# Then schedule the result (media URLs auto-extracted from job)
curl -X POST "http://localhost:8000/api/v1/postiz/schedule-job" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "your_completed_job_id",
    "integrations": ["twitter_123"],
    "post_type": "now"
  }'
```

### 5. Generate AI-Powered Social Media Content

```bash
# Generate engaging content with full context from your job
curl -X POST "http://localhost:8000/api/v1/postiz/generate-content" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "your_completed_job_id",
    "user_instructions": "Make it professional and focus on the benefits",
    "content_style": "engaging",
    "platform": "linkedin",
    "max_length": 280
  }'
```

**Response:**
```json
{
  "success": true,
  "content": "🚀 Dive into the depths with our latest AI-generated video about amazing ocean facts! Discover the mysteries of the deep sea. #OceanFacts #AI #Education",
  "tags": ["OceanFacts", "AI", "Education", "DeepSea", "Marine"],
  "metadata": {
    "job_id": "your_job_id",
    "provider": "openai",
    "model": "gpt-4o",
    "content_type": "video",
    "platform": "linkedin",
    "style": "engaging"
  }
}
```

**Features:**
- ✅ Automatically extracts context (script, topic, etc.) from the job
- ✅ Generates platform-optimized content (Twitter, LinkedIn, Instagram, TikTok, etc.)
- ✅ Supports multiple content styles (engaging, professional, casual, viral, educational)
- ✅ Auto-generates and extracts relevant tags/hashtags
- ✅ Uses original script and topic for context-aware generation
- ✅ Accepts custom user instructions for fine-tuned control

## Media Attachments

### Supported Media Types

The Postiz integration supports the following media formats:

**Images:**
- Formats: `.jpg`, `.jpeg`, `.png`, `.gif`
- Max size: 10MB per image
- Supported by: Twitter/X, LinkedIn, Facebook, Instagram

**Videos:**
- Formats: `.mp4`, `.mov`, `.avi` (MP4 recommended)
- Max size: 100MB per video
- Supported by: Twitter/X, LinkedIn, Facebook
- Instagram: Limited support (check Postiz documentation)

**Audio:**
- Formats: `.mp3`, `.wav`
- Note: Audio files are typically converted to video posts by social platforms

### Media URL Requirements

**Direct Media URLs:**
- Must be publicly accessible (no authentication required)
- Should return proper Content-Type headers
- Recommended to use HTTPS URLs
- Examples: AWS S3, DigitalOcean Spaces, CDN URLs

**Media Processing:**
- The API automatically downloads media from provided URLs
- Files are uploaded to Postiz for processing
- Large files may take longer to process

### Media Attachment Examples

**Single Image:**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Beautiful sunset photo! 🌅",
    "integrations": ["instagram_456"],
    "post_type": "now",
    "media_urls": ["https://cdn.example.com/sunset.jpg"]
  }'
```

**Video with Multiple Platforms:**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Check out this amazing video! 🎬",
    "integrations": ["twitter_123", "facebook_789"],
    "post_type": "schedule",
    "schedule_date": "2024-12-25T15:00:00Z",
    "media_urls": ["https://cdn.example.com/awesome-video.mp4"]
  }'
```

**Multiple Images (Twitter Carousel):**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Photo gallery showcase! 📸✨",
    "integrations": ["twitter_123"],
    "post_type": "now",
    "media_urls": [
      "https://cdn.example.com/photo1.jpg",
      "https://cdn.example.com/photo2.jpg",
      "https://cdn.example.com/photo3.jpg"
    ]
  }'
```

## Advanced Usage

### Scheduled Posts

```bash
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Exciting content coming soon! 🎬",
    "integrations": ["twitter_123"],
    "post_type": "schedule",
    "schedule_date": "2024-12-25T12:00:00Z",
    "tags": ["AI", "content", "automation"]
  }'
```

### Draft Posts

```bash
curl -X POST "http://localhost:8000/api/v1/postiz/create-draft" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Draft content to review later",
    "integrations": ["linkedin_456"],
    "tags": ["draft", "review"]
  }'
```

### Check Job Scheduling Availability

```bash
curl -X GET "http://localhost:8000/api/v1/postiz/job/your_job_id/scheduling-info" \
  -H "X-API-Key: your_api_key"
```

## Supported Content Types

### Automatic Detection
The Postiz integration automatically detects and handles different content types:

- **Videos**: `.mp4`, `.mov`, `.avi` files from video generation jobs
- **Images**: `.jpg`, `.png`, `.gif` files from image generation jobs  
- **Audio**: `.mp3`, `.wav` files from audio generation jobs
- **Text**: Plain text posts with optional media attachments

### Job Type Support
These job types can be automatically scheduled:
- `footage_to_video` - Topic-based video generation
- `aiimage_to_video` - Image-to-video conversion
- `scenes_to_video` - Scene-based video creation
- `short_video_creation` - YouTube Shorts generation
- `image_to_video` - Image animation
- `image_generation` - AI image creation
- `audio_generation` - TTS and music generation

## Error Handling

### Common Errors

**Configuration Error:**
```json
{
  "detail": "Postiz configuration error: Missing POSTIZ_API_KEY"
}
```

**Invalid API Key:**
```json
{
  "detail": "Invalid Postiz API key. Please check your POSTIZ_API_KEY environment variable."
}
```

**Job Not Found:**
```json
{
  "detail": "Job not found"
}
```

**Job Not Completed:**
```json
{
  "detail": "Job must be completed to schedule"
}
```

## Best Practices

1. **Check Job Completion**: Always verify jobs are completed before scheduling
2. **Use Suggested Content**: Let the API generate smart post content when possible
3. **Test Integrations**: Verify your social media integrations in Postiz dashboard
4. **Handle Errors**: Implement proper error handling for network and API issues
5. **Respect Rate Limits**: Be mindful of social media platform posting limits

## API Reference

### Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/postiz/integrations` | GET | Get available social media integrations |
| `/api/v1/postiz/schedule` | POST | Schedule a post with manual content and media |
| `/api/v1/postiz/schedule-job` | POST | Schedule a post from a completed job (auto-extracts media) |
| `/api/v1/postiz/generate-content` | POST | Generate AI-powered social media content |
| `/api/v1/postiz/schedule-now` | POST | Publish immediately |
| `/api/v1/postiz/create-draft` | POST | Save as draft |
| `/api/v1/postiz/job/{job_id}/scheduling-info` | GET | Get scheduling info for a job |
| `/api/v1/postiz/history` | GET | Get post history |
| `/api/v1/postiz/upload-attachment` | POST | Upload media attachment |

### Request Parameters

**SchedulePostRequest:**
```json
{
  "content": "string (required) - Post content text",
  "integrations": ["string (required) - List of integration IDs"],
  "post_type": "string (optional) - now, schedule, or draft (default: now)",
  "schedule_date": "datetime (optional) - ISO 8601 date for scheduled posts",
  "tags": ["string (optional) - List of post tags"],
  "media_urls": ["string (optional) - List of publicly accessible media URLs"]
}
```

**ScheduleJobPostRequest:**
```json
{
  "job_id": "string (required) - ID of completed job",
  "content": "string (optional) - Custom post content (uses suggested if not provided)",
  "integrations": ["string (required) - List of integration IDs"],
  "post_type": "string (optional) - now, schedule, or draft (default: now)",
  "schedule_date": "datetime (optional) - ISO 8601 date for scheduled posts",
  "tags": ["string (optional) - List of post tags"]
}
```

**Note:** `schedule-job` endpoint automatically extracts media URLs from the job result (checks `final_video_url`, `video_url`, `image_url`, `audio_url`). No need to manually specify `media_urls`.

**GenerateContentRequest:**
```json
{
  "job_id": "string (required) - ID of completed job to generate content for",
  "user_instructions": "string (optional) - Custom instructions for AI generation",
  "content_style": "string (optional) - Style: engaging, professional, casual, viral, educational (default: engaging)",
  "platform": "string (optional) - Platform: general, twitter, instagram, linkedin, tiktok (default: general)",
  "max_length": "number (optional) - Maximum character length for generated content"
}
```

### Response Format

**Success Response (Schedule):**
```json
{
  "success": true,
  "message": "Post scheduled successfully",
  "data": {
    "success": true,
    "posts": [
      {
        "postId": "cmi0vxt7v000cq9oo27x2h36y",
        "integration": "cmfamiivn0001pa8yh4qzqhis"
      }
    ]
  }
}
```

**Success Response (AI Content Generation):**
```json
{
  "success": true,
  "content": "Generated social media post text with hashtags",
  "tags": ["tag1", "tag2", "tag3"],
  "metadata": {
    "job_id": "abc-123",
    "provider": "openai",
    "model": "gpt-4o",
    "content_type": "video",
    "platform": "general",
    "style": "engaging"
  }
}
```

**Error Response:**
```json
{
  "detail": "Error description message"
}
```

## AI Content Generation

### Overview

The AI Content Generation feature uses your completed job's context (script, topic, description, etc.) to generate engaging, platform-optimized social media posts automatically.

### How It Works

1. **Context Extraction**: Retrieves original script, topic, title, and other metadata from your job
2. **Intelligent Prompting**: Builds platform-specific prompts with style guidelines
3. **AI Generation**: Uses Unified AI service (auto-selects best provider: Griot → OpenAI → Groq)
4. **Tag Extraction**: Automatically extracts hashtags and generates relevant tags
5. **Content Optimization**: Formats content according to platform requirements

### Supported Platforms

Each platform has optimized guidelines:

- **Twitter/X**: Concise (≤280 chars), conversational, relevant hashtags
- **Instagram**: Visual and engaging, 3-5 hashtags, call-to-action
- **LinkedIn**: Professional tone, value-focused, business insights
- **TikTok**: Fun and energetic, trending hashtags, curiosity-driven
- **General**: Shareable across platforms, 2-3 relevant hashtags

### Content Styles

Choose from 5 optimized styles:

- **Engaging** (default): Hooks attention immediately, encourages interaction
- **Professional**: Polished, authoritative tone for business contexts
- **Casual**: Friendly, conversational, approachable
- **Viral**: Shareable, surprising, emotionally resonant
- **Educational**: Informative while digestible and interesting

### Tag Auto-Generation

Tags are automatically generated using two methods:

1. **Explicit Tags**: AI suggests 3-5 relevant tags based on content context
2. **Hashtag Extraction**: Automatically extracts hashtags (#AI, #Video) from generated content
3. **Deduplication**: Removes duplicates while preserving order
4. **Limit**: Maximum 10 tags returned

### Context Awareness

The AI has access to all available job context:

- **Script/Content**: Original script or generated text
- **Topic**: Main topic or subject matter
- **Title**: Content title or headline
- **Description**: Additional description text
- **Media Type**: Video, image, or audio
- **Scenes**: Scene breakdown (if available)
- **Tags**: Existing tags from job

### Usage Examples

**Basic Generation:**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/generate-content" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc-123"
  }'
```

**Platform-Specific:**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/generate-content" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc-123",
    "platform": "twitter",
    "max_length": 280
  }'
```

**With Custom Instructions:**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/generate-content" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc-123",
    "user_instructions": "Focus on benefits, add emojis, be enthusiastic",
    "content_style": "viral",
    "platform": "instagram"
  }'
```

**Professional LinkedIn Post:**
```bash
curl -X POST "http://localhost:8000/api/v1/postiz/generate-content" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc-123",
    "content_style": "professional",
    "platform": "linkedin",
    "user_instructions": "Highlight business value and ROI"
  }'
```

### Frontend Integration

The Schedule dialog includes built-in AI content generation:

1. User opens Schedule dialog for a completed job
2. Optional: Enter custom instructions in "Instructions for AI" field
3. Click "Generate AI Content" button
4. Generated content + tags automatically populate the form
5. User can edit or schedule immediately

### Best Practices

1. **Use Context**: AI works best with jobs that have rich context (scripts, topics)
2. **Provide Instructions**: Custom instructions help fine-tune the output
3. **Match Platform**: Select the target platform for optimized formatting
4. **Review Content**: Always review generated content before publishing
5. **Iterate**: Regenerate with different instructions to find the perfect tone

## Integration Examples

See [examples.md](examples.md) for detailed integration examples and workflows.

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues and solutions.

---

*For more information about Postiz features and account management, visit [postiz.com](https://postiz.com)*