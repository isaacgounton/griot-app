# YouTube Transcript Generation

This endpoint allows you to generate transcripts for YouTube videos, with options for language selection, translation, and output format.

## Generate YouTube Transcript Job

Generate a transcript for a YouTube video.

### Endpoint

```
POST /v1/media/youtube/transcripts
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "languages": ["en"],
  "translate_to": "es",
  "format": "json"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| video_url | string | Yes | URL of the YouTube video. |
| languages | array of strings | No | List of language codes in order of preference (e.g., `["en", "es"]`). Defaults to `["en"]`. |
| translate_to | string | No | Language code to translate transcript to (e.g., `"fr"`). |
| format | string | No | Output format for the transcript (`"json"`). Defaults to `"json"`. |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

### Example

#### Request

```bash
cURL -X POST \
  https://localhost:8000/v1/media/youtube/transcripts \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "languages": ["en"],
    "translate_to": "es"
  }'
```

#### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Job Status

Check the status of a YouTube transcript generation job.

### Endpoint

```
GET /v1/media/youtube/transcripts/{job_id}
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
    "transcript_url": "https://your-bucket.s3.your-region.amazonaws.com/transcripts/transcript_abc.json"
  },
  "error": null
}
```