# YouTube Shorts Examples & Tutorials

## Quick Start Examples

### Basic YouTube Shorts Generation

The simplest way to create a YouTube Short with AI-powered highlight detection:

```python
import requests
import time

API_KEY = "your_api_key_here"
BASE_URL = "https://your-api-domain.com/v1/yt-shorts"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create a basic short
response = requests.post(f"{BASE_URL}/", json={
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "max_duration": 60
}, headers=headers)

job_id = response.json()["job_id"]
print(f"Job created: {job_id}")

# Wait for completion
while True:
    response = requests.get(f"{BASE_URL}/{job_id}", headers=headers)
    job = response.json()
    
    if job["status"] == "completed":
        print(f"✅ Short created: {job['result']['url']}")
        break
    elif job["status"] == "failed":
        print(f"❌ Job failed: {job['error']}")
        break
    
    print(f"⏳ Status: {job['status']}")
    time.sleep(10)
```

### Advanced Configuration

Create a high-quality short with all advanced features enabled:

```python
# Advanced configuration example
advanced_config = {
    "video_url": "https://www.youtube.com/watch?v=example",
    "max_duration": 45,
    "quality": "ultra",
    "output_format": "mp4",
    
    # AI Features
    "use_ai_highlight": True,
    "speaker_tracking": True,
    "face_tracking_sensitivity": "high",
    
    # Video Processing
    "crop_to_vertical": True,
    "target_resolution": "1080x1920",
    "smooth_transitions": True,
    
    # Audio Enhancement
    "enhance_audio": True,
    "audio_enhancement_level": "speech",
    
    # Additional Features
    "create_thumbnail": True
}

response = requests.post(f"{BASE_URL}/", json=advanced_config, headers=headers)
job_id = response.json()["job_id"]
```

### Custom Time Segment

Extract a specific segment from a video without AI analysis:

```python
# Custom time segment example
custom_segment = {
    "video_url": "https://www.youtube.com/watch?v=example",
    "custom_start_time": 120.5,  # Start at 2:00.5
    "custom_end_time": 180.0,    # End at 3:00.0
    "use_ai_highlight": False,   # Skip AI analysis
    "quality": "high",
    "crop_to_vertical": True
}

response = requests.post(f"{BASE_URL}/", json=custom_segment, headers=headers)
```

## Complete Tutorial: From YouTube to TikTok

### Step 1: Analyze Video First

Before creating a short, analyze the video to understand its content:

```python
def analyze_video(video_url):
    """Analyze a YouTube video for optimal shorts generation."""
    response = requests.post(f"{BASE_URL}/analyze", json={
        "video_url": video_url
    }, headers=headers)
    
    analysis = response.json()
    print(f"📊 Video Analysis:")
    print(f"Duration: {analysis['analysis']['duration']}")
    print(f"Speaker count: {analysis['analysis']['speaker_count']}")
    print(f"Face detection confidence: {analysis['analysis']['face_detection_confidence']}")
    
    print("\n🎯 Recommended segments:")
    for i, segment in enumerate(analysis['analysis']['recommended_segments'], 1):
        print(f"{i}. {segment['start']}s - {segment['end']}s: {segment['reason']}")
    
    return analysis

# Example usage
video_url = "https://www.youtube.com/watch?v=example"
analysis = analyze_video(video_url)
```

### Step 2: Create Optimized Short

Based on the analysis, create an optimized short:

```python
def create_optimized_short(video_url, analysis):
    """Create an optimized short based on video analysis."""
    
    # Use the first recommended segment if available
    recommended_segments = analysis['analysis']['recommended_segments']
    
    if recommended_segments:
        segment = recommended_segments[0]
        config = {
            "video_url": video_url,
            "custom_start_time": segment['start'],
            "custom_end_time": segment['end'],
            "use_ai_highlight": False,  # We already have the segment
            "quality": "high",
            "speaker_tracking": True,
            "enhance_audio": True,
            "target_resolution": "1080x1920",  # TikTok optimized
            "create_thumbnail": True
        }
    else:
        # Fall back to AI highlight detection
        config = {
            "video_url": video_url,
            "use_ai_highlight": True,
            "max_duration": 60,
            "quality": "high",
            "speaker_tracking": True,
            "enhance_audio": True,
            "target_resolution": "1080x1920"
        }
    
    response = requests.post(f"{BASE_URL}/", json=config, headers=headers)
    return response.json()["job_id"]

# Example usage
job_id = create_optimized_short(video_url, analysis)
```

### Step 3: Monitor Progress with Detailed Logging

