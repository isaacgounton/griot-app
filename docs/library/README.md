# Library Management API

The Library Management API provides organized access to all generated content including videos, images, audio files, and documents. Content is automatically catalogued and made searchable with comprehensive metadata.

## Overview

The Library system provides:
- **Organized Content**: Automatically categorize videos, images, audio, and text
- **Persistent Storage**: Database-backed content management with S3 storage
- **Advanced Search**: Filter by content type, date, job type, and metadata
- **Bulk Operations**: Download, delete, and organize multiple items
- **Detailed Metadata**: Comprehensive information about each generated item

## Base URL

All library endpoints use the prefix: `/api/v1/library`

## Content Organization

### Content Types

The library organizes content into these categories:

- **Videos**: Generated videos, YouTube Shorts, concatenated content
- **Audio**: TTS speech, music generation, transcriptions
- **Images**: AI-generated images, thumbnails, processed images
- **Text**: Generated scripts, transcripts, documents

### Automatic Cataloging

Content is automatically added to the library when jobs complete successfully:
- File URLs are extracted and stored
- Metadata is parsed and indexed
- Thumbnails are generated for videos and images
- Duration and size information is captured

## API Endpoints

### List Library Content

Retrieve paginated library content with filtering options.

```bash
curl -X GET "http://localhost:8000/api/v1/library/?content_type=video&limit=20" \
  -H "X-API-Key: your_api_key"
```

**Query Parameters:**
- `content_type`: Filter by type (`video`, `audio`, `image`, `text`, `all`)
- `limit`: Items per page (default: 50, max: 200)
- `offset`: Skip N items for pagination (default: 0)
- `job_type`: Filter by specific job type (optional)
- `search`: Search in titles and descriptions (optional)
- `date_from`: Filter items created after date (ISO format)
- `date_to`: Filter items created before date (ISO format)
- `sort_by`: Sort field (`created_at`, `updated_at`, `title`, `file_size`)
- `sort_order`: Sort direction (`asc`, `desc`)

**Response:**
```json
{
  "items": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "job_type": "footage_to_video",
      "content_type": "video",
      "title": "Amazing Ocean Facts",
      "description": "Educational video about ocean discoveries",
      "file_url": "https://s3.../videos/ocean_facts_final.mp4",
      "thumbnail_url": "https://s3.../thumbnails/ocean_facts_thumb.jpg",
      "file_size": 15728640,
      "duration": 60.5,
      "dimensions": {"width": 1920, "height": 1080},
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "metadata": {
        "voice_provider": "kitten",
        "voice_name": "expr-voice-5-f",
        "resolution": "1080p"
      },
      "parameters": {
        "topic": "amazing ocean facts",
        "duration": 60
      }
    }
  ],
  "pagination": {
    "total_count": 1250,
    "limit": 20,
    "offset": 0,
    "has_more": true
  },
  "summary": {
    "total_videos": 500,
    "total_images": 300,
    "total_audio": 200,
    "total_text": 250,
    "total_size_mb": 15000
  }
}
```

### Get Content Item Details

Retrieve detailed information about a specific library item.

```bash
curl -X GET "http://localhost:8000/api/v1/library/{job_id}" \
  -H "X-API-Key: your_api_key"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "footage_to_video",
  "content_type": "video",
  "title": "Amazing Ocean Facts",
  "description": "Educational video about ocean discoveries",
  "file_url": "https://s3.../videos/ocean_facts_final.mp4",
  "thumbnail_url": "https://s3.../thumbnails/ocean_facts_thumb.jpg",
  "file_size": 15728640,
  "duration": 60.5,
  "dimensions": {"width": 1920, "height": 1080},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "voice_provider": "kitten",
    "voice_name": "expr-voice-5-f",
    "script_generated": "The ocean covers 71% of Earth's surface...",
    "background_videos_count": 12,
    "captions_enabled": true
  },
  "parameters": {
    "topic": "amazing ocean facts",
    "duration": 60,
    "voice_provider": "kitten"
  },
  "s3_details": {
    "bucket": "your-s3-bucket",
    "key": "videos/ocean_facts_final.mp4",
    "last_modified": "2024-01-15T10:30:00Z",
    "etag": "\"d41d8cd98f00b204e9800998ecf8427e\""
  }
}
```

### Search Library Content

Advanced search across all library content.

```bash
curl -X GET "http://localhost:8000/api/v1/library/search?q=ocean+facts&content_type=video" \
  -H "X-API-Key: your_api_key"
```

**Query Parameters:**
- `q`: Search query (searches title, description, metadata)
- `content_type`: Limit to specific content type
- `limit`: Results limit (default: 20)
- `offset`: Pagination offset

### Delete Library Item

Remove an item from the library (optionally delete from S3).

```bash
curl -X DELETE "http://localhost:8000/api/v1/library/{job_id}?delete_files=true" \
  -H "X-API-Key: your_api_key"
```

**Query Parameters:**
- `delete_files`: Also delete files from S3 storage (default: false)

### Library Statistics

Get comprehensive library statistics and usage metrics.

```bash
curl -X GET "http://localhost:8000/api/v1/library/stats" \
  -H "X-API-Key: your_api_key"
```

