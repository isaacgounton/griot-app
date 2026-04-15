# LTX Video Generations

The LTX video generations endpoint allows you to create high-quality videos from text prompts or images using the Lightricks LTX-Video model deployed on Modal. This endpoint follows OpenAI conventions.

## Create Text-to-Video Generation Job

Generate a video from a text prompt using the LTX-Video model.

### Endpoint

```
POST /v1/videos/generate
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "prompt": "A beautiful sunset over mountains with clouds drifting by",
  "negative_prompt": "blurry, low quality, distorted",
  "width": 704,
  "height": 480,
  "num_frames": 150,
  "num_inference_steps": 200,
  "guidance_scale": 4.5,
  "seed": 42
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| prompt | string | Yes | Text prompt describing the video to generate (max 1000 characters) |
| negative_prompt | string | No | Text prompt for what to avoid in the video (default: "") |
| width | number | No | Video width in pixels (must be divisible by 32, default: 704) |
| height | number | No | Video height in pixels (must be divisible by 32, default: 480) |
| num_frames | number | No | Number of frames to generate (1-257, default: 150) |
| num_inference_steps | number | No | Number of inference steps (1-500, default: 200) |
| guidance_scale | number | No | Guidance scale for prompt adherence (1.0-20.0, default: 4.5) |
| seed | number | No | Random seed for reproducible results (default: null) |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Create Image-to-Video Generation Job

Generate a video from an image with a text prompt using the LTX-Video model.

### Endpoint

```
POST /v1/videos/from_image
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
| negative_prompt | string | No | Text prompt for what to avoid in the video (default: "") |
| width | number | No | Video width in pixels (must be divisible by 32, default: 704) |
| height | number | No | Video height in pixels (must be divisible by 32, default: 480) |
| num_frames | number | No | Number of frames to generate (1-257, default: 150) |
| num_inference_steps | number | No | Number of inference steps (1-500, default: 200) |
| guidance_scale | number | No | Guidance scale for prompt adherence (1.0-20.0, default: 4.5) |
| seed | number | No | Random seed for reproducible results (default: null) |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Text-to-Video Job Status

Check the status of a text-to-video generation job.

### Endpoint

```
GET /v1/videos/generate/{job_id}
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
    "prompt_used": "A beautiful sunset over mountains with clouds drifting by",
    "negative_prompt_used": "blurry, low quality, distorted",
    "dimensions": {
      "width": 704,
      "height": 480
    },
    "num_frames": 150,
    "processing_time": 45.2
  },
  "error": null
}
```

## Get Image-to-Video Job Status

Check the status of an image-to-video generation job.

### Endpoint

```
GET /v1/videos/from_image/{job_id}
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
    "prompt_used": "make the flowers bloom and butterflies fly",
    "negative_prompt_used": "blurry, low quality",
    "dimensions": {
      "width": 704,
      "height": 480
    },
    "num_frames": 150,
    "processing_time": 52.7
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
  https://localhost:8000/v1/videos/generate \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "prompt": "A cat walking through a garden with flowers blooming",
    "width": 704,
    "height": 480,
    "num_frames": 150,
    "num_inference_steps": 200,
    "guidance_scale": 4.5
  }'
```

### Example 2: Image-to-Video Generation

```bash
curl -X POST \
  https://localhost:8000/v1/videos/from_image \
  -H 'X-API-Key: your-api-key' \
  -F 'prompt=make the cat walk and play with a ball' \
  -F 'image=@cat_photo.jpg' \
  -F 'width=704' \
  -F 'height=480' \
  -F 'num_frames=150' \
  -F 'num_inference_steps=200' \
  -F 'guidance_scale=4.5'
```

### Example 3: Check Job Status

```bash
curl -X GET \
  https://localhost:8000/v1/videos/generate/j-123e4567-e89b-12d3-a456-426614174000 \
  -H 'X-API-Key: your-api-key'
```

## Model Information

The LTX-Video model is a state-of-the-art video generation model developed by Lightricks that can generate high-quality videos from text prompts or animate existing images. Key features include:

- **Fast Generation**: Capable of generating 20-second 480p videos in as little as 2 seconds on a warm container
- **High Quality**: Produces smooth, coherent videos with good temporal consistency
- **Flexible Input**: Supports both text-to-video and image-to-video generation
- **Customizable Parameters**: Fine-tune generation with various parameters like guidance scale, inference steps, and frame count

## Performance Notes

- **Cold Start**: First generation after inactivity may take longer due to model loading (typically 20-30 seconds)
- **Warm Containers**: Subsequent generations are much faster (typically 5-15 seconds)
- **Resolution**: Videos are generated at the specified resolution, which must be divisible by 32
- **Frame Count**: More frames result in longer videos but also longer processing times
- **Inference Steps**: Higher values generally produce better quality but take longer to generate

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
  "detail": "Width and height must be divisible by 32"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Video generation failed: [error details]"
}