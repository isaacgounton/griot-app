# Video Captions

Add professional captions to videos with auto-transcription, multiple caption styles, and advanced customization. This endpoint provides AI-powered captioning with TikTok-style viral effects and comprehensive styling options.

## Features Overview

### 🎯 Core Features

- **Auto-Transcription**: AI-powered speech recognition with word-level timestamps using OpenAI Whisper
- **5 Caption Styles**: Classic, Karaoke, Highlight, Underline, Word-by-Word
- **Multi-Format Support**: Auto-transcription, SRT files, or plain text
- **Advanced Styling**: 20+ customization options for fonts, colors, positioning
- **Text Processing**: Remove filler words, replace text, exclude time ranges
- **High Quality**: Original video quality preserved with embedded ASS subtitles

### 🎨 Caption Styles

| Style | Description | Best For | Word Timestamps |
|-------|-------------|----------|-----------------|
| **Classic** | Traditional subtitles, all text at once | Movies, documentaries | Optional |
| **Karaoke** 🔥 | TikTok-style word-by-word highlighting | Social media, viral content | Required |
| **Highlight** | Full text visible, current word changes color | Educational, tutorials | Required |
| **Underline** | Full text visible, current word underlined | Professional, corporate | Required |
| **Word-by-Word** | One word at a time for dramatic effect | Motivational, quotes | Required |

### 📝 Caption Sources

1. **Auto-Transcription** (Recommended for karaoke/highlight)
   - Whisper AI with word-level timestamps
   - 99+ languages supported
   - Automatic language detection

2. **SRT Files** (Pre-timed subtitles)
   - Upload SRT content or URL
   - Word timestamps estimated
   - Full timing control

3. **Plain Text** (Auto-timed)
   - Simple text input
   - Automatic sentence splitting
   - Evenly distributed timing

### ⚙️ Key Settings

- **Positioning**: 9 preset positions or custom x,y coordinates
- **Typography**: Font family, size (default 52px), bold, italic, underline
- **Colors**: Line color, word color, outline color (hex format)
- **Layout**: Max words per line, margin controls, spacing
- **Effects**: Outline width, shadow offset, rotation angle

### 🚀 Performance

- **Processing**: 10-30 seconds per minute of video (auto-transcription)
- **Quality**: Original video quality preserved
- **Formats**: MP4, MOV, AVI, MKV, WEBM supported
- **Storage**: Auto-upload to S3-compatible storage
- **Async**: Background job processing for large videos

## Quick Start

### Simple Auto-Transcription

```bash
curl -X POST https://api.example.com/api/v1/videos/caption \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "language": "en"
  }'
```

### TikTok-Style Karaoke (Recommended Settings)

```bash
curl -X POST https://api.example.com/api/v1/videos/caption \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "settings": {
      "style": "karaoke",
      "line_color": "#FFFFFF",
      "word_color": "#FFFF00",
      "font_size": 56,
      "all_caps": true,
      "max_words_per_line": 3,
      "outline_width": 6,
      "margin_v": 100
    },
    "language": "en"
  }'
```

### With Text Cleanup

```bash
curl -X POST https://api.example.com/api/v1/videos/caption \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "replace": [
      {"find": "um", "replace": ""},
      {"find": "uh", "replace": ""},
      {"find": "like", "replace": ""}
    ],
    "settings": {
      "style": "karaoke",
      "font_size": 52,
      "max_words_per_line": 3
    }
  }'
```

## Create Caption Job

Generate captions for a video with auto-transcription and advanced styling options.

### Endpoint

