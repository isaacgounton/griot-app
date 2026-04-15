# Video Text Overlay

The text overlay endpoints allow you to add customizable text overlays to videos with professional styling options. This feature is perfect for titles, subtitles, watermarks, captions, and other text-based video enhancements.

## Overview

Text overlay functionality provides:
- **Professional text rendering** using FFmpeg
- **9 positioning options** for precise text placement
- **8 predefined presets** optimized for different use cases
- **Advanced styling** with fonts, colors, backgrounds, and animations
- **Intelligent text wrapping** for long content
- **S3 integration** for seamless file handling

## Create Text Overlay Job

Add custom text overlay to a video with full styling control.

### Endpoint

```
POST /v1/videos/text-overlay
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "video_url": "https://example.com/video.mp4",
  "text": "Welcome to our channel!",
  "options": {
    "duration": 5,
    "font_size": 48,
    "font_color": "white",
    "box_color": "black",
    "box_opacity": 0.8,
    "boxborderw": 60,
    "position": "bottom-center",
    "y_offset": 50,
    "line_spacing": 8,
    "auto_wrap": true
  }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video_url | string | Yes | URL of the video to add text overlay to |
| text | string | Yes | Text content to overlay (1-500 characters) |
| options | object | Yes | Styling and positioning options |

#### Options Object

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| duration | integer | 5 | Duration in seconds (1-999999) |
| font_size | integer | 48 | Font size in pixels (8-200) |
| font_color | string | "white" | Text color (named colors or hex) |
| box_color | string | "black" | Background box color |
| box_opacity | float | 0.8 | Background opacity (0.0-1.0) |
| boxborderw | integer | 60 | Background border width (0-100px) |
| position | string | "bottom-center" | Text position on video |
| y_offset | integer | 50 | Vertical offset in pixels |
| line_spacing | integer | 8 | Line spacing in pixels (0-50) |
| auto_wrap | boolean | true | Auto-wrap long text |

#### Position Options

| Position | Description |
|----------|-------------|
| top-left | Top left corner |
| top-center | Top center |
| top-right | Top right corner |
| center-left | Center left |
| center | Dead center |
| center-right | Center right |
| bottom-left | Bottom left corner |
| bottom-center | Bottom center (default) |
| bottom-right | Bottom right corner |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

### Example

#### Request

```bash
curl -X POST \
  https://localhost:8000/v1/videos/text-overlay \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "video_url": "https://example.com/sample-video.mp4",
    "text": "Subscribe for more content!",
    "options": {
      "duration": 8,
      "font_size": 56,
      "font_color": "yellow",
      "box_color": "red",
      "box_opacity": 0.9,
      "position": "center",
      "y_offset": 0
    }
  }'
```

#### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Available Presets

Retrieve all available text overlay presets with their configurations.

### Endpoint

```
GET /v1/videos/text-overlay/presets
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |

### Response

```json
{
  "title_overlay": {
    "description": "Large title text at the top, optimized for short phrases",
    "options": {
      "duration": 5,
      "font_size": 60,
      "font_color": "white",
      "box_color": "black",
      "box_opacity": 0.85,
      "boxborderw": 80,
      "position": "top-center",
      "y_offset": 80,
      "line_spacing": 18,
      "auto_wrap": true
    }
  },
  "subtitle": {
    "description": "Subtitle text at the bottom, with good readability",
    "options": {
      "duration": 10,
      "font_size": 42,
      "font_color": "white",
      "box_color": "black",
      "box_opacity": 0.8,
      "boxborderw": 60,
      "position": "bottom-center",
      "y_offset": 100,
      "line_spacing": 15,
      "auto_wrap": true
    }
  }
}
```

### Available Presets

| Preset | Description | Best For |
|--------|-------------|----------|
| **title_overlay** | Large title text at top | Video headers, main titles |
| **subtitle** | Bottom subtitle text | Standard subtitles, captions |
| **watermark** | Small, subtle text | Branding, watermarks |
| **alert** | Attention-grabbing style | Notifications, alerts |
| **modern_caption** | Clean contemporary style | Professional content |
| **social_post** | Instagram/TikTok optimized | Social media content |
| **quote** | Elegant testimonial style | Quotes, testimonials |
| **news_ticker** | Breaking news banner | News updates, announcements |

### Example

```bash
curl -X GET \
  https://localhost:8000/v1/videos/text-overlay/presets \
  -H 'X-API-Key: your-api-key'
```

## Create Text Overlay with Preset

Add text overlay using a predefined preset with optional customization.

### Endpoint

```
POST /v1/videos/text-overlay/preset/{preset_name}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| preset_name | string | Yes | Name of the preset to use |

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "video_url": "https://example.com/video.mp4",
  "text": "Breaking News: New Product Launch!",
  "options": {
    "font_color": "red",
    "duration": 10
  }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video_url | string | Yes | URL of the video to add text overlay to |
| text | string | Yes | Text content to overlay (1-500 characters) |
| options | object | No | Optional overrides for preset settings |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

### Example

#### Request

```bash
curl -X POST \
  https://localhost:8000/v1/videos/text-overlay/preset/news_ticker \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "video_url": "https://example.com/news-video.mp4",
    "text": "BREAKING: Major announcement at 3 PM EST",
    "options": {
      "font_color": "yellow",
      "duration": 15
    }
  }'