```python
def monitor_job_with_details(job_id):
    """Monitor job progress with detailed logging."""
    
    while True:
        response = requests.get(f"{BASE_URL}/{job_id}", headers=headers)
        job = response.json()
        
        status = job["status"]
        
        if status == "completed":
            result = job["result"]
            
            print("✅ Job completed successfully!")
            print(f"📹 Video URL: {result['url']}")
            print(f"🖼️ Thumbnail: {result['thumbnail_url']}")
            print(f"⏱️ Duration: {result['duration']}s")
            print(f"🎯 Segment: {result['highlight_start']}s - {result['highlight_end']}s")
            
            # Processing statistics
            stats = result['processing_stats']
            print(f"\n📊 Processing Statistics:")
            print(f"Download size: {stats['download_size'] / 1024 / 1024:.1f} MB")
            print(f"Transcription segments: {stats['transcription_segments']}")
            print(f"AI highlight detected: {stats['ai_highlight_detected']}")
            print(f"Dynamic crop applied: {stats['dynamic_crop_applied']}")
            
            # Quality check
            quality = result['quality_check']
            print(f"\n🔍 Quality Check:")
            print(f"File size: {quality['file_size'] / 1024 / 1024:.1f} MB")
            print(f"Resolution: {quality['resolution']}")
            print(f"Bitrate: {quality['bitrate'] / 1000:.0f} kbps")
            print(f"Audio-video sync: {'✅' if quality['av_sync'] else '❌'}")
            
            return result
            
        elif status == "failed":
            print(f"❌ Job failed: {job['error']}")
            return None
            
        elif status == "processing":
            print("⚙️ Processing video...")
            
        elif status == "pending":
            print("⏳ Job is queued...")
        
        time.sleep(10)

# Example usage
result = monitor_job_with_details(job_id)
```

## Platform-Specific Optimizations

### TikTok Optimization

```python
def create_tiktok_short(video_url):
    """Create a TikTok-optimized short."""
    return {
        "video_url": video_url,
        "max_duration": 60,  # TikTok max length
        "quality": "high",
        "target_resolution": "1080x1920",  # TikTok preferred resolution
        "crop_to_vertical": True,
        "speaker_tracking": True,
        "enhance_audio": True,
        "audio_enhancement_level": "speech",  # Clear speech for TikTok
        "smooth_transitions": True,
        "face_tracking_sensitivity": "high",  # Important for TikTok engagement
        "output_format": "mp4"
    }
```

### Instagram Reels Optimization

```python
def create_instagram_reel(video_url):
    """Create an Instagram Reels-optimized short."""
    return {
        "video_url": video_url,
        "max_duration": 90,  # Instagram Reels max length
        "quality": "high",
        "target_resolution": "1080x1920",
        "crop_to_vertical": True,
        "speaker_tracking": True,
        "enhance_audio": True,
        "audio_enhancement_level": "auto",  # Auto-detect for mixed content
        "smooth_transitions": True,
        "create_thumbnail": True,  # Important for Instagram
        "output_format": "mp4"
    }
```

### YouTube Shorts Optimization

```python
def create_youtube_short(video_url):
    """Create a YouTube Shorts-optimized short."""
    return {
        "video_url": video_url,
        "max_duration": 60,  # YouTube Shorts max length
        "quality": "ultra",  # Higher quality for YouTube
        "target_resolution": "1080x1920",
        "crop_to_vertical": True,
        "speaker_tracking": True,
        "enhance_audio": True,
        "audio_enhancement_level": "speech",
        "smooth_transitions": True,
        "face_tracking_sensitivity": "medium",
        "create_thumbnail": True,
        "output_format": "mp4"
    }
```

## Batch Processing Multiple Videos

```python
def batch_process_videos(video_urls, config_template):
    """Process multiple videos with the same configuration."""
    
    jobs = []
    
    # Create all jobs
    for i, video_url in enumerate(video_urls, 1):
        config = config_template.copy()
        config["video_url"] = video_url
        
        response = requests.post(f"{BASE_URL}/", json=config, headers=headers)
        job_id = response.json()["job_id"]
        
        jobs.append({
            "id": job_id,
            "video_url": video_url,
            "index": i
        })
        
        print(f"📄 Created job {i}/{len(video_urls)}: {job_id}")
    
    # Monitor all jobs
    completed = []
    failed = []
    
    while len(completed) + len(failed) < len(jobs):
        for job in jobs:
            if job["id"] in [c["id"] for c in completed] or job["id"] in [f["id"] for f in failed]:
                continue
                
            response = requests.get(f"{BASE_URL}/{job['id']}", headers=headers)
            job_data = response.json()
            
            if job_data["status"] == "completed":
                completed.append({
                    "id": job["id"],
                    "video_url": job["video_url"],
                    "result": job_data["result"]
                })
                print(f"✅ Job {job['index']} completed")
                
            elif job_data["status"] == "failed":
                failed.append({
                    "id": job["id"],
                    "video_url": job["video_url"],
                    "error": job_data["error"]
                })
                print(f"❌ Job {job['index']} failed")
        
        time.sleep(10)
    
    return completed, failed

# Example usage
video_urls = [
    "https://www.youtube.com/watch?v=video1",
    "https://www.youtube.com/watch?v=video2",
    "https://www.youtube.com/watch?v=video3"
]

config = create_tiktok_short("")  # Template config
completed, failed = batch_process_videos(video_urls, config)

print(f"\n📊 Results: {len(completed)} completed, {len(failed)} failed")
```