```
POST /api/v1/videos/caption
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
  "settings": {
    "style": "karaoke",
    "line_color": "#FFFFFF",
    "word_color": "#FFFF00",
    "font_size": 32,
    "all_caps": true,
    "position": "bottom_center"
  },
  "language": "en"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video_url | string | Yes | URL of the video to add captions to |
| captions | string | No | Caption content, URL to caption file, or omit for auto-transcription |
| settings | object | No | Advanced styling settings (see Settings section below) |
| replace | array | No | Text replacement rules (e.g., [{"find": "um", "replace": ""}]) |
| exclude_time_ranges | array | No | Time ranges to exclude (e.g., [{"start": "00:00:00.000", "end": "00:00:05.000"}]) |
| language | string | No | Language code (default: "auto"). Options: 'en', 'fr', 'es', etc. |
| sync | boolean | No | Process synchronously (default: false) |

#### Settings Object

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| style | string | "classic" | Caption style: classic, karaoke, highlight, underline, word_by_word |
| line_color | string | "#FFFFFF" | Text color (hex format) |
| word_color | string | "#FFFF00" | Highlighted word color (used in karaoke/highlight styles) |
| outline_color | string | "#000000" | Outline color |
| all_caps | boolean | false | Convert all text to uppercase |
| max_words_per_line | integer | 10 | Maximum words per caption line (applies to karaoke and classic styles) |
| position | string | "bottom_center" | Position preset: bottom_left, bottom_center, bottom_right, middle_left, middle_center, middle_right, top_left, top_center, top_right |
| alignment | integer | 2 | ASS alignment code (1-9). Position parameter takes precedence |
| font_family | string | "Arial" | Font family name |
| font_size | integer | 52 | Font size in pixels (increased default for better visibility) |
| bold | boolean | false | Bold text |
| italic | boolean | false | Italic text |
| underline | boolean | false | Underline text |
| strikeout | boolean | false | Strikeout text |
| outline_width | integer | 2 | Outline width in pixels |
| spacing | integer | 0 | Character spacing |
| angle | integer | 0 | Text rotation angle |
| shadow_offset | integer | 0 | Shadow offset |
| x | integer | - | X position coordinate (custom positioning) |
| y | integer | - | Y position coordinate (custom positioning) |
| margin_v | integer | 80 | Vertical margin in pixels (increased default to prevent captions from being hidden at bottom) |

### Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Example

#### Request

```bash
curl -X POST \
  https://localhost:8000/api/v1/videos/caption \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "settings": {
      "style": "karaoke",
      "line_color": "#FFFFFF",
      "word_color": "#FFFF00",
      "font_size": 32,
      "all_caps": true,
      "position": "bottom_center"
    },
    "language": "en"
  }'
```

#### Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Get Job Status

Check the status of a caption job.

### Endpoint

```
GET /api/v1/videos/caption/{job_id}
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
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "url": "https://s3.amazonaws.com/bucket/captioned_video.mp4",
    "path": "videos/captioned_abc123.mp4",
    "width": 1920,
    "height": 1080,
    "file_size": 5242880,
    "style": "karaoke"
  },
  "error": null
}
```

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
  https://localhost:8000/api/v1/videos/caption/550e8400-e29b-41d4-a716-446655440000 \
  -H 'X-API-Key: your-api-key'
```

## Get Caption Styles

Get list of available caption styles with descriptions.

### Endpoint

