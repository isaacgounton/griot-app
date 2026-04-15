# Error Handling

This guide covers error handling, troubleshooting, and debugging when using the FFmpeg Compose API.

## Error Types

### HTTP Status Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| 400 | Bad Request | Invalid JSON, missing required fields |
| 401 | Unauthorized | Invalid or missing API key |
| 404 | Not Found | Job ID not found |
| 422 | Validation Error | Invalid parameter values, unsupported codecs |
| 429 | Rate Limited | Too many requests |
| 500 | Internal Server Error | Processing failure, system error |

### Job Status Errors

Jobs can fail during processing with specific error messages:

```json
{
  "job_id": "abc123-def456",
  "status": "failed",
  "error": "FFmpeg command failed: Invalid codec parameters"
}
```

## Common Error Scenarios

### 1. Invalid Input URLs

**Error:**
```json
{
  "status": "failed",
  "error": "Failed to download input file: HTTP 404 Not Found"
}
```

**Solutions:**
- Verify URL accessibility
- Check file permissions
- Ensure stable network connection
- Use direct file URLs (not redirects)

**Prevention:**
```python
import requests

def validate_url(url: str) -> bool:
    """Validate URL accessibility before submission."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Usage
if not validate_url("https://example.com/video.mp4"):
    raise ValueError("Input URL is not accessible")
```

### 2. Codec Configuration Errors

**Error:**
```json
{
  "status": "failed",
  "error": "Unknown encoder 'libx265'"
}
```

**Solutions:**
- Use supported codecs (libx264, libx265, aac, mp3)
- Check codec spelling
- Verify codec availability on the system

**Prevention:**
```json
{
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},  // Use widely supported codec
        {"option": "-c:a", "argument": "aac"}       // Use widely supported codec
      ]
    }
  ]
}
```

### 3. Filter Graph Errors

**Error:**
```json
{
  "status": "failed",
  "error": "Cannot find a matching stream for unlabeled input pad 1 on filter overlay"
}
```

**Solutions:**
- Check input/output label connections
- Verify filter arguments
- Ensure proper stream routing

**Debugging:**
```json
{
  "filters": [
    {
      "filter": "scale",
      "arguments": ["320", "240"],
      "input_labels": ["1:v"],        // Must match available input
      "output_label": "overlay_scaled" // Must be unique
    },
    {
      "filter": "overlay",
      "arguments": ["10", "10"],
      "input_labels": ["0:v", "overlay_scaled"], // Must reference existing labels
      "output_label": "final_video"
    }
  ]
}
```

### 4. Memory and Resource Limits

**Error:**
```json
{
  "status": "failed",
  "error": "Processing timeout: Operation exceeded maximum allowed time"
}
```

**Solutions:**
- Reduce input file size
- Use lower quality settings
- Enable hardware acceleration
- Split large jobs into smaller chunks

**Optimization:**
```json
{
  "inputs": [
    {
      "file_url": "https://example.com/large-video.mp4",
      "options": [
        {"option": "-ss", "argument": "0"},      // Start from beginning
        {"option": "-t", "argument": "300"}      // Process only 5 minutes
      ]
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-preset", "argument": "ultrafast"}, // Faster processing
        {"option": "-crf", "argument": 28}              // Lower quality for speed
      ]
    }
  ]
}
```

### 5. Stream Mapping Errors

**Error:**
```json
{
  "status": "failed",
  "error": "Stream specifier '0:v:1' does not match any streams"
}
```

**Solutions:**
- Check available streams in input files
- Use correct stream indices
- Handle missing streams gracefully

**Debug Approach:**
```json
{
  "metadata": {
    "encoder": true  // This will show available streams
  }
}
```

## Error Handling Patterns

### 1. Retry with Exponential Backoff

