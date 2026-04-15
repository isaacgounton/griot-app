# Web Screenshot API

Advanced webpage screenshot service using Playwright with full browser automation capabilities.

## Overview

The web screenshot service provides comprehensive webpage capture capabilities with device emulation, content injection, and advanced rendering options.

## Base Endpoint
```
POST /api/v1/image/web_screenshot/capture
```

## Features

### Device Emulation
- **Desktop**: 1920x1080 viewport, desktop user agent
- **Mobile**: 375x667 viewport, mobile user agent, touch events
- **Tablet**: 768x1024 viewport, tablet user agent, touch events
- **Custom**: Custom viewport dimensions

### Screenshot Options
- **Formats**: PNG (default), JPEG
- **JPEG Quality**: 1-100 (only for JPEG format)
- **Full Page**: Capture entire webpage or just viewport
- **Element Targeting**: Capture specific CSS selectors
- **Custom Dimensions**: Override device viewport sizes

### Advanced Features
- **Content Injection**: HTML, CSS, JavaScript injection
- **Cookie Support**: Custom cookies for authentication
- **Custom Headers**: HTTP header manipulation
- **Wait Conditions**: Wait for selectors or time delays
- **Color Schemes**: Light/dark/no-preference
- **Media Types**: Screen/print emulation

## Request Model

```json
{
  "url": "https://example.com",
  "width": 1920,
  "height": 1080,
  "device_type": "desktop",
  "format": "png",
  "quality": 80,
  "wait_for_selector": "#content",
  "wait_time": 3000,
  "full_page": true,
  "selector": ".main-content",
  "cookies": [
    {
      "name": "session",
      "value": "abc123",
      "domain": "example.com"
    }
  ],
  "headers": {
    "Authorization": "Bearer token"
  },
  "html_inject": "<div>Custom HTML</div>",
  "css_inject": "body { background: red; }",
  "js_inject": "console.log('Injected JS');",
  "color_scheme": "dark",
  "media_type": "screen",
  "ignore_https_errors": true,
  "timeout": 30000,
  "sync": false
}
```

## Usage Examples

### Basic Screenshot
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "sync": true
  }'
```

### Mobile Device Screenshot
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "device_type": "mobile",
    "format": "png",
    "sync": true
  }'
```

### Element-Specific Screenshot
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "selector": ".product-card",
    "wait_for_selector": ".product-card",
    "sync": true
  }'
```

### Screenshot with Authentication
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://protected-site.com",
    "cookies": [
      {
        "name": "auth_token",
        "value": "token123",
        "domain": "protected-site.com"
      }
    ],
    "headers": {
      "Authorization": "Bearer token123"
    },
    "sync": true
  }'
```

### Full Page Screenshot with Dark Mode
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "full_page": true,
    "color_scheme": "dark",
    "format": "jpeg",
    "quality": 90,
    "sync": true
  }'
```

### Async Processing
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "full_page": true,
    "device_type": "desktop",
    "sync": false
  }'
```

Response:
```json
{
  "job_id": "abc-123",
  "message": "Screenshot job started. Use /api/v1/jobs/{job_id}/status to check progress.",
  "status_endpoint": "/api/v1/jobs/abc-123/status"
}
```

## Quick Endpoints

### Element Screenshot
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture/element" \
  -H "X-API-Key: your_api_key" \
  -d "url=https://example.com&selector=.header&device_type=desktop"
```

### Full Page Screenshot
```bash
curl -X POST "http://localhost:8000/api/v1/image/web_screenshot/capture/fullpage" \
  -H "X-API-Key: your_api_key" \
  -d "url=https://example.com&format=png&quality=100"
```

## Device Information

Get available device configurations:
```bash
curl -X GET "http://localhost:8000/api/v1/image/web_screenshot/devices" \
  -H "X-API-Key: your_api_key"
```

Response:
```json
[
  {
    "type": "desktop",
    "name": "Desktop",
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "device_scale_factor": 1.0,
    "is_mobile": false,
    "has_touch": false
  },
  {
    "type": "mobile",
    "name": "Mobile",
    "viewport": {
      "width": 375,
      "height": 667
    },
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "device_scale_factor": 2.0,
    "is_mobile": true,
    "has_touch": true
  }
]
```

## Response Format

### Sync Response
```json
{
  "success": true,
  "screenshot_url": "https://your-s3-bucket.s3.amazonaws.com/screenshots/abc123.png",
  "metadata": {
    "url": "https://example.com",
    "device_type": "desktop",
    "format": "png",
    "dimensions": {
      "width": 1920,
      "height": 1080
    },
    "full_page": false,
    "file_size": 245760,
    "execution_time": 2.34,
    "screenshot_id": "abc-123"
  },
  "execution_time": 2.34,
  "message": "Screenshot captured successfully"
}
```

### Async Response
```json
{
  "job_id": "abc-123-def",
  "message": "Screenshot job started. Use /api/v1/jobs/{job_id}/status to check progress.",
  "status_endpoint": "/api/v1/jobs/abc-123-def/status"
}
```

## Error Handling

Common error responses:
```json
{
  "detail": "Screenshot capture failed: Timeout waiting for selector .content"
}
```

## Use Cases

- **UI Testing**: Automated screenshot testing of web applications
- **Monitoring**: Periodic webpage monitoring with visual comparison
- **Documentation**: Generate screenshots for technical documentation
- **Social Media**: Create social media preview images from web content
- **Archiving**: Archive webpage visual states for historical reference
- **Quality Assurance**: Visual regression testing for web applications

## Best Practices

1. **Use appropriate timeouts**: Set reasonable timeout values based on page complexity
2. **Wait for content**: Use `wait_for_selector` for dynamic content
3. **Responsive design**: Test with different device types for responsive layouts
4. **Authentication**: Use cookies/headers for authenticated content
5. **File size**: Consider JPEG format for large screenshots
6. **Async processing**: Use `sync=false` for complex pages or batch operations

## Rate Limiting

Subject to standard API rate limiting. Use async processing for bulk screenshot operations.