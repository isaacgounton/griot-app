# Advanced Usage

This guide covers advanced techniques and patterns for using the FFmpeg Compose API effectively in production environments.

## Complex Filter Graphs

### Multi-Step Processing

Chain multiple operations for complex transformations:

```json
{
  "id": "complex-processing",
  "inputs": [
    {"file_url": "https://example.com/raw-footage.mov"}
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1920", "1080"],
      "input_labels": ["0:v"],
      "output_label": "scaled"
    },
    {
      "filter": "eq",
      "arguments": ["brightness=0.1", "contrast=1.2", "saturation=1.1"],
      "input_labels": ["scaled"],
      "output_label": "color_corrected"
    },
    {
      "filter": "unsharp",
      "arguments": ["5", "5", "1.0", "5", "5", "0.0"],
      "input_labels": ["color_corrected"],
      "output_label": "sharpened"
    },
    {
      "filter": "drawtext",
      "arguments": [
        "fontfile=/app/static/fonts/Arial-Regular.ttf",
        "text='Processed Video'",
        "fontsize=48",
        "fontcolor=white",
        "x=(w-text_w)/2",
        "y=50"
      ],
      "input_labels": ["sharpened"],
      "output_label": "final_video"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 20},
        {"option": "-c:a", "argument": "copy"}
      ],
      "stream_mappings": ["[final_video]", "0:a"]
    }
  ]
}
```

### Multi-Input Complex Operations

Process multiple inputs with sophisticated routing:

```json
{
  "id": "multi-input-complex",
  "inputs": [
    {"file_url": "https://example.com/background.mp4"},
    {"file_url": "https://example.com/overlay1.mp4"},
    {"file_url": "https://example.com/overlay2.png"},
    {"file_url": "https://example.com/audio.wav"}
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["320", "240"],
      "input_labels": ["1:v"],
      "output_label": "overlay1_scaled"
    },
    {
      "filter": "scale",
      "arguments": ["200", "100"],
      "input_labels": ["2:v"],
      "output_label": "overlay2_scaled"
    },
    {
      "filter": "overlay",
      "arguments": ["10", "10"],
      "input_labels": ["0:v", "overlay1_scaled"],
      "output_label": "first_overlay"
    },
    {
      "filter": "overlay",
      "arguments": ["W-w-10", "H-h-10"],
      "input_labels": ["first_overlay", "overlay2_scaled"],
      "output_label": "final_video"
    },
    {
      "filter": "volume",
      "arguments": ["0.7"],
      "input_labels": ["0:a"],
      "output_label": "bg_audio"
    },
    {
      "filter": "volume",
      "arguments": ["0.8"],
      "input_labels": ["3:a"],
      "output_label": "main_audio"
    },
    {
      "filter": "amix",
      "arguments": ["inputs=2", "duration=longest"],
      "input_labels": ["bg_audio", "main_audio"],
      "output_label": "mixed_audio"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["[final_video]", "[mixed_audio]"]
    }
  ]
}
```

## Production Patterns

### Adaptive Bitrate Streaming

Generate multiple quality levels for streaming:

```json
{
  "id": "abr-ladder",
  "inputs": [
    {"file_url": "https://example.com/source.mp4"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-b:v", "argument": "4000k"},
        {"option": "-s", "argument": "1920x1080"},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "192k"}
      ]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-b:v", "argument": "2500k"},
        {"option": "-s", "argument": "1280x720"},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "128k"}
      ]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-b:v", "argument": "1200k"},
        {"option": "-s", "argument": "854x480"},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "96k"}
      ]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-b:v", "argument": "600k"},
        {"option": "-s", "argument": "640x360"},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "64k"}
      ]
    }
  ],
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true,
    "bitrate": true
  }
}
```

### Social Media Formats

Generate content for different platforms:

```json
{
  "id": "social-media-formats",
  "inputs": [
    {"file_url": "https://example.com/landscape-video.mp4"}
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1080", "1080"],
      "input_labels": ["0:v"],
      "output_label": "square"
    },
    {
      "filter": "scale",
      "arguments": ["1080", "1920"],
      "input_labels": ["0:v"],
      "output_label": "vertical"
    },
    {
      "filter": "crop",
      "arguments": ["1920", "1080", "(iw-1920)/2", "(ih-1080)/2"],
      "input_labels": ["0:v"],
      "output_label": "landscape_cropped"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["[square]", "0:a"]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["[vertical]", "0:a"]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["[landscape_cropped]", "0:a"]
    }
  ]
}
```

## Optimization Strategies

### Hardware Acceleration Pipeline