```

#### Response

```json
{
  "job_id": "j-456e7890-a12b-34c5-d678-901234567890"
}
```

## Get Job Status

Check the status of a text overlay job.

### Endpoint

```
GET /v1/videos/text-overlay/{job_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | ID of the job to get status for |

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "video_url": "https://cdn.localhost:8000/output/j-123e4567.mp4",
    "duration": 15.5,
    "preset_used": "title_overlay"
  },
  "error": null
}
```

#### Result Fields

| Field | Description |
|-------|-------------|
| video_url | URL to the video with text overlay |
| duration | Duration of the output video in seconds |
| preset_used | Name of the preset used (if applicable) |

#### Status Values

| Status | Description |
|--------|-------------|
| pending | Job is in the queue waiting to be processed |
| processing | Job is currently being processed |
| completed | Job has completed successfully |
| failed | Job has failed with an error |

### Example

```bash
curl -X GET \
  https://localhost:8000/v1/videos/text-overlay/j-123e4567-e89b-12d3-a456-426614174000 \
  -H 'X-API-Key: your-api-key'
```

## Styling Guide

### Font Colors

You can use named colors or hex codes:

**Named Colors**: `white`, `black`, `red`, `blue`, `green`, `yellow`, `orange`, `purple`, `pink`, `cyan`, `magenta`, `gray`, `navy`, `darkred`

**Hex Colors**: `#FFFFFF`, `#000000`, `#FF0000`, `#00FF00`, `#0000FF`

### Background Styling

**Box Colors**: Same options as font colors
**Opacity**: 0.0 (transparent) to 1.0 (opaque)
**Border Width**: 0-100 pixels for background padding

### Position Guidelines

| Use Case | Recommended Position | Y-Offset |
|----------|---------------------|----------|
| Video Title | top-center | 80-120 |
| Subtitles | bottom-center | 80-120 |
| Watermark | bottom-right | 40-60 |
| Alert/CTA | center | 0 |
| Social Caption | bottom-center | 120-150 |

### Text Length Guidelines

| Text Length | Recommended Settings |
|-------------|---------------------|
| Short (1-20 chars) | font_size: 56-80, auto_wrap: false |
| Medium (21-60 chars) | font_size: 42-56, auto_wrap: true |
| Long (61+ chars) | font_size: 32-42, auto_wrap: true |

## Best Practices

### 1. Text Readability
- Use high contrast colors (white text on dark background)
- Ensure adequate background opacity (0.7-0.9)
- Choose appropriate font sizes for viewing distance

### 2. Duration Guidelines
- **Titles**: 3-6 seconds
- **Subtitles**: 8-12 seconds
- **Watermarks**: Full video duration (999999)
- **Alerts**: 2-5 seconds

### 3. Positioning
- Leave margins from video edges (y_offset: 50-100)
- Test positioning on different screen sizes
- Consider safe zones for mobile viewing

### 4. Content Guidelines
- Keep text concise and impactful
- Use active voice for engagement
- Consider your target audience

### 5. Preset Selection
- **title_overlay**: Video intros, main titles
- **subtitle**: Standard captions, translations
- **watermark**: Branding, attribution
- **alert**: CTAs, urgent messages
- **social_post**: Instagram, TikTok content
- **news_ticker**: Breaking news, updates

## Technical Details

### Font Support
- **Default Fonts**: Roboto, Arial, DejaVu Sans
- **Emoji Support**: OpenSansEmoji for emoji rendering
- **Fallback**: System fonts if custom fonts unavailable

### Processing
- **Engine**: FFmpeg with hardware acceleration
- **Quality**: Professional-grade text rendering
- **Formats**: Supports all common video formats
- **Resolution**: Maintains original video quality

### File Handling
- **Input**: Supports S3 URLs and public video URLs
- **Output**: Automatically uploaded to S3
- **Cleanup**: Temporary files automatically removed
- **Security**: Secure file handling and validation

## Error Handling

### Common Errors

#### 400 Bad Request
```json
{
  "detail": "Text content cannot be empty"
}
```

#### 404 Not Found
```json
{
  "detail": "Preset 'invalid_preset' not found. Available presets: title_overlay, subtitle, watermark, alert, modern_caption, social_post, quote, news_ticker"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Text not appearing | Check duration and position settings |
| Poor readability | Increase background opacity or contrast |
| Text cut off | Adjust y_offset or reduce font_size |
| Job failed | Check video URL accessibility |

## Limitations

- **Text Length**: Maximum 500 characters per overlay
- **Duration**: Maximum 999999 seconds (essentially unlimited)
- **Font Size**: 8-200 pixels
- **Processing Time**: Varies by video length and complexity
- **File Size**: Supports videos up to 1GB

## Integration Examples

### React/JavaScript

```javascript
const createTextOverlay = async (videoUrl, text, options) => {
  const response = await fetch('/v1/videos/text-overlay', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
      video_url: videoUrl,
      text: text,
      options: options
    })
  });
  
  const data = await response.json();
  return data.job_id;
};

// Usage
const jobId = await createTextOverlay(
  'https://example.com/video.mp4',
  'Subscribe for more!',
  {
    duration: 5,
    position: 'bottom-center',
    font_color: 'yellow'
  }
);
```

### Python

```python
import requests

def create_text_overlay(video_url, text, options=None):
    url = 'https://localhost:8000/v1/videos/text-overlay'
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
    }
    data = {
        'video_url': video_url,
        'text': text,
        'options': options or {}
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Usage
result = create_text_overlay(
    'https://example.com/video.mp4',
    'Welcome to our channel!',
    {
        'duration': 8,
        'font_size': 56,
        'position': 'center'
    }
)
job_id = result['job_id']
```

### cURL

```bash
# Create with custom options
curl -X POST https://localhost:8000/v1/videos/text-overlay \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "text": "Amazing content ahead!",
    "options": {
      "duration": 6,
      "font_size": 48,
      "font_color": "white",
      "box_color": "blue",
      "position": "top-center"
    }
  }'

# Create with preset
curl -X POST https://localhost:8000/v1/videos/text-overlay/preset/social_post \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "text": "Follow us for daily tips! 🔥",
    "options": {
      "font_color": "yellow"
    }
  }'
```