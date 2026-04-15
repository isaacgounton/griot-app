# Media Download

The media download endpoints allow you to download media from various URLs including YouTube videos, with both basic and enhanced features.

## Basic Media Download

Download media from a URL with intelligent format detection and fallback support.

### Endpoint

```
POST /api/v1/media/download
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format": "best",
  "file_name": "rick_roll.mp4",
  "cookies_url": "https://example.com/my_cookies.txt",
  "sync": false,
  "extract_subtitles": false,
  "subtitle_languages": ["en", "auto"],
  "subtitle_formats": ["srt", "vtt"],
  "extract_thumbnail": false,
  "embed_metadata": true,
  "thumbnail_format": "jpg"
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | The URL of the media to download |
| format | string | No | "best" | Format selector (best, mp3, mp4, 720p, 480p, etc.) |
| file_name | string | No | null | Custom filename. If not provided, yt-dlp will determine the name |
| cookies_url | string | No | null | URL to a Netscape-formatted cookies file for authentication |
| sync | boolean | No | false | If True, return response immediately. If False (default), create async job |
| extract_subtitles | boolean | No | false | Extract subtitles from the media |
| subtitle_languages | array | No | ["en", "auto"] | Subtitle languages to extract |
| subtitle_formats | array | No | ["srt", "vtt"] | Subtitle output formats |
| extract_thumbnail | boolean | No | false | Extract thumbnail from the media |
| embed_metadata | boolean | No | true | Embed metadata in the output file |
| thumbnail_format | string | No | "jpg" | Thumbnail format (jpg, png, webp) |

### Response

#### Async Response (default)
```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

#### Sync Response (sync=true)
```json
{
  "success": true,
  "file_url": "https://your-bucket.s3.your-region.amazonaws.com/my_downloaded_video.mp4",
  "title": "Video Title",
  "duration": 213,
  "uploader": "Channel Name",
  "upload_date": "20241215",
  "download_method": "yt-dlp"
}
```

### Example

#### Request

```bash
curl -X POST "http://localhost:8000/api/v1/media/download" \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "mp4",
    "file_name": "my_downloaded_video.mp4",
    "cookies_url": "https://example.com/my_cookies.txt",
    "extract_subtitles": true,
    "subtitle_languages": ["en", "es"],
    "extract_thumbnail": true,
    "sync": true
  }'
```

#### Response

```json
{
  "success": true,
  "file_url": "https://your-bucket.s3.your-region.amazonaws.com/my_downloaded_video.mp4",
  "thumbnail_url": "https://your-bucket.s3.your-region.amazonaws.com/my_downloaded_video.jpg",
  "subtitle_urls": [
    "https://your-bucket.s3.your-region.amazonaws.com/my_downloaded_video_en.srt",
    "https://your-bucket.s3.your-region.amazonaws.com/my_downloaded_video_es.srt"
  ],
  "title": "Never Gonna Give You Up",
  "duration": 213,
  "uploader": "Rick Astley",
  "upload_date": "20091025",
  "download_method": "enhanced-yt-dlp",
  "extracted_subtitles": true,
  "extracted_thumbnail": true,
  "total_files": 3
}
```

## Supported Features

### Platform Detection
The endpoint automatically detects the platform and uses the appropriate download method:

- **Media Platforms** (YouTube, Vimeo, TikTok, etc.): Uses yt-dlp
- **Direct Downloads** (PDFs, images, documents): Uses HTTP download
- **Authenticated Content**: Supports cookies for private/protected content

### Format Options
- `"best"`: Best quality available
- `"mp4"`: Best MP4 format
- `"mp3"`: Extract audio only as MP3
- `"720p"`, `"480p"`, `"360p"`: Video height specifications
- Any yt-dlp format selector

### Authentication
- **Cookies**: Upload cookies file URL for authenticated access
- **Private Content**: Download YouTube private videos, Vimeo protected content
- **Session Management**: Maintain login sessions across requests

## Enhanced Media Download

For advanced features like subtitle extraction, thumbnail generation, and multi-language support, see the [Enhanced Media Download](./ENHANCED_DOWNLOAD.md) documentation.

## Job Status

All download jobs use the centralized job status system:

### Check Job Status

```
GET /api/v1/jobs/{job_id}/status
```

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/j-123e4567-e89b-12d3-a456-426614174000/status" \
  -H 'X-API-Key: your-api-key'
```

Response:
```json
{
  "success": true,
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "data": {
    "id": "j-123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "operation": "media_download",
    "params": {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "format": "mp4"
    },
    "result": {
      "file_url": "https://your-bucket.s3.your-region.amazonaws.com/my_downloaded_video.mp4",
      "title": "Never Gonna Give You Up",
      "download_method": "yt-dlp"
    },
    "error": null,
    "created_at": "2024-12-15T10:30:00.123456",
    "updated_at": "2024-12-15T10:32:15.654321"
  }
}
```

## Error Handling

Common error responses:

### Invalid URL
```json
{
  "detail": "URL is required"
}
```

### Download Failed
```json
{
  "detail": "Failed to create media download job"
}
```

### Platform Not Supported
```json
{
  "detail": "Media download failed: Unable to download from this platform"
}
```

## Use Cases

- **Content Curation**: Download videos for offline viewing or processing
- **Social Media**: Save TikTok, Instagram, or YouTube content
- **Audio Extraction**: Extract audio from videos for podcast creation
- **Archival**: Backup important video content
- **Batch Processing**: Process multiple downloads using job queue
- **Integration**: Use sync mode for immediate results in workflows

## Best Practices

1. **Use sync=false** for large files or playlists to avoid timeouts
2. **Provide cookies** for private or protected content
3. **Choose appropriate formats** to balance quality and file size
4. **Custom filenames** for better organization
5. **Monitor job status** for long-running downloads
6. **Rate limiting**: Respect platform rate limits and terms of service