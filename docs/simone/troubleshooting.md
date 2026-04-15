# Simone Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Simone's video-to-content conversion functionality.

## Common Issues

### Installation and Setup Issues

#### 1. Tesseract OCR Not Found

**Error:**
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```

**Solutions:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng

# Verify installation
tesseract --version
which tesseract
```

**macOS:**
```bash
brew install tesseract

# Verify installation
tesseract --version
which tesseract
```

**Windows:**
1. Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install to default location (usually `C:\Program Files\Tesseract-OCR\`)
3. Add to PATH or set environment variable:
```bash
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

**Set Custom Path:**
```bash
export TESSERACT_PATH=/your/custom/path/to/tesseract
```

#### 2. OpenCV Installation Issues

**Error:**
```
ImportError: No module named 'cv2'
```

**Solutions:**
```bash
# Install OpenCV
pip install opencv-python

# For additional functionality
pip install opencv-contrib-python

# Verify installation
python -c "import cv2; print(cv2.__version__)"
```

**macOS ARM64 Issues:**
```bash
# Use conda for better ARM64 support
conda install opencv

# Or use specific build
pip install opencv-python-headless
```

#### 3. Whisper Model Download Issues

**Error:**
```
RuntimeError: Failed to download model
ConnectionError: Failed to establish a new connection
```

**Solutions:**

**Manual Model Download:**
```python
import whisper

# Download models manually
models = ['tiny', 'base', 'small']
for model_name in models:
    print(f"Downloading {model_name}...")
    model = whisper.load_model(model_name)
    print(f"✓ {model_name} downloaded successfully")
```

**Offline Environment:**
```bash
# Download models on connected machine
python -c "import whisper; whisper.load_model('base')"

# Copy model files to offline machine
# Models are stored in ~/.cache/whisper/
```

**Network Issues:**
```bash
# Use proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Or disable SSL verification (not recommended for production)
export CURL_CA_BUNDLE=""
```

### Processing Issues

#### 4. Video Download Failures

**Error:**
```
yt_dlp.utils.DownloadError: Unable to download video
```

**Common Causes and Solutions:**

**Private/Restricted Videos:**
```python
# Use cookies for authentication
request_data = {
    "url": "https://youtube.com/watch?v=private-video",
    "cookies_content": "session_token=abc123; user_id=456789",
    "cookies_url": "https://youtube.com"
}
```

**Geographic Restrictions:**
```bash
# Video might be geo-blocked
# Solution: Use VPN or different video source
```

**Age-Restricted Content:**
```python
# Some videos require age verification
# Solution: Provide appropriate cookies or use different video
```

**Rate Limiting:**
```bash
# Too many requests to platform
# Solution: Implement delays between requests
```

**Debugging Video Download:**
```python
import yt_dlp

def debug_video_download(url):
    ydl_opts = {
        'verbose': True,
        'extract_flat': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Duration: {info.get('duration', 'Unknown')} seconds")
            print(f"Available formats: {len(info.get('formats', []))}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

# Test video URL
debug_video_download("https://youtube.com/watch?v=your-video")
```

#### 5. Transcription Issues

**Error:**
```
RuntimeError: CUDA out of memory
whisper.transcribe() failed
```

**Solutions:**

**Memory Issues:**
```python
# Use smaller Whisper model
import whisper
model = whisper.load_model("tiny")  # Instead of "large"

# Or process in chunks
def transcribe_in_chunks(audio_path, chunk_duration=300):
    # Split audio into 5-minute chunks
    # Process each chunk separately
    pass
```

**CPU-Only Processing:**
```python
import torch
import whisper

# Force CPU usage
device = "cpu"
model = whisper.load_model("base", device=device)
```

**Audio Quality Issues:**
```bash
# Poor audio quality leading to bad transcription
# Solution: Pre-process audio

ffmpeg -i input.mp4 -af "highpass=f=200,lowpass=f=3000" -ac 1 -ar 16000 cleaned_audio.wav
```

#### 6. OCR/Frame Analysis Issues

**Error:**
```
pytesseract.pytesseract.TesseractError: (1, 'Error opening data file')
```

**Solutions:**

**Language Data Missing:**
```bash
# Install additional language packs
sudo apt install tesseract-ocr-eng tesseract-ocr-spa  # Add more as needed

# Verify available languages
tesseract --list-langs
```

**Image Quality Issues:**
```python
import cv2
import numpy as np

def preprocess_image_for_ocr(image):
    """Improve image quality for better OCR results."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply noise reduction
    denoised = cv2.medianBlur(gray, 3)
    
    # Increase contrast
    alpha = 1.5  # Contrast control
    beta = 0     # Brightness control
    enhanced = cv2.convertScaleAbs(denoised, alpha=alpha, beta=beta)
    
    # Apply threshold
    _, threshold = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return threshold
```

**Custom Tesseract Configuration:**
```python
import pytesseract

# Custom OCR configuration for better results
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '

text = pytesseract.image_to_string(image, config=custom_config)
```

### API and Storage Issues

#### 7. OpenAI API Issues

**Error:**
```
openai.error.RateLimitError: Rate limit exceeded
openai.error.AuthenticationError: Invalid API key
```

**Solutions:**

**Rate Limiting:**
```python
import time
import random
from openai import RateLimitError

def call_openai_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response
        except RateLimitError:
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
            else:
                raise
```

**Authentication Issues:**
```bash
# Verify API key format
echo $OPENAI_API_KEY | head -c 10  # Should show "sk-" prefix

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Token Limit Issues:**
```python
def chunk_text_for_api(text, max_tokens=3000):
    """Split large text into chunks that fit within token limits."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        # Rough estimate: 1 token ≈ 0.75 words
        word_tokens = len(word) * 0.75
        
        if current_length + word_tokens > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_tokens
        else:
            current_chunk.append(word)
            current_length += word_tokens
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks
```

#### 8. S3 Storage Issues

**Error:**
```
ClientError: The AWS Access Key Id you provided does not exist
NoCredentialsError: Unable to locate credentials
```

**Solutions:**

**Credential Issues:**
```bash
# Verify S3 credentials
aws configure list

# Test S3 access
aws s3 ls s3://your-bucket-name
```

**Permission Issues:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket/*"
        }
    ]
}
```

**Network Issues:**
```python
import boto3
from botocore.exceptions import ClientError

def test_s3_connection():
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        print("✓ S3 connection successful")
        return True
    except ClientError as e:
        print(f"✗ S3 connection failed: {e}")
        return False
```

### Performance Issues

#### 9. Slow Processing

**Symptoms:**
- Jobs taking extremely long to complete
- High CPU/memory usage
- System becoming unresponsive

**Solutions:**

**Resource Optimization:**
```python
# Monitor system resources
import psutil

def check_system_health():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print(f"CPU: {cpu_percent}%")
    print(f"Memory: {memory.percent}% ({memory.available / 1024**3:.1f} GB available)")
    print(f"Disk: {disk.percent}% ({disk.free / 1024**3:.1f} GB free)")
    
    if cpu_percent > 90:
        print("⚠️ High CPU usage")
    if memory.percent > 85:
        print("⚠️ High memory usage")
    if disk.percent > 90:
        print("⚠️ Low disk space")
```

**Processing Optimization:**
```python
# Optimize Whisper model selection
def select_optimal_whisper_model(video_duration_seconds):
    if video_duration_seconds < 300:  # 5 minutes
        return "tiny"
    elif video_duration_seconds < 900:  # 15 minutes
        return "base"
    elif video_duration_seconds < 1800:  # 30 minutes
        return "small"
    else:
        return "base"  # For very long videos, use base for speed

# Optimize frame sampling
def optimize_frame_sampling(video_duration_seconds):
    if video_duration_seconds < 300:
        return 2  # Sample 2 frames per second
    elif video_duration_seconds < 900:
        return 1  # Sample 1 frame per second
    else:
        return 0.5  # Sample 0.5 frames per second
```

#### 10. Memory Leaks

**Symptoms:**
- Memory usage increasing over time
- Eventually running out of memory
- System slowdown

**Solutions:**

**Resource Cleanup:**
```python
import gc
import tempfile
import shutil

def cleanup_resources():
    """Clean up resources after processing."""
    # Force garbage collection
    gc.collect()
    
    # Clean up temporary files
    temp_dirs = ['/tmp', tempfile.gettempdir()]
    for temp_dir in temp_dirs:
        for item in os.listdir(temp_dir):
            if item.startswith('simone_'):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as e:
                    print(f"Failed to clean up {item_path}: {e}")
```

**Memory-Efficient Processing:**
```python
def process_large_video_efficiently(video_path):
    """Process large videos with memory management."""
    try:
        # Process in chunks to manage memory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use context managers for automatic cleanup
            result = process_video_chunks(video_path, temp_dir)
            return result
    finally:
        # Explicit cleanup
        cleanup_resources()
```

### Job Queue Issues

#### 11. Jobs Stuck in Processing

**Symptoms:**
- Jobs remain in "processing" status indefinitely
- No error messages
- Worker processes not responding

**Solutions:**

**Check Worker Status:**
```bash
# Check if worker processes are running
ps aux | grep simone

# Check Redis connection
redis-cli ping

# Check job queue status
python -c "
from app.services.redis_service import redis_service
import asyncio

async def check_queue():
    await redis_service.connect()
    # Check for stuck jobs
    jobs = await redis_service.get_all_jobs()
    processing_jobs = [j for j in jobs if j.status == 'processing']
    print(f'Processing jobs: {len(processing_jobs)}')

asyncio.run(check_queue())
"
```

**Job Recovery:**
```python
async def recover_stuck_jobs():
    """Recover jobs that have been processing too long."""
    import time
    from app.services.job_queue import job_queue
    
    cutoff_time = time.time() - 3600  # 1 hour ago
    
    for job_id, job_info in job_queue.jobs.items():
        if (job_info.status == "processing" and 
            job_info.started_at < cutoff_time):
            
            print(f"Recovering stuck job: {job_id}")
            await job_queue.update_job_status(
                job_id, 
                "failed", 
                error="Job timed out and was recovered"
            )
```

#### 12. High Job Failure Rate

**Symptoms:**
- Many jobs failing with various errors
- Inconsistent results
- System instability

**Solutions:**

**Error Analysis:**
```python
def analyze_job_failures():
    """Analyze patterns in job failures."""
    from app.services.redis_service import redis_service
    
    failed_jobs = redis_service.get_failed_jobs()
    
    error_patterns = {}
    for job in failed_jobs:
        error = job.get('error', 'Unknown error')
        error_type = error.split(':')[0] if ':' in error else error
        error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
    
    print("Most common errors:")
    for error_type, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  {error_type}: {count}")
```

**Robust Error Handling:**
```python
async def robust_job_processing(job_id, job_data):
    """Process job with comprehensive error handling."""
    try:
        # Pre-flight checks
        await validate_job_requirements(job_data)
        
        # Process with timeout
        result = await asyncio.wait_for(
            process_job(job_data), 
            timeout=1800  # 30 minutes
        )
        
        return result
        
    except asyncio.TimeoutError:
        raise JobTimeoutError("Job processing timed out")
    except ValidationError as e:
        raise JobValidationError(f"Invalid job data: {e}")
    except Exception as e:
        # Log detailed error for debugging
        logger.exception(f"Unexpected error in job {job_id}")
        raise JobProcessingError(f"Processing failed: {e}")
```

## Debugging Tools

### Log Analysis

**Enable Detailed Logging:**
```python
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simone_debug.log'),
        logging.StreamHandler()
    ]
)

# Enable specific module logging
logging.getLogger('app.services.simone_service').setLevel(logging.DEBUG)
logging.getLogger('app.utils.simone').setLevel(logging.DEBUG)
```

**Log Analysis Script:**
```bash
#!/bin/bash
# analyze_logs.sh

echo "Recent errors:"
grep -i error simone_debug.log | tail -10

echo -e "\nMost common errors:"
grep -i error simone_debug.log | awk -F': ' '{print $NF}' | sort | uniq -c | sort -nr | head -5

echo -e "\nProcessing times:"
grep "processing completed" simone_debug.log | awk '{print $NF}' | sort -n
```

### Health Check Script

```python
#!/usr/bin/env python3
"""
Simone Health Check Script
Run this to verify Simone installation and configuration.
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path

async def health_check():
    print("🔍 Simone Health Check")
    print("=" * 50)
    
    checks = []
    
    # Check Python dependencies
    try:
        import whisper
        import cv2
        import pytesseract
        import yt_dlp
        checks.append(("Python dependencies", True, "All required packages installed"))
    except ImportError as e:
        checks.append(("Python dependencies", False, f"Missing package: {e}"))
    
    # Check Tesseract
    try:
        pytesseract.get_tesseract_version()
        checks.append(("Tesseract OCR", True, "Tesseract accessible"))
    except Exception as e:
        checks.append(("Tesseract OCR", False, f"Tesseract error: {e}"))
    
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("sk-"):
        checks.append(("OpenAI API Key", True, "API key format valid"))
    else:
        checks.append(("OpenAI API Key", False, "Invalid or missing API key"))
    
    # Check S3 configuration (consistent with other services)
    s3_vars = ["S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET_NAME", "S3_REGION"]
    missing_vars = [var for var in s3_vars if not os.getenv(var)]
    
    # Check for dummy credentials
    using_dummy_credentials = (
        os.getenv("S3_ACCESS_KEY") == "dummy_access_key_id" or 
        os.getenv("S3_SECRET_KEY") == "dummy_secret_access_key" or 
        os.getenv("S3_BUCKET_NAME") == "dummy-bucket-name"
    )
    
    if not missing_vars and not using_dummy_credentials:
        checks.append(("S3 Configuration", True, "S3 properly configured"))
    elif using_dummy_credentials:
        checks.append(("S3 Configuration", True, "Using dummy credentials (mock S3 URLs)"))
    else:
        checks.append(("S3 Configuration", False, f"Missing: {missing_vars}"))
    
    # Check disk space
    temp_dir = Path(tempfile.gettempdir())
    stat = temp_dir.stat()
    free_gb = (stat.st_size if hasattr(stat, 'st_size') else 0) / (1024**3)
    if free_gb > 5:
        checks.append(("Disk Space", True, f"Sufficient space available"))
    else:
        checks.append(("Disk Space", False, f"Low disk space: {free_gb:.1f}GB"))
    
    # Display results
    for check_name, status, message in checks:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}: {message}")
    
    # Overall status
    failed_checks = [c for c in checks if not c[1]]
    if not failed_checks:
        print("\n🎉 All checks passed! Simone is ready to use.")
        return True
    else:
        print(f"\n⚠️ {len(failed_checks)} check(s) failed. Please resolve the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(health_check())
    sys.exit(0 if success else 1)
```

## Getting Help

### Support Resources

1. **Documentation**: Review all documentation files in `/docs/simone/`
2. **Logs**: Check application logs for detailed error information
3. **Health Check**: Run the health check script above
4. **API Testing**: Use the examples in `examples.md` to test functionality

### Reporting Issues

When reporting issues, please include:

1. **Environment Information:**
   - Operating system and version
   - Python version
   - Package versions (`pip list`)

2. **Configuration:**
   - Environment variables (redacted for sensitive data)
   - System resources (CPU, memory, disk)

3. **Error Details:**
   - Complete error messages
   - Relevant log entries
   - Steps to reproduce

4. **Context:**
   - Video URL or type causing issues
   - Expected vs. actual behavior
   - Any recent changes to configuration

### Emergency Recovery

**If Simone is completely non-functional:**

1. **Stop all processing:**
```bash
# Kill stuck processes
pkill -f simone
```

2. **Clear job queue:**
```python
from app.services.redis_service import redis_service
await redis_service.clear_all_jobs()
```

3. **Clean up resources:**
```bash
# Remove temporary files
rm -rf /tmp/simone_*
rm -rf public/simone_outputs/processing_*
```

4. **Restart services:**
```bash
# Restart the application
docker-compose restart api
# or
systemctl restart your-app-service
```

5. **Verify health:**
```bash
python health_check.py
```

This troubleshooting guide should help you resolve most issues with Simone. For persistent problems, consider reviewing the configuration and ensuring all dependencies are properly installed and configured.