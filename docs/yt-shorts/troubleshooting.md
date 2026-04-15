# YouTube Shorts Troubleshooting Guide

## Common Issues and Solutions

### 0. YouTube Download Failures (Coolify/Server Environments) 🔥

**Problem:** "Unable to download video" or "Video unavailable" errors when running on Coolify or other server environments.

**Symptoms:**
- Videos download fine locally but fail on server
- "Sign in to confirm your age" errors  
- "This video is not available" messages
- HTTP 403 or similar errors

**Root Cause:** YouTube restricts access for server/headless environments and requires browser cookies for many videos.

**Solutions:**

#### Option 1: Use Cookie File (Recommended) ⭐
Export cookies from your browser and host them for the API to use:

1. **Export cookies from your browser:**
   - Install browser extension like "Get cookies.txt" or "cookies.txt"
   - Visit YouTube and login to your account
   - Export cookies.txt file from the extension

2. **Host cookies file publicly:**
   - Upload to cloud storage (S3, Dropbox, GitHub raw, etc.)
   - Get a public URL to the cookies file
   - Update cookies weekly for best results

3. **Use cookies_url parameter:**
   ```json
   {
     "video_url": "https://www.youtube.com/watch?v=example",
     "cookies_url": "https://your-storage.com/cookies.txt",
     "max_duration": 30,
     "quality": "high"
   }
   ```

#### Option 2: Enhanced Request Headers (Automatic)
The API now automatically uses:
- Browser-like User-Agent headers
- Retry logic with exponential backoff  
- Optimized format selection for servers
- Fragment retry mechanisms

#### Option 3: Alternative Video Sources
- Use direct video URLs when available
- Pre-download and upload videos to your storage
- Use videos from less restrictive platforms

**Cookie File Format Example:**
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	session_token	abc123...
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	def456...
```

**Security Notes:**
- Only use cookies from accounts you control
- Rotate cookies regularly (weekly recommended)
- Don't share cookie files publicly
- Use separate YouTube account for API access

**Quick Test:**
```bash
# Test with cookies
curl -X POST "https://your-api.com/v1/yt-shorts/" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "cookies_url": "https://your-cookies-url.com/cookies.txt",
    "max_duration": 30,
    "quality": "low"
  }'
```

### 1. Job Creation Issues

#### Problem: "Invalid YouTube URL format"
**Symptoms**: HTTP 400 error when creating a job
**Cause**: The provided URL is not a valid YouTube URL

**Solution**:
```python
# ✅ Correct formats
valid_urls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtube.com/watch?v=dQw4w9WgXcQ"
]

# ❌ Invalid formats
invalid_urls = [
    "https://vimeo.com/123456",
    "https://tiktok.com/@user/video/123",
    "not-a-url",
    "https://youtube.com/playlist?list=..."
]
```

#### Problem: "Custom segment duration cannot exceed 5 minutes"
**Symptoms**: HTTP 400 error when using custom time segments
**Cause**: The difference between custom_end_time and custom_start_time is too large

**Solution**:
```python
# ✅ Correct: 60 second segment
config = {
    "custom_start_time": 120.0,
    "custom_end_time": 180.0,  # 60 seconds duration
    "use_ai_highlight": False
}

# ❌ Incorrect: 10 minute segment
config = {
    "custom_start_time": 120.0,
    "custom_end_time": 720.0,  # 600 seconds = 10 minutes (too long)
    "use_ai_highlight": False
}
```

### 2. Authentication Issues

#### Problem: "Unauthorized" (HTTP 401)
**Symptoms**: All requests return 401 Unauthorized
**Cause**: Missing or invalid API key

**Solution**:
```python
# ✅ Correct header format
headers = {
    "X-API-Key": "your_actual_api_key_here",  # Replace with real key
    "Content-Type": "application/json"
}

# ❌ Common mistakes
bad_headers = {
    "Authorization": "Bearer your_key",  # Wrong header name
    "API-Key": "your_key",               # Missing X- prefix
    "X-API-Key": "",                     # Empty key
    "X-API-Key": "undefined"             # Literal "undefined"
}
```

#### Problem: API Key Not Working
**Symptoms**: Still getting 401 errors with correct header format
**Cause**: API key may be invalid, expired, or not properly configured

**Solution**:
1. **Verify API key**: Check that your API key is correctly copied
2. **Check expiration**: Ensure your API key hasn't expired
3. **Contact support**: If issues persist, contact API support

### 3. Processing Issues

#### Problem: Job Stuck in "pending" Status
**Symptoms**: Job remains in "pending" status for extended periods
**Cause**: High server load or queue backlog

**Solution**:
```python
import time