```python
import time
import requests
from typing import Dict, Any

def submit_job_with_retry(config: Dict[Any, Any], api_key: str, max_retries: int = 3) -> str:
    """Submit job with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/v1/ffmpeg/compose",
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json=config,
                timeout=30
            )
            
            if response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt
                print(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response.json()["job_id"]
            
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise Exception(f"Failed to submit job after {max_retries} attempts: {e}")
            
            wait_time = 2 ** attempt
            print(f"Attempt {attempt + 1} failed, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
```

### 2. Graceful Degradation

```python
def create_fallback_config(original_config: Dict[Any, Any]) -> Dict[Any, Any]:
    """Create a simpler configuration as fallback."""
    fallback = {
        "id": f"{original_config['id']}_fallback",
        "inputs": original_config["inputs"],
        "outputs": [
            {
                "options": [
                    {"option": "-c:v", "argument": "libx264"},
                    {"option": "-preset", "argument": "ultrafast"},
                    {"option": "-crf", "argument": 28},
                    {"option": "-c:a", "argument": "aac"}
                ]
            }
        ]
    }
    return fallback

def process_with_fallback(config: Dict[Any, Any], api_key: str) -> Dict[Any, Any]:
    """Process with fallback configuration on failure."""
    try:
        return process_job(config, api_key)
    except Exception as primary_error:
        print(f"Primary configuration failed: {primary_error}")
        print("Attempting fallback configuration...")
        
        try:
            fallback_config = create_fallback_config(config)
            return process_job(fallback_config, api_key)
        except Exception as fallback_error:
            raise Exception(f"Both primary and fallback failed. Primary: {primary_error}, Fallback: {fallback_error}")
```

### 3. Input Validation

```python
from urllib.parse import urlparse
from typing import List, Dict, Any

class ConfigValidator:
    SUPPORTED_VIDEO_CODECS = ["libx264", "libx265", "libvpx-vp9", "copy"]
    SUPPORTED_AUDIO_CODECS = ["aac", "mp3", "libopus", "copy"]
    
    @staticmethod
    def validate_config(config: Dict[Any, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate basic structure
        errors.extend(ConfigValidator._validate_structure(config))
        
        # Validate inputs
        errors.extend(ConfigValidator._validate_inputs(config.get("inputs", [])))
        
        # Validate outputs
        errors.extend(ConfigValidator._validate_outputs(config.get("outputs", [])))
        
        # Validate filters
        errors.extend(ConfigValidator._validate_filters(config.get("filters", [])))
        
        return errors
    
    @staticmethod
    def _validate_structure(config: Dict[Any, Any]) -> List[str]:
        """Validate basic configuration structure."""
        errors = []
        
        required_fields = ["id", "inputs", "outputs"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        if not isinstance(config.get("inputs"), list) or len(config.get("inputs", [])) == 0:
            errors.append("At least one input is required")
        
        if not isinstance(config.get("outputs"), list) or len(config.get("outputs", [])) == 0:
            errors.append("At least one output is required")
        
        return errors
    
    @staticmethod
    def _validate_inputs(inputs: List[Dict[Any, Any]]) -> List[str]:
        """Validate input configurations."""
        errors = []
        
        for i, input_config in enumerate(inputs):
            if "file_url" not in input_config:
                errors.append(f"Input {i}: Missing file_url")
                continue
            
            url = input_config["file_url"]
            parsed = urlparse(url)
            
            if not parsed.scheme and not url.startswith("/"):
                errors.append(f"Input {i}: Invalid URL format")
            
            if parsed.scheme and parsed.scheme not in ["http", "https"]:
                errors.append(f"Input {i}: Unsupported URL scheme: {parsed.scheme}")
        
        return errors
    
    @staticmethod
    def _validate_outputs(outputs: List[Dict[Any, Any]]) -> List[str]:
        """Validate output configurations."""
        errors = []
        
        for i, output in enumerate(outputs):
            if "options" not in output:
                errors.append(f"Output {i}: Missing options")
                continue
            
            options = {opt["option"]: opt.get("argument") for opt in output["options"]}
            
            # Check video codec
            video_codec = options.get("-c:v")
            if video_codec and video_codec not in ConfigValidator.SUPPORTED_VIDEO_CODECS:
                errors.append(f"Output {i}: Unsupported video codec: {video_codec}")
            
            # Check audio codec
            audio_codec = options.get("-c:a")
            if audio_codec and audio_codec not in ConfigValidator.SUPPORTED_AUDIO_CODECS:
                errors.append(f"Output {i}: Unsupported audio codec: {audio_codec}")
            
            # Check for essential codecs
            if not video_codec and "-an" not in options:
                errors.append(f"Output {i}: Missing video codec or -an flag")
            
            if not audio_codec and "-vn" not in options:
                errors.append(f"Output {i}: Missing audio codec or -vn flag")
        
        return errors
    
    @staticmethod
    def _validate_filters(filters: List[Dict[Any, Any]]) -> List[str]:
        """Validate filter configurations."""
        errors = []
        
        output_labels = set()
        
        for i, filter_config in enumerate(filters):
            if "filter" not in filter_config:
                errors.append(f"Filter {i}: Missing filter name")
                continue
            
            # Check for duplicate output labels
            output_label = filter_config.get("output_label")
            if output_label:
                if output_label in output_labels:
                    errors.append(f"Filter {i}: Duplicate output label: {output_label}")
                output_labels.add(output_label)
        
        return errors

# Usage
validator = ConfigValidator()
errors = validator.validate_config(config)
if errors:
    for error in errors:
        print(f"Validation error: {error}")
    raise ValueError("Configuration validation failed")
```

