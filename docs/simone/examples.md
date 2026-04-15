# Simone Examples

This document provides practical examples and code samples for using Simone's video-to-content conversion capabilities.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Advanced Examples](#advanced-examples)
- [Platform-Specific Examples](#platform-specific-examples)
- [Integration Examples](#integration-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Basic Examples

### Simple Video to Blog Conversion

Convert a YouTube video to a blog post without social media content.

```bash
curl -X POST "http://localhost:8000/v1/simone/video-to-blog" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }'
```

**Response:**
```json
{
  "job_id": "blog-job-123",
  "status": "pending"
}
```

### Check Job Status

```bash
curl "http://localhost:8000/v1/simone/video-to-blog/blog-job-123" \
  -H "X-API-Key: your-api-key"
```

### Video to Blog with LinkedIn Post

Generate a blog post and LinkedIn-optimized social media post.

```bash
curl -X POST "http://localhost:8000/v1/simone/video-to-blog" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=example-video",
    "platform": "linkedin"
  }'
```

---

## Advanced Examples

### Viral Content Generation

Create a comprehensive content package with viral optimization.

```bash
curl -X POST "http://localhost:8000/v1/simone/viral-content" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=tech-tutorial",
    "include_topics": true,
    "include_x_thread": true,
    "platforms": ["x", "linkedin", "instagram"],
    "thread_config": {
      "max_posts": 12,
      "character_limit": 280,
      "thread_style": "viral"
    }
  }'
```

### Multi-Platform Content Generation

Generate content for multiple social media platforms simultaneously.

```bash
curl -X POST "http://localhost:8000/v1/simone/viral-content" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=business-insights",
    "platforms": ["x", "linkedin", "instagram", "facebook"],
    "thread_config": {
      "max_posts": 8,
      "character_limit": 280,
      "thread_style": "professional"
    }
  }'
```

### Processing Private or Authenticated Videos

For videos requiring authentication (private YouTube videos, etc.).

```bash
curl -X POST "http://localhost:8000/v1/simone/video-to-blog" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=private-video",
    "platform": "x",
    "cookies_content": "session_token=abc123; user_id=456789",
    "cookies_url": "https://www.youtube.com"
  }'
```

---

## Platform-Specific Examples

### X (Twitter) Thread Generation

Focus on viral X thread creation with engagement optimization.

```bash
curl -X POST "http://localhost:8000/v1/simone/viral-content" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=viral-content",
    "platforms": ["x"],
    "include_x_thread": true,
    "thread_config": {
      "max_posts": 15,
      "character_limit": 280,
      "thread_style": "viral"
    }
  }'
```

### LinkedIn Professional Content

Generate professional LinkedIn content with industry focus.

```bash
curl -X POST "http://localhost:8000/v1/simone/viral-content" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=industry-insights",
    "platforms": ["linkedin"],
    "include_topics": true,
    "thread_config": {
      "thread_style": "professional"
    }
  }'
```

### Instagram Visual Content

Create Instagram-optimized content with visual focus.

```bash
curl -X POST "http://localhost:8000/v1/simone/viral-content" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=visual-tutorial",
    "platforms": ["instagram"],
    "include_topics": true
  }'
```

---

## Integration Examples

### Python Integration

```python
import requests
import time
import json

class SimoneClient:
    def __init__(self, api_key, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def create_blog_job(self, url, platform=None):
        """Create a video-to-blog processing job."""
        data = {"url": url}
        if platform:
            data["platform"] = platform
        
        response = requests.post(
            f"{self.base_url}/v1/simone/video-to-blog",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def create_viral_content_job(self, url, **kwargs):
        """Create an enhanced processing job."""
        data = {"url": url, **kwargs}
        
        response = requests.post(
            f"{self.base_url}/v1/simone/viral-content",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_job_status(self, job_id, job_type="video-to-blog"):
        """Get job status and results."""
        endpoint = f"/v1/simone/{job_type}/{job_id}"
        
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id, job_type="video-to-blog", timeout=600):
        """Wait for job completion with polling."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_job_status(job_id, job_type)
            status = result["status"]
            
            if status == "completed":
                return result
            elif status == "failed":
                raise Exception(f"Job failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(10)  # Poll every 10 seconds
        
        raise Exception(f"Job timed out after {timeout} seconds")

# Usage example
client = SimoneClient("your-api-key")

# Create and wait for basic blog processing
job = client.create_blog_job(
    url="https://www.youtube.com/watch?v=example",
    platform="linkedin"
)

print(f"Created job: {job['job_id']}")

# Wait for completion
result = client.wait_for_completion(job["job_id"])
print("Blog post generated:")
print(result["result"]["blog_post_content"][:200] + "...")

# Create enhanced processing job
viral_content_job = client.create_viral_content_job(
    url="https://www.youtube.com/watch?v=example",
    platforms=["x", "linkedin"],
    include_x_thread=True,
    thread_config={
        "max_posts": 10,
        "thread_style": "viral"
    }
)

# Wait for enhanced processing
viral_content_result = client.wait_for_completion(
    viral_content_job["job_id"], 
    "viral-content"
)

print("Enhanced content package generated:")
print(f"Topics found: {viral_content_result['result']['processing_summary']['total_topics']}")
print(f"Thread posts: {viral_content_result['result']['processing_summary']['thread_posts']}")
```

### JavaScript/Node.js Integration

```javascript
const axios = require('axios');

class SimoneClient {
    constructor(apiKey, baseUrl = 'http://localhost:8000') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        };
    }

    async createBlogJob(url, platform = null) {
        const data = { url };
        if (platform) data.platform = platform;

        const response = await axios.post(
            `${this.baseUrl}/v1/simone/video-to-blog`,
            data,
            { headers: this.headers }
        );
        return response.data;
    }

    async createEnhancedJob(url, options = {}) {
        const data = { url, ...options };

        const response = await axios.post(
            `${this.baseUrl}/v1/simone/viral-content`,
            data,
            { headers: this.headers }
        );
        return response.data;
    }

    async getJobStatus(jobId, jobType = 'video-to-blog') {
        const response = await axios.get(
            `${this.baseUrl}/v1/simone/${jobType}/${jobId}`,
            { headers: this.headers }
        );
        return response.data;
    }

    async waitForCompletion(jobId, jobType = 'video-to-blog', timeout = 600000) {
        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            const result = await this.getJobStatus(jobId, jobType);
            
            if (result.status === 'completed') {
                return result;
            } else if (result.status === 'failed') {
                throw new Error(`Job failed: ${result.error || 'Unknown error'}`);
            }

            await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
        }

        throw new Error(`Job timed out after ${timeout}ms`);
    }
}

// Usage example
async function processVideo() {
    const client = new SimoneClient('your-api-key');

    try {
        // Create enhanced processing job
        const job = await client.createEnhancedJob(
            'https://www.youtube.com/watch?v=example',
            {
                platforms: ['x', 'linkedin', 'instagram'],
                include_x_thread: true,
                thread_config: {
                    max_posts: 8,
                    thread_style: 'viral'
                }
            }
        );

        console.log(`Created job: ${job.job_id}`);

        // Wait for completion
        const result = await client.waitForCompletion(job.job_id, 'viral-content');
        
        console.log('Processing completed!');
        console.log(`Blog post URL: ${result.result.blog_post_url}`);
        console.log(`Screenshots: ${result.result.screenshots.length}`);
        console.log(`Platforms: ${result.result.processing_summary.platforms_generated.join(', ')}`);

    } catch (error) {
        console.error('Error processing video:', error.message);
    }
}

processVideo();
```

---

## Error Handling

### Handling Common Errors

```python
import requests

def safe_create_job(api_key, url, platform=None):
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    data = {"url": url}
    if platform:
        data["platform"] = platform
    
    try:
        response = requests.post(
            "http://localhost:8000/v1/simone/video-to-blog",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 401:
            return {"error": "Invalid API key"}
        elif response.status_code == 400:
            return {"error": f"Bad request: {response.json().get('detail', 'Unknown error')}"}
        elif response.status_code == 500:
            return {"error": "Server error - please try again later"}
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to server"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

# Usage
result = safe_create_job("your-api-key", "https://youtube.com/watch?v=example")
if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(f"Job created: {result['job_id']}")
```

### Retry Logic

```python
import time
import random

def create_job_with_retry(api_key, url, max_retries=3):
    for attempt in range(max_retries):
        result = safe_create_job(api_key, url)
        
        if "error" not in result:
            return result
        
        if attempt < max_retries - 1:
            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f} seconds...")
            time.sleep(delay)
    
    return {"error": "Max retries exceeded"}
```

---

## Best Practices

### 1. Optimal Video Selection

```python
# Good video characteristics for Simone processing
good_videos = [
    "https://youtube.com/watch?v=tutorial-content",     # Educational content
    "https://youtube.com/watch?v=expert-interview",    # Interviews and discussions
    "https://youtube.com/watch?v=product-demo",        # Product demonstrations
    "https://youtube.com/watch?v=conference-talk"      # Conference presentations
]

# Less optimal videos
avoid_videos = [
    "https://youtube.com/watch?v=music-video",         # Music videos (little spoken content)
    "https://youtube.com/watch?v=silent-footage",      # Videos without speech
    "https://youtube.com/watch?v=non-english"          # Non-English content (if not supported)
]
```

### 2. Platform-Specific Optimization

```python
# X (Twitter) optimization
x_config = {
    "platforms": ["x"],
    "include_x_thread": True,
    "thread_config": {
        "max_posts": 8,
        "character_limit": 280,
        "thread_style": "viral"
    }
}

# LinkedIn optimization
linkedin_config = {
    "platforms": ["linkedin"],
    "include_topics": True,
    "thread_config": {
        "thread_style": "professional"
    }
}

# Instagram optimization
instagram_config = {
    "platforms": ["instagram"],
    "include_topics": True
}
```

### 3. Batch Processing

```python
def process_multiple_videos(api_key, video_urls):
    client = SimoneClient(api_key)
    jobs = []
    
    # Create all jobs first
    for url in video_urls:
        try:
            job = client.create_viral_content_job(url, platforms=["x", "linkedin"])
            jobs.append({"job_id": job["job_id"], "url": url})
        except Exception as e:
            print(f"Failed to create job for {url}: {e}")
    
    # Wait for all jobs to complete
    results = []
    for job in jobs:
        try:
            result = client.wait_for_completion(job["job_id"], "viral-content")
            results.append({"url": job["url"], "result": result})
        except Exception as e:
            print(f"Job {job['job_id']} failed: {e}")
            results.append({"url": job["url"], "error": str(e)})
    
    return results

# Usage
video_urls = [
    "https://youtube.com/watch?v=video1",
    "https://youtube.com/watch?v=video2",
    "https://youtube.com/watch?v=video3"
]

results = process_multiple_videos("your-api-key", video_urls)
```

### 4. Content Quality Validation

```python
def validate_content_quality(result):
    """Validate the quality of generated content."""
    if result["status"] != "completed":
        return False, "Job not completed"
    
    content = result["result"]
    
    # Check blog post length
    blog_content = content.get("blog_post_content", "")
    if len(blog_content) < 500:
        return False, "Blog post too short"
    
    # Check screenshot count
    screenshots = content.get("screenshots", [])
    if len(screenshots) < 2:
        return False, "Insufficient screenshots generated"
    
    # Check transcription quality
    transcription = content.get("transcription_content", "")
    if len(transcription) < 200:
        return False, "Transcription too short - possible audio quality issues"
    
    return True, "Content quality acceptable"

# Usage
result = client.wait_for_completion(job_id, "viral-content")
is_valid, message = validate_content_quality(result)

if is_valid:
    print("Content ready for publication!")
else:
    print(f"Content quality issue: {message}")
```

---

## Next Steps

- Review the [Setup Guide](setup.md) for environment configuration
- Check [Best Practices](best-practices.md) for optimization tips
- Explore [Troubleshooting](troubleshooting.md) for common issues