def wait_for_job_with_timeout(job_id, timeout_minutes=30):
    """Wait for job completion with timeout."""
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    while time.time() - start_time < timeout_seconds:
        response = requests.get(f"{BASE_URL}/{job_id}", headers=headers)
        job = response.json()
        
        if job["status"] != "pending":
            return job
        
        print(f"⏳ Still pending... ({int(time.time() - start_time)}s)")
        time.sleep(30)  # Check every 30 seconds
    
    raise TimeoutError(f"Job {job_id} did not start processing within {timeout_minutes} minutes")
```

#### Problem: "Job failed: Video download failed"
**Symptoms**: Job fails during video download phase
**Cause**: YouTube video may be private, age-restricted, or unavailable

**Solution**:
1. **Check video availability**: Ensure the video is publicly accessible
2. **Verify URL**: Make sure the YouTube URL is correct and working
3. **Try different video**: Test with a known working public video

```python
# Test with a known working video
test_config = {
    "video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo" - first YouTube video
    "max_duration": 30,
    "quality": "medium"
}
```

#### Problem: "Job failed: Transcription failed"
**Symptoms**: Job fails during audio transcription
**Cause**: Video may have no audio, very poor audio quality, or non-English speech

**Solution**:
```python
# Try with a video that has clear English speech
config = {
    "video_url": "your_video_url",
    "use_ai_highlight": False,  # Skip AI analysis if transcription fails
    "custom_start_time": 60,
    "custom_end_time": 120,
    "enhance_audio": True,
    "audio_enhancement_level": "speech"
}
```

### 4. Quality Issues

#### Problem: Poor Video Quality
**Symptoms**: Output video is pixelated or blurry
**Cause**: Low quality preset or poor source video

**Solution**:
```python
# Use higher quality preset
config = {
    "quality": "high",  # or "ultra" for maximum quality
    "target_resolution": "1080x1920",  # Higher resolution
    "output_format": "mp4"
}
```

#### Problem: Audio Out of Sync
**Symptoms**: Audio doesn't match video movements
**Cause**: Processing error or source video issues

**Solution**:
```python
# Enable audio enhancement and verification
config = {
    "enhance_audio": True,
    "audio_enhancement_level": "speech",
    "smooth_transitions": True,
    "quality": "high"  # Higher quality often improves sync
}
```

#### Problem: Face Not Properly Tracked
**Symptoms**: Face cropping is off-center or jumpy
**Cause**: Poor face detection or tracking sensitivity

**Solution**:
```python
# Adjust face tracking sensitivity
config = {
    "speaker_tracking": True,
    "face_tracking_sensitivity": "high",  # Try different levels
    "crop_to_vertical": True,
    "smooth_transitions": True
}
```

### 5. Performance Issues

#### Problem: Very Slow Processing
**Symptoms**: Jobs take much longer than expected
**Cause**: High quality settings or complex processing

**Solution**:
```python
# Optimize for speed
fast_config = {
    "quality": "medium",           # Lower quality for speed
    "use_ai_highlight": False,     # Skip AI analysis
    "custom_start_time": 60,       # Use known good segment
    "custom_end_time": 120,
    "speaker_tracking": False,     # Disable if not needed
    "enhance_audio": False,        # Skip audio enhancement
    "target_resolution": "720x1280"  # Lower resolution
}
```

#### Problem: Rate Limiting
**Symptoms**: HTTP 429 "Too Many Requests" errors
**Cause**: Exceeded API rate limits

**Solution**:
```python
import time
from requests.exceptions import HTTPError

