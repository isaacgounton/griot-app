# S3 File Upload

The S3 upload endpoint allows you to upload files to your configured S3 bucket with automatic MIME type detection, file metadata extraction, and comprehensive error handling.

## Upload File

Upload a file to S3.

### Endpoint

```
POST /api/v1/s3/upload
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | multipart/form-data |

### Request Body

This endpoint accepts `multipart/form-data`.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | file | Yes | The file to upload. |
| file_name | string | No | An optional file name. If not provided, the original file name will be used. |

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
  https://localhost:8000/api/v1/s3/upload \
  -H 'Content-Type: multipart/form-data' \
  -H 'X-API-Key: your-api-key' \
  -F 'file=@/path/to/your/file.png' \
  -F 'file_name=custom_name.png'
```

#### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Job Status

Check the status of an upload job.

### Endpoint

```
GET /api/v1/jobs/{job_id}/status
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

#### Pending/Processing Status

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "result": null,
  "error": null
}
```

#### Completed Status

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "file_url": "https://your-bucket.s3.your-region.amazonaws.com/custom_name.png",
    "file_name": "custom_name.png",
    "file_extension": "png",
    "mime_type": "image/png",
    "file_size": 1048576,
    "file_size_mb": "1.0 MB"
  },
  "error": null
}
```

#### Failed Status

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "failed",
  "result": null,
  "error": "Upload failed: S3 connection timeout"
}
```

## Features

### Automatic MIME Type Detection

The service automatically detects MIME types for uploaded files using a sophisticated detection system:

1. **Filename-based Detection**: Prioritizes the intended filename (from `file_name` parameter or original filename) for accurate MIME type identification
2. **Extension Mapping**: Comprehensive mapping of file extensions to MIME types
3. **Fallback Protection**: Falls back to `application/octet-stream` if detection fails

### Supported File Types

| File Type | Extensions | MIME Type |
|-----------|------------|-----------|
| **Videos** | .mp4, .webm, .mov, .avi, .mkv, .m4v, .wmv, .flv | video/mp4, video/webm, etc. |
| **Images** | .jpg, .jpeg, .png, .gif, .webp, .bmp, .tiff, .svg | image/jpeg, image/png, etc. |
| **Audio** | .mp3, .wav, .ogg, .flac, .aac, .m4a, .wma | audio/mpeg, audio/wav, etc. |
| **Documents** | .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx | application/pdf, etc. |
| **Archives** | .zip, .rar, .7z, .tar, .gz | application/zip, etc. |
| **Text** | .txt, .csv, .json, .xml, .html, .css, .js | text/plain, etc. |

### File Metadata

The completed upload provides comprehensive metadata:

- **file_url**: Direct URL to the uploaded file
- **file_name**: Final filename used in S3
- **file_extension**: File extension (without dot)
- **mime_type**: Detected MIME type
- **file_size**: File size in bytes
- **file_size_mb**: Human-readable file size

## Upload from URL

Upload a file from an external URL to S3.

### Endpoint

```
POST /v1/s3/upload-from-url
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "url": "https://example.com/file.jpg",
  "file_name": "custom_name.jpg"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| url | string | Yes | The URL of the file to upload |
| file_name | string | No | Custom filename. If not provided, extracted from URL |

### Response

Same job-based response format as regular file upload.

### Example

#### Request

```bash
curl -X POST \
  https://localhost:8000/v1/s3/upload-from-url \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "url": "https://example.com/image.jpg",
    "file_name": "downloaded_image.jpg"
  }'
```

## Error Handling

The service provides detailed error messages for common issues:

- **File Too Large**: If file exceeds size limits
- **Invalid File Type**: If file type is not supported (when restrictions are enabled)
- **S3 Connection Issues**: Network or credential problems
- **Invalid URL**: For URL-based uploads with malformed URLs

## Best Practices

1. **Use Descriptive Filenames**: Provide meaningful `file_name` parameters for better organization
2. **Check Job Status**: Always poll the job status endpoint for completion
3. **Handle Errors**: Implement proper error handling for failed uploads
4. **File Size Optimization**: Compress large files before uploading when possible
5. **MIME Type Verification**: The returned `mime_type` can be used to verify successful detection

## Recent Improvements

### Enhanced MIME Type Detection (Latest Update)

The S3 service now features improved MIME type detection that properly identifies video files:

- **Fixed MP4 Detection**: MP4 files now correctly return `video/mp4` instead of `application/octet-stream`
- **Prioritized Filename Detection**: Uses intended filename over temporary file paths for accurate type detection
- **Comprehensive Video Support**: All video formats (.mp4, .webm, .mov, .avi, etc.) get correct MIME types
- **Backward Compatible**: All existing functionality remains unchanged

This fix ensures that video processing pipelines return the correct MIME type metadata for generated content.