```json
{
  "id": "hardware-accelerated",
  "inputs": [
    {
      "file_url": "https://example.com/large-video.mov",
      "options": [
        {"option": "-hwaccel", "argument": "auto"}
      ]
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "h264_nvenc"},
        {"option": "-preset", "argument": "p4"},
        {"option": "-cq", "argument": "23"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ]
}
```

### Memory-Efficient Processing

For large files, optimize memory usage:

```json
{
  "id": "memory-efficient",
  "inputs": [
    {
      "file_url": "https://example.com/huge-video.mov",
      "options": [
        {"option": "-threads", "argument": "4"},
        {"option": "-fflags", "argument": "+genpts"}
      ]
    }
  ],
  "global_options": [
    {"option": "-max_muxing_queue_size", "argument": "1024"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-preset", "argument": "medium"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ]
}
```

## Error Handling and Resilience

### Retry Logic Implementation

```python
import requests
import time
from typing import Dict, Any

class FFmpegProcessor:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    def process_with_retry(self, config: Dict[Any, Any], max_retries: int = 3) -> Dict[Any, Any]:
        for attempt in range(max_retries):
            try:
                # Submit job
                response = requests.post(
                    f"{self.base_url}/v1/ffmpeg/compose",
                    headers=self.headers,
                    json=config,
                    timeout=30
                )
                response.raise_for_status()
                job_id = response.json()["job_id"]
                
                # Poll for completion
                return self._poll_job(job_id)
                
            except (requests.RequestException, KeyError) as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _poll_job(self, job_id: str, timeout: int = 3600) -> Dict[Any, Any]:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.base_url}/v1/ffmpeg/compose/{job_id}",
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                status = response.json()
                
                if status["status"] == "completed":
                    return status["result"]
                elif status["status"] == "failed":
                    raise Exception(f"Job failed: {status.get('error', 'Unknown error')}")
                
                time.sleep(5)
                
            except requests.RequestException:
                time.sleep(10)  # Wait longer on network errors
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
```

### Input Validation

```python
from typing import List, Dict, Any

def validate_ffmpeg_config(config: Dict[Any, Any]) -> List[str]:
    """Validate FFmpeg configuration and return list of errors."""
    errors = []
    
    # Required fields
    if not config.get("id"):
        errors.append("Missing required field: id")
    
    if not config.get("inputs"):
        errors.append("Missing required field: inputs")
    
    if not config.get("outputs"):
        errors.append("Missing required field: outputs")
    
    # Validate inputs
    for i, input_config in enumerate(config.get("inputs", [])):
        if not input_config.get("file_url"):
            errors.append(f"Input {i}: Missing file_url")
        
        # Validate URL format
        url = input_config.get("file_url", "")
        if not (url.startswith("http://") or url.startswith("https://") or url.startswith("/")):
            errors.append(f"Input {i}: Invalid file_url format")
    
    # Validate outputs
    for i, output_config in enumerate(config.get("outputs", [])):
        if not output_config.get("options"):
            errors.append(f"Output {i}: Missing options")
        
        # Check for essential codec options
        options = {opt["option"]: opt.get("argument") for opt in output_config.get("options", [])}
        if "-c:v" not in options and "-an" not in options:
            errors.append(f"Output {i}: Missing video codec (-c:v)")
        if "-c:a" not in options and "-vn" not in options:
            errors.append(f"Output {i}: Missing audio codec (-c:a)")
    
    return errors
```

## Performance Monitoring

### Processing Time Estimation

```python
def estimate_processing_time(config: Dict[Any, Any]) -> float:
    """Estimate processing time based on configuration complexity."""
    base_time = 30.0  # Base processing time
    
    # Factor in number of inputs and outputs
    inputs_factor = len(config.get("inputs", []))
    outputs_factor = len(config.get("outputs", []))
    
    # Factor in filter complexity
    filters_factor = 1.0
    if config.get("filters"):
        filters_factor = 1.5 + (len(config["filters"]) * 0.1)
    
    # Check for hardware acceleration
    hw_accel_factor = 1.0
    for output in config.get("outputs", []):
        for option in output.get("options", []):
            if option.get("option") == "-c:v":
                codec = option.get("argument", "")
                if "nvenc" in codec or "qsv" in codec or "amf" in codec:
                    hw_accel_factor = 0.3
                    break
    
    estimated_time = (
        base_time * 
        inputs_factor * 
        outputs_factor * 
        filters_factor * 
        hw_accel_factor
    )
    
    return estimated_time
```

### Resource Usage Monitoring