## Debugging Strategies

### 1. Enable Detailed Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def debug_process_job(config: Dict[Any, Any], api_key: str) -> Dict[Any, Any]:
    """Process job with detailed logging."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting job: {config.get('id')}")
    logger.debug(f"Configuration: {config}")
    
    try:
        # Submit job
        response = requests.post(
            "http://localhost:8000/v1/ffmpeg/compose",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json=config
        )
        
        logger.debug(f"Submit response status: {response.status_code}")
        logger.debug(f"Submit response: {response.text}")
        
        response.raise_for_status()
        job_id = response.json()["job_id"]
        logger.info(f"Job submitted successfully: {job_id}")
        
        # Poll for completion
        while True:
            status_response = requests.get(
                f"http://localhost:8000/v1/ffmpeg/compose/{job_id}",
                headers={"X-API-Key": api_key}
            )
            
            status = status_response.json()
            logger.debug(f"Job status: {status}")
            
            if status["status"] == "completed":
                logger.info(f"Job completed successfully: {job_id}")
                return status["result"]
            elif status["status"] == "failed":
                logger.error(f"Job failed: {status.get('error')}")
                raise Exception(f"Job failed: {status.get('error')}")
            
            time.sleep(5)
            
    except Exception as e:
        logger.error(f"Job processing failed: {e}")
        raise
```

### 2. Test with Minimal Configuration

```python
def test_minimal_config(api_key: str) -> bool:
    """Test with minimal configuration to isolate issues."""
    minimal_config = {
        "id": "test-minimal",
        "inputs": [
            {"file_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"}
        ],
        "outputs": [
            {
                "options": [
                    {"option": "-c:v", "argument": "copy"},
                    {"option": "-c:a", "argument": "copy"}
                ]
            }
        ]
    }
    
    try:
        result = process_job(minimal_config, api_key)
        print("Minimal configuration test passed")
        return True
    except Exception as e:
        print(f"Minimal configuration test failed: {e}")
        return False
```

### 3. Progressive Configuration Building

```python
def test_progressive_config(api_key: str):
    """Build configuration progressively to identify issues."""
    
    # Test 1: Basic copy
    config1 = {
        "id": "test-basic-copy",
        "inputs": [{"file_url": "https://example.com/test.mp4"}],
        "outputs": [{"options": [{"option": "-c", "argument": "copy"}]}]
    }
    print("Testing basic copy...")
    process_job(config1, api_key)
    print("✓ Basic copy successful")
    
    # Test 2: Add encoding
    config2 = {
        "id": "test-encoding",
        "inputs": [{"file_url": "https://example.com/test.mp4"}],
        "outputs": [{
            "options": [
                {"option": "-c:v", "argument": "libx264"},
                {"option": "-c:a", "argument": "aac"}
            ]
        }]
    }
    print("Testing encoding...")
    process_job(config2, api_key)
    print("✓ Encoding successful")
    
    # Test 3: Add simple filter
    config3 = {
        "id": "test-simple-filter",
        "inputs": [{"file_url": "https://example.com/test.mp4"}],
        "filters": [{"filter": "scale", "arguments": ["640", "480"], "type": "video"}],
        "use_simple_video_filter": True,
        "outputs": [{
            "options": [
                {"option": "-c:v", "argument": "libx264"},
                {"option": "-c:a", "argument": "aac"}
            ]
        }]
    }
    print("Testing simple filter...")
    process_job(config3, api_key)
    print("✓ Simple filter successful")
```

## Production Error Monitoring

### 1. Error Aggregation

```python
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

class ErrorTracker:
    def __init__(self):
        self.errors = defaultdict(list)
    
    def record_error(self, error_type: str, error_message: str, config_id: str = None):
        """Record an error with timestamp and context."""
        self.errors[error_type].append({
            "message": error_message,
            "timestamp": datetime.now(),
            "config_id": config_id
        })
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of error counts by type."""
        return {error_type: len(errors) for error_type, errors in self.errors.items()}
    
    def get_frequent_errors(self, top_n: int = 5) -> List[tuple]:
        """Get most frequent error types."""
        error_counts = self.get_error_summary()
        return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