```
GET /api/v1/videos/caption/styles/list
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |

### Response

```json
{
  "styles": [
    {
      "id": "classic",
      "name": "Classic",
      "description": "Traditional movie-style subtitles where all text appears at once",
      "best_for": "Movies, documentaries, traditional content"
    },
    {
      "id": "karaoke",
      "name": "Karaoke",
      "description": "TikTok-style word-by-word highlighting with smooth color transitions",
      "best_for": "Social media, music videos, engaging short-form content"
    },
    {
      "id": "highlight",
      "name": "Highlight",
      "description": "Full text visible, current word changes to a different color",
      "best_for": "Educational content, presentations, tutorials"
    },
    {
      "id": "underline",
      "name": "Underline",
      "description": "Full text visible, current word gets underlined",
      "best_for": "Professional content, corporate videos, news"
    },
    {
      "id": "word_by_word",
      "name": "Word-by-Word",
      "description": "Only one word visible at a time for maximum focus and dramatic effect",
      "best_for": "Motivational quotes, impactful messages, dramatic content"
    }
  ]
}
```

## Caption Style Examples

### Classic Style

Traditional movie-style subtitles where all text appears at once.
**Best for**: Movies, documentaries, traditional content

**Features**:

- All text appears simultaneously for entire segment
- Supports `max_words_per_line` for multi-line captions
- Text wrapping with `\N` for line breaks

**Example**:

```json
{
  "settings": {
    "style": "classic",
    "font_size": 40,
    "max_words_per_line": 10,
    "all_caps": false
  }
}
```

### Karaoke Style 🔥

TikTok-style word-by-word highlighting with smooth color transitions using ASS karaoke tags (`\k`). **This is the viral effect!**
**Best for**: Social media, music videos, engaging short-form content

**Features**:

- Each word highlights sequentially with precise timing
- Smooth color transition from `line_color` to `word_color`
- Supports `max_words_per_line` - splits into multiple caption lines
- Uses word-level timestamps for accurate synchronization
- Perfect for engagement and retention

**Example**:

```json
{
  "settings": {
    "style": "karaoke",
    "line_color": "#FFFFFF",
    "word_color": "#FFFF00",
    "font_size": 52,
    "max_words_per_line": 3,
    "outline_width": 4,
    "all_caps": true
  }
}
```

### Highlight Style

Full text visible, current word changes to a different color.
**Best for**: Educational content, presentations, tutorials

**Features**:

- All words visible at once
- Current word changes to `word_color`
- Individual dialogue line for each word
- Good for following along with speaker

**Example**:

```json
{
  "settings": {
    "style": "highlight",
    "line_color": "#FFFFFF",
    "word_color": "#00FFFF",
    "font_size": 44
  }
}
```

### Underline Style

Full text visible, current word gets underlined.
**Best for**: Professional content, corporate videos, news

**Features**:

- Full text always visible
- Current word underlined with ASS `\u1` tag
- Professional appearance
- Non-distracting emphasis

**Example**:

```json
{
  "settings": {
    "style": "underline",
    "font_size": 38,
    "outline_width": 2
  }
}
```

### Word-by-Word Style

Only one word visible at a time for maximum focus and dramatic effect.
**Best for**: Motivational quotes, impactful messages, dramatic content

**Features**:

- Extreme focus - one word at a time
- Maximum dramatic impact
- Each word has individual timing
- Great for short, powerful messages

**Example**:

```json
{
  "settings": {
    "style": "word_by_word",
    "font_size": 60,
    "all_caps": true,
    "position": "middle_center",
    "bold": true
  }
}
```

## Advanced Examples

### Caption Source Options

The API supports three ways to provide caption content:

#### 1. Auto-Transcription (No captions parameter)

Automatically transcribe video using Whisper AI with word-level timestamps:

```json
{
  "video_url": "https://example.com/video.mp4",
  "settings": {"style": "karaoke", "font_size": 52},
  "language": "en"
}
```

**Pros**: Word-level timestamps for perfect karaoke/highlight effects
**Cons**: Processing time, requires good audio quality

#### 2. SRT File or URL

Provide pre-timed subtitles in SRT format:

```json
{
  "video_url": "https://example.com/video.mp4",
  "captions": "1\n00:00:00,000 --> 00:00:02,000\nHello world\n\n2\n00:00:02,000 --> 00:00:04,000\nThis is a test",
  "settings": {"style": "classic"}
}
```

or URL:

```json
{
  "video_url": "https://example.com/video.mp4",
  "captions": "https://example.com/subtitles.srt",
  "settings": {"style": "classic"}
}
```

**Pros**: Full control over timing, no processing delay
**Cons**: Word-level timestamps estimated, less accurate for karaoke

#### 3. Plain Text

Provide plain text - timing is automatically distributed:

```json
{
  "video_url": "https://example.com/video.mp4",
  "captions": "This is my caption text. It will be split into sentences and timed automatically.",
  "settings": {"style": "classic"}
}
```

**Pros**: Simple and quick
**Cons**: Timing may not match video content, no word-level sync

### Auto-Transcribe Video

```json
{
  "video_url": "https://example.com/video.mp4",
  "settings": {"style": "classic", "font_size": 40},
  "language": "en"
}
```

### TikTok-Style Karaoke 🔥

```json
{
  "video_url": "https://example.com/video.mp4",
  "settings": {
    "style": "karaoke",
    "line_color": "#FFFFFF",
    "word_color": "#FFFF00",
    "font_size": 48,
    "all_caps": true,
    "outline_width": 4,
    "max_words_per_line": 3
  }
}
```

### Optimized Positioning (Visible Captions)

```json
{
  "video_url": "https://example.com/video.mp4",
  "settings": {
    "style": "karaoke",
    "position": "bottom_center",
    "margin_v": 100,
    "font_size": 52,
    "max_words_per_line": 3
  }
}
```

### Remove Filler Words

```json
{
  "video_url": "https://example.com/interview.mp4",
  "replace": [
    {"find": "um", "replace": ""},
    {"find": "like", "replace": ""},
    {"find": "you know", "replace": ""}
  ]
}
```

### Skip Intro/Outro

```json
{
  "video_url": "https://example.com/video.mp4",
  "exclude_time_ranges": [
    {"start": "00:00:00.000", "end": "00:00:05.000"},
    {"start": "00:05:30.000", "end": "00:05:40.000"}
  ]
}
```

### Educational Highlight Style

```json
{
  "video_url": "https://example.com/tutorial.mp4",
  "captions": "https://example.com/subtitles.srt",
  "settings": {
    "style": "highlight",
    "line_color": "#FFFFFF",
    "word_color": "#00FFFF",
    "font_size": 40,
    "max_words_per_line": 8
  }
}
```

### Word-by-Word Motivational

```json
{
  "video_url": "https://example.com/motivational.mp4",
  "captions": "Believe in yourself. You can achieve anything.",
  "settings": {
    "style": "word_by_word",
    "font_size": 60,
    "all_caps": true,
    "position": "middle_center"
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "video_url is required"
}
```

### 401 Unauthorized

```json
{
  "detail": "Missing API Key. Please provide a valid API key in the X-API-Key header."
}
```

### 404 Not Found

```json
{
  "detail": "Job with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Caption processing dependencies not available. Please install: faster-whisper, srt, ffmpeg"
}
```

## Technical Details

### AI Model Information

- **Transcription Model**: OpenAI Whisper (via faster-whisper)
- **Model Size**: Base (configurable)
- **Type**: Automatic speech recognition with word-level timestamps
- **Training**: Trained on 680,000 hours of multilingual audio data
- **Capabilities**: 99+ languages with automatic language detection
- **Device**: CPU optimized with int8 quantization
- **Performance**: ~10-30 seconds per minute of audio

### Subtitle Format

- **Internal Format**: ASS (Advanced SubStation Alpha)
- **Features**: Karaoke tags (`\k`), color tags (`\c`), positioning
- **Alignment**: NumPad-style codes (1-9)
- **Colors**: ASS BGR format (&H00BBGGRR), auto-converted from hex
- **Effects**: Outline, shadow, rotation, spacing
- **Line Breaks**: `\N` for multi-line captions

### Video Specifications

- **Supported Formats**: MP4, MOV, AVI, MKV, WEBM
- **Maximum Size**: 2GB
- **Maximum Duration**: 2 hours (auto-transcription), unlimited (with provided captions)
- **Output Format**: MP4 with embedded ASS subtitles
- **Quality**: Original video quality preserved
- **Codec**: Original codecs maintained (no re-encoding when possible)

### Processing Pipeline

1. **Video Download**: Fetch video from URL
2. **Transcription** (if needed):
   - Extract audio
   - Run Whisper model
   - Generate word-level timestamps
3. **Caption Processing**:
   - Parse/process caption text
   - Apply text replacements
   - Filter excluded time ranges
   - Generate ASS subtitle file
4. **Video Rendering**:
   - Embed subtitles using FFmpeg
   - Maintain original quality
5. **Upload**: Store to S3-compatible storage
6. **Cleanup**: Remove temporary files

### Performance Considerations

- **Model Loading**: First request may take 10-20 seconds for model initialization
- **Caching**: Whisper model cached in memory for faster subsequent processing
- **Concurrency**: Jobs processed asynchronously in a queue system
- **Resource Usage**: CPU-based processing, ~2GB RAM per job
- **Scalability**: Horizontal scaling supported via job queue

### Caption Generation Details

**Classic Style**:

- Single dialogue line per segment
- `\N` for line breaks when max_words exceeded
- Timing: segment start → segment end

**Karaoke Style**:

- Multiple dialogue lines (one per max_words chunk)
- `\k{duration}` tag per word (centiseconds)
- Timing: word-precise, line start → line end
- Color transition: PrimaryColour → SecondaryColour

**Highlight Style**:

- One dialogue line per word
- Full text with `\c{color}` tags
- Current word in SecondaryColour
- Timing: per-word precision

**Underline Style**:

- One dialogue line per word
- Full text with `\u1` for current word
- Timing: per-word precision

**Word-by-Word Style**:

- One dialogue line per word
- Single word visible
- Timing: per-word precision

### Dependencies

The caption feature requires the following Python packages:

- `faster-whisper>=0.10.0` - Optimized Whisper transcription
- `srt>=3.5.0` - SRT subtitle parsing and manipulation
- `ffmpeg-python>=0.2.0` - FFmpeg video processing bindings
- System `ffmpeg` and `ffprobe` binaries

If these dependencies are not installed, the endpoint will return an error message with installation instructions.

### Position Alignment Mapping

ASS uses NumPad-style alignment codes (1-9):

```
7 (top_left)     8 (top_center)     9 (top_right)
4 (middle_left)  5 (middle_center)  6 (middle_right)
1 (bottom_left)  2 (bottom_center)  3 (bottom_right)
```

Default: 2 (bottom_center)

## Best Practices

### Caption Positioning & Visibility

1. **Use adequate margin**: Default `margin_v: 80` prevents captions from being hidden at bottom
2. **Increase for safety**: Use `margin_v: 100-120` for guaranteed visibility
3. **Font size matters**: Minimum 40px for mobile, 52px+ recommended for social media
4. **High contrast**: White text (#FFFFFF) with black outline for maximum readability
5. **Position presets**: Use `position: "bottom_center"` instead of manual x,y coordinates

**Recommended Settings for Visibility**:

```json
{
  "font_size": 52,
  "margin_v": 100,
  "position": "bottom_center",
  "outline_width": 4,
  "outline_color": "#000000"
}
```

### max_words_per_line Usage

The `max_words_per_line` parameter controls caption line breaking:

**Classic Style**: Splits long segments into multi-line captions with `\N` breaks
**Karaoke Style**: Creates multiple sequential caption lines, each with max N words

**Examples**:

```json
// 3 words per line - great for TikTok/Reels
{"max_words_per_line": 3, "style": "karaoke"}

// 8 words per line - good for educational content
{"max_words_per_line": 8, "style": "highlight"}

// No limit (default: 10)
{"style": "classic"}
```

**Tips**:

- Social media: 2-4 words for maximum engagement
- Educational: 6-8 words for readability
- Professional: 8-12 words for natural flow

### Social Media Content

- Use `karaoke` style for viral effect
- Set `all_caps: true` for mobile visibility  
- Use large fonts (48-60px)
- High contrast colors (white text, black outline)
- Short lines: `max_words_per_line: 2-3`
- Position at bottom with good margin

**Perfect TikTok/Reels Settings**:

```json
{
  "style": "karaoke",
  "line_color": "#FFFFFF",
  "word_color": "#FFFF00",
  "font_size": 56,
  "all_caps": true,
  "max_words_per_line": 3,
  "outline_width": 6,
  "margin_v": 100,
  "position": "bottom_center"
}
```

### Educational Content

- Use `highlight` or `classic` style for emphasis
- Set `max_words_per_line: 6-8` for readability
- Moderate font size (40-48px)
- Clear, readable fonts

### Professional Content

- Use `underline` or `classic` style
- Conservative fonts (36-44px)
- Neutral colors
- Proper grammar and spacing

### Filler Words to Remove

Use the `replace` parameter to clean up transcripts:

```json
{
  "replace": [
    {"find": "um", "replace": ""},
    {"find": "uh", "replace": ""},
    {"find": "like", "replace": ""},
    {"find": "you know", "replace": ""},
    {"find": "sort of", "replace": ""},
    {"find": "kind of", "replace": ""}
  ]
}
```

**Advanced Replacements**:

```json
{
  "replace": [
    {"find": "gonna", "replace": "going to"},
    {"find": "wanna", "replace": "want to"},
    {"find": "&", "replace": "and"}
  ]
}
```

**Tips**:

- Replacements are case-insensitive
- Applied to all caption text before rendering
- Works with all caption styles
- Use empty string `""` to remove words completely

### Time Range Exclusion

Skip certain parts of the video (intros, outros, music breaks):

```json
{
  "exclude_time_ranges": [
    {"start": "00:00:00.000", "end": "00:00:05.000"},
    {"start": "00:05:30.000", "end": "00:05:40.000"}
  ]
}
```

**Format**: HH:MM:SS.mmm (hours:minutes:seconds.milliseconds)

**Use Cases**:

- Skip intro music (no speech)
- Remove outro credits
- Exclude background music sections
- Skip advertisement breaks

**How it works**: Any caption segment overlapping with excluded ranges is removed from output

## Performance Tips

### Processing Times

**Auto-transcription** (with Whisper):

- Small videos (<1 min): 10-30 seconds
- Medium videos (1-5 min): 30-120 seconds  
- Large videos (5-30 min): 2-10 minutes
- Depends on: audio quality, video length, language

**Caption rendering** (with provided captions):

- Classic style: 5-15 seconds
- Karaoke/Highlight: 10-30 seconds (depends on word count)
- Word-by-word: 15-45 seconds

### Optimization Tips

1. **Specify language**: Use `"language": "en"` instead of `"auto"` for 20-30% faster transcription
2. **Use async mode**: For videos > 1 minute, use `"sync": false` (default)
3. **Sync mode for testing**: Use `"sync": true` only for quick tests (<30 seconds)
4. **Pre-transcribe offline**: Provide SRT captions to skip transcription entirely
5. **Batch processing**: Queue multiple jobs to process in parallel

### When to Use Each Mode

**Auto-transcription**:

- Need word-level timestamps
- Using karaoke/highlight styles
- Don't have existing captions
- Audio is clear

**Provided SRT**:

- Have pre-timed captions
- Need exact timing control
- Want faster processing
- Classic style is sufficient

**Plain text**:

- Quick prototype/testing
- Don't care about precise timing
- Classic style only

## Troubleshooting

### Caption Visibility Issues

**Problem**: Captions hidden at bottom or cut off
**Solution**:

```json
{
  "settings": {
    "margin_v": 100,  // Increase vertical margin
    "position": "bottom_center",
    "font_size": 52  // Larger font for visibility
  }
}
```

**Problem**: Captions too small on mobile
**Solution**:

```json
{
  "settings": {
    "font_size": 56,  // Minimum 48 for mobile
    "outline_width": 6,  // Thicker outline for contrast
    "all_caps": true  // Better readability
  }
}
```

### max_words_per_line Not Working

**Problem**: Shows more words than specified
**Solution**: This is now fixed! The karaoke style correctly limits to exact word count.

- `max_words_per_line: 3` = exactly 3 words per line
- Works with both classic and karaoke styles

**Verification**:

```json
{
  "settings": {
    "style": "karaoke",
    "max_words_per_line": 3  // Guaranteed 3 words max
  }
}
```

### Transcription Issues

**Low transcription accuracy:**

- Ensure good audio quality (no background noise)
- Specify correct language: `"language": "en"`
- Check audio levels (not too quiet/loud)
- Consider using professional audio editing first

**Wrong language detected:**

- Always specify language when known
- Use `"language": "en"` instead of `"auto"`
- Supported: en, fr, es, de, it, pt, ru, zh, ja, ko, ar, hi, and 90+ more

**Missing word timestamps (karaoke doesn't work):**

- Word timestamps require auto-transcription
- SRT files get estimated word timings (less accurate)
- For best karaoke: use auto-transcription or word-level SRT

### Timing Issues

**Karaoke timing off:**

- Better audio = better timing
- Use auto-transcription for best results
- Consider pre-timed SRT with word-level timing
- Check audio sync in original video

**Captions appear too early/late:**

- Verify video audio sync
- Check SRT timing if provided
- Use exclude_time_ranges to skip problematic sections

### Performance Issues

**Job takes too long:**

- Auto-transcription adds significant time
- Specify language parameter (20-30% faster)
- Use provided SRT captions to skip transcription
- Consider pre-transcribing offline for large batches

**Out of memory errors:**

- Video too large (>2GB limit)
- Try shorter segments
- Use sync mode for small videos only
- Contact support for enterprise solutions

### Style-Specific Issues

**Classic style - text too long:**

```json
{"settings": {"max_words_per_line": 8}}  // Break into multiple lines
```

**Karaoke - no highlighting:**

- Requires word timestamps (auto-transcription)
- Check that transcription completed successfully
- Verify style is set to "karaoke"

**Highlight/Underline - no emphasis:**

- Requires word timestamps
- Check settings applied correctly
- Verify colors have sufficient contrast

### Color Issues

**Can't see text:**

```json
{
  "settings": {
    "line_color": "#FFFFFF",  // White text
    "outline_color": "#000000",  // Black outline
    "outline_width": 4  // Thick outline
  }
}
```

**Wrong colors applied:**

- Use hex format: "#RRGGBB"
- Include the "#" symbol
- Check color contrast
- ASS format uses BGR internally (handled automatically)

## Common Recipes

### Recipe 1: Perfect TikTok/Instagram Reels Captions

```json
{
  "video_url": "https://example.com/video.mp4",
  "settings": {
    "style": "karaoke",
    "line_color": "#FFFFFF",
    "word_color": "#FFFF00",
    "font_size": 56,
    "all_caps": true,
    "max_words_per_line": 3,
    "outline_width": 6,
    "outline_color": "#000000",
    "margin_v": 100,
    "position": "bottom_center",
    "bold": true
  },
  "language": "en"
}
```

**Why this works**: Large, bold text with high contrast, 3 words per line for easy reading, karaoke effect for engagement

### Recipe 2: Clean Interview/Podcast Captions

```json
{
  "video_url": "https://example.com/interview.mp4",
  "replace": [
    {"find": "um", "replace": ""},
    {"find": "uh", "replace": ""},
    {"find": "like", "replace": ""},
    {"find": "you know", "replace": ""}
  ],
  "exclude_time_ranges": [
    {"start": "00:00:00.000", "end": "00:00:05.000"}
  ],
  "settings": {
    "style": "classic",
    "font_size": 42,
    "max_words_per_line": 10,
    "position": "bottom_center",
    "margin_v": 90
  }
}
```

**Why this works**: Removes filler words, skips intro, classic readable style

### Recipe 3: Educational Tutorial with Emphasis

```json
{
  "video_url": "https://example.com/tutorial.mp4",
  "settings": {
    "style": "highlight",
    "line_color": "#FFFFFF",
    "word_color": "#00FFFF",
    "font_size": 44,
    "max_words_per_line": 8,
    "outline_width": 3,
    "position": "bottom_center",
    "margin_v": 85
  },
  "language": "en"
}
```

**Why this works**: Highlight style helps viewers follow along, 8 words is readable but not overwhelming

### Recipe 4: Motivational Quote (Dramatic)

```json
{
  "video_url": "https://example.com/motivational.mp4",
  "captions": "Never give up. Success is just around the corner. Believe in yourself.",
  "settings": {
    "style": "word_by_word",
    "font_size": 72,
    "all_caps": true,
    "position": "middle_center",
    "bold": true,
    "outline_width": 8,
    "line_color": "#FFFFFF",
    "outline_color": "#000000"
  }
}
```

**Why this works**: One word at a time creates dramatic impact, centered for focus

### Recipe 5: Multi-Language Content

```json
{
  "video_url": "https://example.com/spanish-video.mp4",
  "settings": {
    "style": "karaoke",
    "font_size": 50,
    "max_words_per_line": 4,
    "position": "bottom_center",
    "margin_v": 95
  },
  "language": "es"
}
```

**Why this works**: Specifying language improves accuracy and speed

### Recipe 6: Professional Corporate Video

```json
{
  "video_url": "https://example.com/corporate.mp4",
  "settings": {
    "style": "underline",
    "font_family": "Arial",
    "font_size": 38,
    "line_color": "#FFFFFF",
    "outline_width": 2,
    "position": "bottom_center",
    "margin_v": 75,
    "max_words_per_line": 10
  }
}
```

**Why this works**: Professional underline style, conservative sizing, clear readability

### Recipe 7: Music Video with Beat Sync

```json
{
  "video_url": "https://example.com/music-video.mp4",
  "captions": "https://example.com/lyrics-timed.srt",
  "settings": {
    "style": "karaoke",
    "line_color": "#FF00FF",
    "word_color": "#00FFFF",
    "font_size": 60,
    "all_caps": true,
    "max_words_per_line": 2,
    "position": "bottom_center",
    "margin_v": 110,
    "bold": true,
    "outline_width": 8
  }
}
```

**Why this works**: Pre-timed SRT for perfect beat sync, bold colorful style for music content

### Recipe 8: Accessibility Captions (Maximum Readability)

```json
{
  "video_url": "https://example.com/video.mp4",
  "settings": {
    "style": "classic",
    "font_family": "Arial",
    "font_size": 48,
    "line_color": "#FFFF00",
    "outline_color": "#000000",
    "outline_width": 5,
    "position": "bottom_center",
    "margin_v": 100,
    "max_words_per_line": 8
  }
}
```

**Why this works**: High contrast yellow on black, large font, simple classic style for accessibility

## Limitations

- Maximum video size: 2GB
- Maximum duration: 2 hours (auto-transcription)
- Supported formats: MP4, MOV, AVI, MKV, WEBM
- Processing time: 10-60 seconds per minute
- Languages: 99+ supported by Whisper