**Response:**
```json
{
  "total_items": 1250,
  "content_breakdown": {
    "video": 500,
    "image": 300, 
    "audio": 200,
    "text": 250
  },
  "storage_usage": {
    "total_size_bytes": 15728640000,
    "total_size_mb": 15000,
    "total_size_gb": 15.0,
    "by_type": {
      "video": {"count": 500, "size_mb": 12000},
      "image": {"count": 300, "size_mb": 1500},
      "audio": {"count": 200, "size_mb": 1000},
      "text": {"count": 250, "size_mb": 500}
    }
  },
  "creation_timeline": {
    "last_24h": 25,
    "last_week": 180,
    "last_month": 750,
    "last_year": 1250
  },
  "top_job_types": [
    {"job_type": "footage_to_video", "count": 200},
    {"job_type": "image_generation", "count": 150},
    {"job_type": "yt_shorts", "count": 120},
    {"job_type": "audio_speech", "count": 100}
  ]
}
```

## Content Types and Job Type Mapping

### Video Content
Job types that produce video content:
- `footage_to_video` - Topic-based video generation
- `yt_shorts` - YouTube Shorts creation
- `scenes_to_video` - Scene-based video creation
- `aiimage_to_video` - Image-to-video conversion
- `image_to_video` - Static image animation
- `video_concatenation` - Multiple video joining
- `video_merge` - Video with audio merging

### Audio Content  
Job types that produce audio content:
- `audio_speech` - Text-to-speech generation
- `audio_music` - Music generation
- `audio_transcription` - Audio-to-text transcription
- `voice_synthesis` - Voice generation

### Image Content
Job types that produce image content:
- `image_generation` - AI image creation
- `image_enhancement` - Image processing
- `image_overlay` - Image composition
- `thumbnail_generation` - Video thumbnails

### Text Content
Job types that produce text content:
- `script_generation` - Video script creation
- `document_conversion` - PDF/DOC to Markdown
- `text_generation` - AI text creation
- `transcription` - Audio/video transcription

## Advanced Features

### Bulk Operations

Download multiple items as ZIP archive:
```bash
curl -X POST "http://localhost:8000/api/v1/library/bulk/download" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440001"
    ]
  }'
```

Delete multiple items:
```bash
curl -X DELETE "http://localhost:8000/api/v1/library/bulk" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_ids": ["job1", "job2"],
    "delete_files": true
  }'
```

### Metadata Management

Update item metadata:
```bash
curl -X PATCH "http://localhost:8000/api/v1/library/{job_id}/metadata" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Ocean Facts Video",
    "description": "Enhanced educational content about marine life",
    "tags": ["education", "ocean", "marine-biology"]
  }'
```

### Content Organization

Create and manage content collections:
```bash
curl -X POST "http://localhost:8000/api/v1/library/collections" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Educational Videos",
    "description": "Collection of educational content",
    "job_ids": ["job1", "job2", "job3"]
  }'
```

## Integration Examples

### Automatic Library Updates

The library automatically updates when jobs complete. Here's how it works:

```python
# When a job completes successfully
job_result = {
    "final_video_url": "https://s3.../video.mp4",
    "thumbnail_url": "https://s3.../thumb.jpg",
    "script_generated": "Amazing content...",
    "duration": 60.5
}

# Library service automatically:
# 1. Extracts media URLs
# 2. Analyzes file metadata
# 3. Creates library entry
# 4. Indexes for search
```

### Frontend Integration

Display library content in your frontend:

```javascript
// Fetch library content
const response = await fetch('/api/v1/library/?content_type=video&limit=12', {
  headers: { 'X-API-Key': 'your_api_key' }
});

const library = await response.json();

// Display in grid layout
library.items.forEach(item => {
  displayContentCard({
    title: item.title,
    thumbnail: item.thumbnail_url,
    duration: item.duration,
    created: item.created_at,
    downloadUrl: item.file_url
  });
});
```

### Backup and Export

Export library metadata for backup:
```bash
curl -X GET "http://localhost:8000/api/v1/library/export" \
  -H "X-API-Key: your_api_key" \
  > library_backup.json
```

## Performance Considerations

### Pagination
- Use reasonable `limit` values (20-50 items per page)
- Implement proper offset-based pagination
- Consider cursor-based pagination for large datasets

### Caching
- Library responses are cached for 5 minutes
- Statistics are cached for 15 minutes
- Use conditional requests with ETags when possible

### Storage Optimization
- Regularly clean up old/unused content
- Implement automated archiving for old content
- Monitor storage usage with the stats endpoint

## Error Handling

### Common Errors

**Item Not Found:**
```json
{
  "detail": "Library item not found"
}
```

**Invalid Content Type:**
```json
{
  "detail": "Invalid content_type. Must be one of: video, audio, image, text, all"
}
```

**Storage Error:**
```json
{
  "detail": "Failed to access S3 storage for file deletion"
}
```

### Error Recovery

1. **Missing Files**: Items remain in library even if S3 files are deleted
2. **Metadata Corruption**: Library rebuilds metadata from job results
3. **Search Issues**: Full-text search rebuilds indexes automatically

## Best Practices

1. **Regular Cleanup**: Remove unused content to manage storage costs
2. **Metadata Enhancement**: Add descriptive titles and tags for better search
3. **Content Organization**: Use collections to group related content
4. **Monitoring**: Track storage usage and growth trends
5. **Backup**: Regular exports of library metadata

---

*The Library Management system provides persistent, organized access to all your generated content with powerful search and management capabilities.*