def create_job_with_rate_limiting(config):
    """Create job with automatic rate limit handling."""
    max_retries = 3
    retry_delay = 60  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.post(f"{BASE_URL}/", json=config, headers=headers)
            response.raise_for_status()
            return response.json()["job_id"]
            
        except HTTPError as e:
            if e.response.status_code == 429:
                if attempt < max_retries - 1:
                    print(f"⏳ Rate limited, waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
            else:
                raise
```

### 6. Network Issues

#### Problem: Connection Timeouts
**Symptoms**: Requests fail with timeout errors
**Cause**: Network connectivity issues or server overload

**Solution**:
```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_robust_session():
    """Create a session with retry strategy."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Use the robust session
session = create_robust_session()
response = session.post(f"{BASE_URL}/", json=config, headers=headers, timeout=30)
```

### 7. Model and Dependency Issues

#### Problem: "Face detection model not found"
**Symptoms**: Job fails with missing model file errors
**Cause**: Model files are not properly installed

**Solution**:
```bash
# Verify model files exist
ls -la /home/etugrand/DEV.ai/Projects/griot/models/yt_shorts/
# Should show:
# - deploy.prototxt
# - res10_300x300_ssd_iter_140000_fp16.caffemodel
# - haarcascade_frontalface_default.xml
```

#### Problem: "Module not found: webrtcvad"
**Symptoms**: Speaker detection fails with import errors
**Cause**: Missing dependencies

**Solution**:
```bash
# Install missing dependencies
pip install webrtcvad-wheels
pip install opencv-python
pip install moviepy
```

### 8. S3 Storage Issues

#### Problem: "S3 upload failed"
**Symptoms**: Job completes processing but fails during upload
**Cause**: S3 configuration or permissions issues

**Solution**:
1. **Check S3 configuration**:
```env
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
S3_REGION=your_region
```

2. **Verify S3 permissions**: Ensure your S3 credentials have upload permissions
3. **Check bucket exists**: Verify the S3 bucket exists and is accessible

### 9. Debugging Steps

#### Step 1: Enable Detailed Logging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add detailed logging to your requests
response = requests.post(f"{BASE_URL}/", json=config, headers=headers)
logger.debug(f"Request: {config}")
logger.debug(f"Response: {response.status_code} - {response.text}")
```

#### Step 2: Test with Minimal Configuration
```python
# Minimal test configuration
minimal_config = {
    "video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "max_duration": 30,
    "quality": "low",
    "use_ai_highlight": False,
    "custom_start_time": 0,
    "custom_end_time": 30,
    "speaker_tracking": False,
    "enhance_audio": False,
    "crop_to_vertical": False
}
```

#### Step 3: Check System Resources
```python
import psutil

def check_system_resources():
    """Check available system resources."""
    print(f"CPU usage: {psutil.cpu_percent()}%")
    print(f"Memory usage: {psutil.virtual_memory().percent}%")
    print(f"Disk usage: {psutil.disk_usage('/').percent}%")

check_system_resources()
```

### 10. Common Error Messages and Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Invalid YouTube URL format" | Malformed URL | Use proper YouTube URL format |
| "Video not found or private" | Video unavailable | Check video accessibility |
| "Transcription failed" | Audio issues | Try with clear speech video |
| "Face detection failed" | No faces in video | Disable speaker tracking |
| "Processing timeout" | Server overload | Retry with lower quality |
| "S3 upload failed" | Storage issues | Check S3 configuration |
| "Rate limit exceeded" | Too many requests | Implement rate limiting |
| "Model file not found" | Missing dependencies | Install required model files |

### 11. Performance Optimization

#### Quick Processing Tips
1. **Use custom segments** instead of AI analysis
2. **Lower quality settings** for faster processing
3. **Disable unnecessary features** (speaker tracking, audio enhancement)
4. **Shorter segments** process faster
5. **Pre-analyze videos** to find good segments

#### Resource Management
```python
# Optimal configuration for different use cases

# Speed-optimized (30-60 seconds)
speed_config = {
    "quality": "low",
    "use_ai_highlight": False,
    "speaker_tracking": False,
    "enhance_audio": False,
    "target_resolution": "720x1280"
}

# Quality-optimized (5-10 minutes)
quality_config = {
    "quality": "ultra",
    "use_ai_highlight": True,
    "speaker_tracking": True,
    "enhance_audio": True,
    "target_resolution": "1080x1920"
}

# Balanced (2-4 minutes)
balanced_config = {
    "quality": "high",
    "use_ai_highlight": True,
    "speaker_tracking": True,
    "enhance_audio": True,
    "target_resolution": "1080x1920"
}
```

### 12. Getting Help

If you're still experiencing issues:

1. **Check the logs** in your application
2. **Review the API documentation** for correct usage
3. **Test with known working examples**
4. **Verify all dependencies** are installed
5. **Check system resources** (CPU, memory, disk space)
6. **Contact support** with specific error messages and job IDs

#### Support Information Format
When contacting support, please include:
- **Job ID**: The specific job that failed
- **Error message**: Complete error message from the API
- **Configuration**: The exact configuration used
- **Video URL**: The YouTube URL being processed (if public)
- **Timestamp**: When the error occurred
- **Steps to reproduce**: What you did to trigger the error

---

*This troubleshooting guide covers the most common issues. For additional support, please refer to the API documentation or contact technical support.*