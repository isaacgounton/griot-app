# WaveSpeed Video Generations

The WaveSpeed video generations endpoints allow you to create high-quality videos from text prompts or images using the WaveSpeedAI platform. WaveSpeedAI offers both text-to-video generation and image-to-video generation with advanced motion synthesis capabilities.

## Create Text-to-Video Generation Job

Generate a video from a text prompt using WaveSpeedAI's advanced AI models.

### Endpoint

```
POST /v1/videos/wavespeed/generate
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "prompt": "A majestic eagle soaring over mountain peaks at sunset",
  "model": "wan-2.2",
  "size": "832*480",
  "duration": 5,
  "seed": 42
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| prompt | string | Yes | Text prompt describing the video content (max 1000 characters) |
| model | string | No | WaveSpeedAI model version (wan-2.2, minimax-video-02, minimax-video-01, default: wan-2.2) |
| size | string | No | Video dimensions (832*480, 480*832, default: 832*480) |
| duration | number | No | Video duration in seconds (5, 8, default: 5) |
| seed | number | No | Random seed for reproducible results (-1 for random, default: -1) |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Text-to-Video Job Status

Check the status of a WaveSpeedAI text-to-video generation job.

### Endpoint

```
GET /v1/videos/wavespeed/generate/{job_id}
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
    "video_url": "https://cdn.localhost:8000/videos/j-123e4567.mp4",
    "prompt_used": "A majestic eagle soaring over mountain peaks at sunset",
    "model_used": "wan-2.2",
    "size_used": "832*480",
    "duration_used": 5,
    "seed_used": 42,
    "provider": "wavespeed"
  },
  "error": null
}
```

## Create Image-to-Video Generation Job

Generate a video from an image using WaveSpeedAI's advanced motion synthesis technology.

### Endpoint

```
POST /v1/videos/wavespeed/image_to_video
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | multipart/form-data |

### Request Body (Form Data)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| prompt | string | Yes | Text prompt describing the video motion/content (max 1000 characters) |
| image | file | Yes | Image file to animate (PNG, JPG, JPEG up to 10MB) |
| seed | number | No | Random seed for reproducible results (-1 for random, default: -1) |
| model | string | No | WaveSpeedAI model version (default: wan-2.2) |
| resolution | string | No | Video resolution (default: 720p) |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Image-to-Video Job Status

Check the status of a WaveSpeedAI video generation job.

### Endpoint

```
GET /v1/videos/wavespeed/image_to_video/{job_id}
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
    "original_image_url": "https://cdn.localhost:8000/images/j-123e4567.png",
    "video_url": "https://cdn.localhost:8000/videos/j-123e4567.mp4",
    "prompt_used": "make the ocean waves move gently and birds fly across the sky",
    "seed_used": 42,
    "model_used": "wan-2.2",
    "resolution_used": "720p",
    "provider": "wavespeed"
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

## Examples

### Example 1: Text-to-Video Generation

```bash
curl -X POST \
  https://localhost:8000/v1/videos/wavespeed/generate \
  -H 'X-API-Key: your-api-key' \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "A majestic eagle soaring over mountain peaks at sunset, cinematic shot",
    "model": "wan-2.2",
    "size": "832*480",
    "duration": 5,
    "seed": 42
  }'
```

### Example 2: Animate a Nature Scene

```bash
curl -X POST \
  https://localhost:8000/v1/videos/wavespeed/image_to_video \
  -H 'X-API-Key: your-api-key' \
  -F 'prompt=make the ocean waves move gently with seagulls flying overhead' \
  -F 'image=@beach_scene.jpg' \
  -F 'resolution=720p' \
  -F 'seed=42'
```

### Example 3: Animate a Portrait

```bash
curl -X POST \
  https://localhost:8000/v1/videos/wavespeed/image_to_video \
  -H 'X-API-Key: your-api-key' \
  -F 'prompt=subtle breathing motion and gentle hair movement in the wind' \
  -F 'image=@portrait.png' \
  -F 'model=wan-2.2' \
  -F 'resolution=1080p'
```

### Example 4: Check Job Status

```bash
curl -X GET \
  https://localhost:8000/v1/videos/wavespeed/image_to_video/j-123e4567-e89b-12d3-a456-426614174000 \
  -H 'X-API-Key: your-api-key'
```

## Model Information

WaveSpeedAI specializes in high-quality image-to-video generation with the following capabilities:

- **Advanced Motion Synthesis**: Creates realistic motion from static images
- **High Resolution Support**: Supports 720p and 1080p video generation
- **Natural Motion**: Produces smooth, coherent motion that looks natural
- **Flexible Control**: Fine-tune generation with prompts and seed values
- **Fast Processing**: Optimized for quick turnaround times

### Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| wan-2.2 | Latest WaveSpeedAI model with improved motion quality | General purpose, recommended |

### Supported Resolutions

| Resolution | Aspect Ratio | Best For |
|------------|--------------|----------|
| 720p | 16:9 | Social media, web content |
| 1080p | 16:9 | High-quality content, presentations |

## Performance Notes

- **Processing Time**: Typically 30-120 seconds depending on resolution and complexity
- **File Size Limits**: Input images up to 10MB supported
- **Queue System**: Jobs are processed asynchronously with status polling
- **Reproducibility**: Use seed values for consistent results across generations

## Best Practices

### Prompt Writing Tips

1. **Be Specific**: Describe the exact motion you want to see
   - Good: "gentle ocean waves lapping at the shore with birds flying overhead"
   - Poor: "make it move"

2. **Focus on Motion**: Emphasize movement and dynamics
   - Examples: "flowing hair in the wind", "flickering candle flame", "falling leaves"

3. **Consider Physics**: Describe realistic motion patterns
   - Examples: "water cascading down rocks", "smoke rising slowly upward"

### Image Preparation

1. **High Quality**: Use clear, well-lit images for best results
2. **Composition**: Images with clear subjects work better than busy scenes
3. **Format**: PNG and JPEG formats are supported
4. **Size**: Keep images under 10MB for optimal processing

## Error Responses

### 404 Not Found

```json
{
  "detail": "Job with ID j-123e4567-e89b-12d3-a456-426614174000 not found"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid API key"
}
```

### 400 Bad Request

```json
{
  "detail": "Invalid file type. Please upload a PNG or JPEG image."
}
```

### 503 Service Unavailable

```json
{
  "detail": "WaveSpeedAI service is not available. Please check WAVESPEEDAI_API_KEY configuration."
}
```

### 500 Internal Server Error

```json
{
  "detail": "WaveSpeedAI video generation failed: [error details]"
}
```

## Comparison with Other Services

| Feature | WaveSpeedAI | LTX-Video |
|---------|-------------|-----------|
| Input Types | Image-to-Video only | Text-to-Video, Image-to-Video |
| Motion Quality | Excellent natural motion | High-quality general video |
| Processing Speed | Fast (30-120s) | Moderate (30-180s) |
| Specialization | Motion synthesis | General video generation |
| Best Use Cases | Animating photos, portraits | Creative video generation |