```python
import psutil
import threading
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class ResourceUsage:
    cpu_percent: float
    memory_percent: float
    disk_io: Dict[str, int]

class ResourceMonitor:
    def __init__(self):
        self.monitoring = False
        self.usage_history = []
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self, interval: float = 1.0):
        """Start monitoring system resources."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> List[ResourceUsage]:
        """Stop monitoring and return usage history."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        return self.usage_history
    
    def _monitor_loop(self, interval: float):
        """Monitor resources in a loop."""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_percent = psutil.virtual_memory().percent
                disk_io = psutil.disk_io_counters()._asdict()
                
                usage = ResourceUsage(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    disk_io=disk_io
                )
                self.usage_history.append(usage)
                
            except Exception:
                pass  # Ignore monitoring errors
            
            time.sleep(interval)
```

## Webhook Integration

### Webhook Notification Setup

```json
{
  "id": "webhook-example",
  "inputs": [
    {"file_url": "https://example.com/input.mp4"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ],
  "webhook_url": "https://your-api.com/webhooks/ffmpeg-complete"
}
```

### Webhook Handler Example

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhooks/ffmpeg-complete', methods=['POST'])
def handle_ffmpeg_webhook():
    try:
        payload = request.get_json()
        
        # Verify webhook signature (if implemented)
        # signature = request.headers.get('X-Signature')
        # if not verify_signature(request.data, signature):
        #     return jsonify({'error': 'Invalid signature'}), 401
        
        job_id = payload.get('job_id')
        status = payload.get('status')
        result = payload.get('result')
        
        if status == 'completed':
            # Process successful completion
            outputs = result.get('outputs', [])
            for i, output in enumerate(outputs):
                file_url = output.get('file_url')
                thumbnail_url = output.get('thumbnail_url')
                
                # Update your database, notify users, etc.
                print(f"Job {job_id} completed: {file_url}")
                
        elif status == 'failed':
            # Handle failure
            error = payload.get('error', 'Unknown error')
            print(f"Job {job_id} failed: {error}")
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': 'Processing failed'}), 500

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature for security."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Batch Processing

### Queue Management

```python
import asyncio
import aiohttp
from typing import List, Dict, Any

class BatchProcessor:
    def __init__(self, api_key: str, base_url: str, max_concurrent: int = 5):
        self.api_key = api_key
        self.base_url = base_url
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(self, configs: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        """Process multiple configurations concurrently."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._process_single(session, config)
                for config in configs
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
    
    async def _process_single(self, session: aiohttp.ClientSession, config: Dict[Any, Any]) -> Dict[Any, Any]:
        """Process a single configuration."""
        async with self.semaphore:
            try:
                # Submit job
                async with session.post(
                    f"{self.base_url}/v1/ffmpeg/compose",
                    json=config,
                    headers={"X-API-Key": self.api_key}
                ) as response:
                    response.raise_for_status()
                    job_data = await response.json()
                    job_id = job_data["job_id"]
                
                # Poll for completion
                return await self._poll_job_async(session, job_id)
                
            except Exception as e:
                return {"error": str(e), "config_id": config.get("id")}
    
    async def _poll_job_async(self, session: aiohttp.ClientSession, job_id: str) -> Dict[Any, Any]:
        """Poll job status asynchronously."""
        while True:
            try:
                async with session.get(
                    f"{self.base_url}/v1/ffmpeg/compose/{job_id}",
                    headers={"X-API-Key": self.api_key}
                ) as response:
                    response.raise_for_status()
                    status = await response.json()
                    
                    if status["status"] == "completed":
                        return status["result"]
                    elif status["status"] == "failed":
                        raise Exception(f"Job failed: {status.get('error')}")
                    
                    await asyncio.sleep(5)
                    
            except Exception as e:
                raise Exception(f"Polling failed: {e}")
```

## Best Practices Summary

### Configuration Best Practices

1. **Use Descriptive IDs**: Include timestamps or unique identifiers
2. **Validate Inputs**: Check URLs and file accessibility before submission
3. **Optimize Stream Mappings**: Use explicit mappings for predictable results
4. **Enable Selective Metadata**: Only request needed metadata to improve performance
5. **Use Hardware Acceleration**: When available, for faster processing

### Error Handling Best Practices

1. **Implement Retry Logic**: With exponential backoff
2. **Validate Configurations**: Before submission
3. **Monitor Resource Usage**: Track system performance
4. **Use Webhooks**: For long-running jobs
5. **Handle Timeouts**: Set appropriate timeout values

### Security Best Practices

1. **Secure API Keys**: Use environment variables, never hard-code
2. **Validate Webhook Signatures**: Verify webhook authenticity
3. **Sanitize URLs**: Validate input URLs to prevent SSRF attacks
4. **Rate Limiting**: Implement client-side rate limiting
5. **Monitor Usage**: Track API usage and costs

---

*Previous: [Metadata Extraction](./metadata.md) | Next: [Error Handling](./error-handling.md)*