# Global error tracker
error_tracker = ErrorTracker()

def process_with_tracking(config: Dict[Any, Any], api_key: str) -> Dict[Any, Any]:
    """Process job with error tracking."""
    try:
        return process_job(config, api_key)
    except Exception as e:
        error_type = type(e).__name__
        error_tracker.record_error(error_type, str(e), config.get("id"))
        raise
```

### 2. Health Checks

```python
import requests
from datetime import datetime, timedelta

class HealthChecker:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check API health with simple request."""
        try:
            response = requests.get(
                f"{self.base_url}/docs",
                timeout=10
            )
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    def check_processing_health(self) -> Dict[str, Any]:
        """Check processing capability with test job."""
        test_config = {
            "id": f"health-check-{int(datetime.now().timestamp())}",
            "inputs": [{"file_url": "https://sample-videos.com/zip/10/mp4/SampleVideo_360x240_1mb.mp4"}],
            "outputs": [{"options": [{"option": "-c", "argument": "copy"}]}]
        }
        
        try:
            start_time = datetime.now()
            result = process_job(test_config, self.api_key)
            end_time = datetime.now()
            
            return {
                "status": "healthy",
                "processing_time": (end_time - start_time).total_seconds(),
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }
```

## Best Practices

### 1. Error Prevention

- **Validate inputs** before submission
- **Use supported codecs** and formats
- **Test configurations** with small files first
- **Monitor resource usage** to prevent timeouts
- **Implement rate limiting** to avoid 429 errors

### 2. Error Handling

- **Use exponential backoff** for retries
- **Implement fallback configurations** for critical paths
- **Log detailed error information** for debugging
- **Monitor error patterns** to identify systemic issues
- **Set appropriate timeouts** for your use case

### 3. Recovery Strategies

- **Graceful degradation** to simpler configurations
- **Automatic retry** with different parameters
- **User notification** for unrecoverable errors
- **Manual intervention** triggers for complex failures
- **Rollback capabilities** for batch operations

---

*Previous: [Advanced Usage](./advanced.md) | [Back to Index](./README.md)*