## Error Handling Best Practices

```python
def robust_shorts_creation(video_url, max_retries=3):
    """Create a short with robust error handling."""
    
    for attempt in range(max_retries):
        try:
            # Create job
            response = requests.post(f"{BASE_URL}/", json={
                "video_url": video_url,
                "max_duration": 60,
                "quality": "high"
            }, headers=headers)
            
            if response.status_code == 429:  # Rate limited
                print("⏳ Rate limited, waiting 60 seconds...")
                time.sleep(60)
                continue
            
            response.raise_for_status()
            job_id = response.json()["job_id"]
            
            # Monitor job
            while True:
                response = requests.get(f"{BASE_URL}/{job_id}", headers=headers)
                response.raise_for_status()
                
                job = response.json()
                
                if job["status"] == "completed":
                    return job["result"]
                elif job["status"] == "failed":
                    error = job["error"]
                    print(f"❌ Job failed: {error}")
                    
                    # Retry on certain errors
                    if "timeout" in error.lower() or "temporary" in error.lower():
                        print(f"🔄 Retrying... (attempt {attempt + 1}/{max_retries})")
                        break
                    else:
                        raise Exception(f"Job failed: {error}")
                
                time.sleep(10)
                
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(30)
            else:
                raise
        
        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(30)
            else:
                raise
    
    raise Exception(f"Failed to create short after {max_retries} attempts")

# Example usage
try:
    result = robust_shorts_creation("https://www.youtube.com/watch?v=example")
    print(f"✅ Success: {result['url']}")
except Exception as e:
    print(f"❌ Failed: {e}")
```

## Performance Optimization Tips

### 1. Choose Appropriate Quality

```python
# For quick testing
config = {"quality": "low"}  # ~30-60 seconds processing

# For production
config = {"quality": "high"}  # ~2-4 minutes processing

# For premium content
config = {"quality": "ultra"}  # ~4-8 minutes processing
```

### 2. Use Custom Segments When Possible

```python
# Faster: Skip AI analysis when you know the segment
config = {
    "custom_start_time": 60,
    "custom_end_time": 120,
    "use_ai_highlight": False  # Skip AI processing
}

# Slower: Let AI find the best segment
config = {
    "use_ai_highlight": True,
    "max_duration": 60
}
```

### 3. Optimize for Your Use Case

```python
# For face-focused content
config = {
    "speaker_tracking": True,
    "face_tracking_sensitivity": "high",
    "crop_to_vertical": True
}

# For landscape/scenery content
config = {
    "speaker_tracking": False,
    "crop_to_vertical": False,
    "target_resolution": "1920x1080"
}
```

## Integration Examples

### Flask Web Application

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/create-short', methods=['POST'])
def create_short():
    data = request.json
    video_url = data.get('video_url')
    
    if not video_url:
        return jsonify({'error': 'video_url is required'}), 400
    
    # Create short
    response = requests.post(f"{BASE_URL}/", json={
        "video_url": video_url,
        "max_duration": 60,
        "quality": "high"
    }, headers=headers)
    
    if response.status_code == 202:
        return jsonify({
            'job_id': response.json()['job_id'],
            'status': 'created'
        })
    else:
        return jsonify({'error': 'Failed to create job'}), 500

@app.route('/job-status/<job_id>')
def job_status(job_id):
    response = requests.get(f"{BASE_URL}/{job_id}", headers=headers)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)
```

### Discord Bot Integration

```python
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.command(name='shorts')
async def create_shorts(ctx, video_url):
    """Create a YouTube short from a video URL."""
    
    await ctx.send(f"🎬 Creating short from: {video_url}")
    
    # Create job
    response = requests.post(f"{BASE_URL}/", json={
        "video_url": video_url,
        "max_duration": 60,
        "quality": "high"
    }, headers=headers)
    
    job_id = response.json()["job_id"]
    
    # Monitor job
    while True:
        response = requests.get(f"{BASE_URL}/{job_id}", headers=headers)
        job = response.json()
        
        if job["status"] == "completed":
            result = job["result"]
            embed = discord.Embed(
                title="✅ Short Created!",
                description=f"Duration: {result['duration']}s",
                color=0x00ff00
            )
            embed.add_field(name="Video", value=result['url'], inline=False)
            embed.add_field(name="Thumbnail", value=result['thumbnail_url'], inline=False)
            await ctx.send(embed=embed)
            break
        elif job["status"] == "failed":
            await ctx.send(f"❌ Failed to create short: {job['error']}")
            break
        
        await asyncio.sleep(10)

bot.run('YOUR_DISCORD_TOKEN')
```

---

*For more advanced examples and use cases, check out our [GitHub repository](https://github.com/your-org/yt-shorts-examples) with complete sample applications.*