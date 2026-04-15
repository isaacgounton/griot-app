# Postiz Integration Examples

This guide provides practical examples for integrating Postiz with your content generation workflows.

## Complete Workflow Examples

### Example 1: AI Video → Social Media Pipeline

```bash
#!/bin/bash
# Complete pipeline: Generate video and auto-schedule to social media

API_KEY="your_api_key_here"
BASE_URL="http://localhost:8000"

# Step 1: Generate a video from topic
echo "🎬 Generating video..."
VIDEO_JOB=$(curl -s -X POST "$BASE_URL/api/v1/ai/footage-to-video" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "10 Mind-Blowing Space Facts",
    "duration": 60,
    "voice_provider": "kokoro",
    "voice_name": "af_bella"
  }' | jq -r '.job_id')

echo "Video job ID: $VIDEO_JOB"

# Step 2: Poll until video is complete
while true; do
  STATUS=$(curl -s -X GET "$BASE_URL/api/v1/ai/footage-to-video/$VIDEO_JOB" \
    -H "X-API-Key: $API_KEY" | jq -r '.status')
  
  if [ "$STATUS" = "completed" ]; then
    echo "✅ Video generation completed!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "❌ Video generation failed!"
    exit 1
  else
    echo "⏳ Video status: $STATUS"
    sleep 30
  fi
done

# Step 3: Get available social media integrations
echo "📱 Getting social media integrations..."
INTEGRATIONS=$(curl -s -X GET "$BASE_URL/api/v1/postiz/integrations" \
  -H "X-API-Key: $API_KEY")

echo "Available integrations: $INTEGRATIONS"

# Step 4: Schedule to multiple platforms
echo "📤 Scheduling to social media..."
curl -X POST "$BASE_URL/api/v1/postiz/schedule-job" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$VIDEO_JOB\",
    \"content\": \"🚀 Just discovered these incredible space facts! Which one surprised you the most? #Space #Facts #AI #Science\",
    \"integrations\": [\"twitter_123\", \"linkedin_456\"],
    \"post_type\": \"now\",
    \"tags\": [\"space\", \"facts\", \"AI\", \"educational\"]
  }"

echo "🎉 Content scheduled successfully!"
```

### Example 2: Batch Image Generation and Scheduling

```javascript
// Node.js example for batch image generation and social media scheduling
const axios = require('axios');

const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000';

async function generateAndScheduleImages() {
  const topics = [
    'Futuristic cityscape at sunset',
    'Serene mountain lake reflection',
    'Abstract digital art with neon colors'
  ];

  for (const topic of topics) {
    try {
      // Generate image
      console.log(`🎨 Generating image: ${topic}`);
      const imageResponse = await axios.post(
        `${BASE_URL}/api/images/generate`,
        {
          prompt: topic,
          width: 1024,
          height: 1024,
          quality: 'high'
        },
        {
          headers: { 'X-API-Key': API_KEY }
        }
      );

      const jobId = imageResponse.data.job_id;
      
      // Poll for completion
      let status = 'pending';
      while (status !== 'completed') {
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        const statusResponse = await axios.get(
          `${BASE_URL}/api/images/generate/${jobId}`,
          { headers: { 'X-API-Key': API_KEY } }
        );
        
        status = statusResponse.data.status;
        console.log(`📊 Image status: ${status}`);
        
        if (status === 'failed') {
          throw new Error('Image generation failed');
        }
      }

      // Schedule to social media with custom content
      const socialContent = `✨ Check out this AI-generated masterpiece: "${topic}" 🎭\n\n#AIArt #DigitalArt #Creative #AI`;
      
      await axios.post(
        `${BASE_URL}/api/v1/postiz/schedule-job`,
        {
          job_id: jobId,
          content: socialContent,
          integrations: ['instagram_789', 'twitter_123'],
          post_type: 'schedule',
          schedule_date: new Date(Date.now() + Math.random() * 24 * 60 * 60 * 1000).toISOString(), // Random time within 24 hours
          tags: ['ai-art', 'creative', 'generated']
        },
        {
          headers: { 'X-API-Key': API_KEY }
        }
      );

      console.log(`✅ Scheduled: ${topic}`);
      
    } catch (error) {
      console.error(`❌ Error with "${topic}":`, error.message);
    }
  }
}

generateAndScheduleImages();
```

### Example 3: YouTube Shorts to TikTok Pipeline

```python
import requests
import time
import json

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000"

def create_tiktok_short(youtube_url):
    """Convert YouTube video to TikTok short and schedule"""
    
    # Step 1: Generate YouTube Short
    print(f"🎬 Creating short from: {youtube_url}")
    response = requests.post(
        f"{BASE_URL}/api/v1/yt-shorts/",
        headers={"X-API-Key": API_KEY},
        json={
            "video_url": youtube_url,
            "max_duration": 60,
            "highlight_detection": True,
            "face_tracking": True,
            "viral_optimization": True
        }
    )
    
    job_id = response.json()["job_id"]
    print(f"📋 Job ID: {job_id}")
    
    # Step 2: Wait for completion
    while True:
        status_response = requests.get(
            f"{BASE_URL}/api/v1/yt-shorts/{job_id}",
            headers={"X-API-Key": API_KEY}
        )
        
        status_data = status_response.json()
        status = status_data["status"]
        
        if status == "completed":
            print("✅ Short creation completed!")
            result = status_data["result"]
            break
        elif status == "failed":
            print("❌ Short creation failed!")
            return None
        else:
            print(f"⏳ Status: {status}")
            time.sleep(30)
    
    # Step 3: Create engaging TikTok content
    video_title = result.get("title", "Amazing content")
    tiktok_content = f"""
🔥 {video_title} 

{result.get('description', 'Check out this incredible content!')}

#viral #trending #fyp #amazing #ai
""".strip()
    
    # Step 4: Schedule to TikTok
    print("📱 Scheduling to TikTok...")
    schedule_response = requests.post(
        f"{BASE_URL}/api/v1/postiz/schedule-job",
        headers={"X-API-Key": API_KEY},
        json={
            "job_id": job_id,
            "content": tiktok_content,
            "integrations": ["tiktok_999"],
            "post_type": "schedule",
            "schedule_date": "2024-12-25T18:00:00Z",  # Peak TikTok time
            "tags": ["viral", "tiktok", "shorts", "ai"]
        }
    )
    
    if schedule_response.status_code == 200:
        print("🎉 Successfully scheduled to TikTok!")
        return schedule_response.json()
    else:
        print(f"❌ Scheduling failed: {schedule_response.text}")
        return None

# Usage
youtube_urls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=example123"
]

for url in youtube_urls:
    result = create_tiktok_short(url)
    if result:
        print(f"✅ Processed: {url}")
    else:
        print(f"❌ Failed: {url}")
    
    time.sleep(60)  # Rate limiting
```

### Example 4: Daily Content Automation

```python
import schedule
import requests
from datetime import datetime, timedelta

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000"

class ContentAutomation:
    def __init__(self):
        self.topics = [
            "Daily motivation quote",
            "Tech tip of the day", 
            "Fun fact about science",
            "Productivity hack",
            "Inspiring success story"
        ]
        self.integrations = ["twitter_123", "linkedin_456"]
    
    def generate_daily_content(self):
        """Generate and schedule daily content"""
        today = datetime.now()
        topic = self.topics[today.weekday() % len(self.topics)]
        
        print(f"📅 {today.strftime('%Y-%m-%d')}: Generating '{topic}'")
        
        # Generate image for the topic
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers={"X-API-Key": API_KEY},
            json={
                "prompt": f"Professional social media post about {topic}, clean design, inspiring",
                "width": 1080,
                "height": 1080
            }
        )
        
        job_id = response.json()["job_id"]
        
        # Wait for completion (simplified)
        import time
        time.sleep(60)  # Wait 1 minute
        
        # Schedule for optimal posting time (9 AM next day)
        schedule_time = (today + timedelta(days=1)).replace(hour=9, minute=0, second=0)
        
        schedule_response = requests.post(
            f"{BASE_URL}/api/v1/postiz/schedule-job",
            headers={"X-API-Key": API_KEY},
            json={
                "job_id": job_id,
                "content": f"🌟 {topic.title()} 🌟\n\nWhat's your take on this? Share in the comments! 👇\n\n#motivation #productivity #success",
                "integrations": self.integrations,
                "post_type": "schedule",
                "schedule_date": schedule_time.isoformat() + "Z",
                "tags": ["daily", "automation", topic.lower().replace(" ", "-")]
            }
        )
        
        print(f"✅ Scheduled for {schedule_time}")
    
    def weekly_batch_generation(self):
        """Generate a week's worth of content"""
        print("📦 Generating weekly batch content...")
        
        for i in range(7):
            future_date = datetime.now() + timedelta(days=i)
            topic = f"Weekly insight #{i+1}: {self.topics[i % len(self.topics)]}"
            
            # Generate content
            response = requests.post(
                f"{BASE_URL}/api/v1/ai/footage-to-video",
                headers={"X-API-Key": API_KEY},
                json={
                    "topic": topic,
                    "duration": 30,
                    "voice_provider": "kokoro"
                }
            )
            
            job_id = response.json()["job_id"]
            
            # Schedule for different times throughout the week
            schedule_time = future_date.replace(hour=10 + (i % 12), minute=0)
            
            requests.post(
                f"{BASE_URL}/api/v1/postiz/schedule-job",
                headers={"X-API-Key": API_KEY},
                json={
                    "job_id": job_id,
                    "integrations": self.integrations,
                    "post_type": "schedule",
                    "schedule_date": schedule_time.isoformat() + "Z",
                    "tags": ["weekly", "batch", f"day-{i+1}"]
                }
            )
            
            print(f"📋 Queued: {topic} for {schedule_time}")

# Set up automation
automation = ContentAutomation()

# Schedule daily content generation
schedule.every().day.at("08:00").do(automation.generate_daily_content)

# Schedule weekly batch on Sundays
schedule.every().sunday.at("07:00").do(automation.weekly_batch_generation)

# Run the scheduler
print("🤖 Content automation started!")
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Integration with Other APIs

### Webhook Integration

```javascript
// Express.js webhook handler for automated scheduling
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

app.post('/webhook/job-completed', async (req, res) => {
  const { job_id, job_type, result } = req.body;
  
  // Auto-schedule certain job types
  const schedulableTypes = ['footage_to_video', 'image_generation', 'yt_shorts'];
  
  if (schedulableTypes.includes(job_type)) {
    try {
      await axios.post('http://localhost:8000/api/v1/postiz/schedule-job', {
        job_id: job_id,
        integrations: ['twitter_123'],
        post_type: 'schedule',
        schedule_date: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours later
        tags: ['auto-scheduled', job_type]
      }, {
        headers: { 'X-API-Key': process.env.API_KEY }
      });
      
      console.log(`✅ Auto-scheduled job ${job_id}`);
    } catch (error) {
      console.error(`❌ Failed to auto-schedule ${job_id}:`, error.message);
    }
  }
  
  res.status(200).json({ success: true });
});

app.listen(3000, () => {
  console.log('Webhook server running on port 3000');
});
```

## Example 5: AI Content Generation Workflow

```bash
#!/bin/bash
# Complete pipeline with AI-generated social media content

API_KEY="your_api_key_here"
BASE_URL="http://localhost:8000"

# Step 1: Create a video about a topic
echo "🎬 Generating video about AI automation..."
VIDEO_JOB=$(curl -s -X POST "$BASE_URL/api/v1/ai/footage-to-video" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "How AI is transforming business automation",
    "duration": 60,
    "voice_provider": "kokoro",
    "voice_name": "af_bella"
  }' | jq -r '.job_id')

echo "Video job ID: $VIDEO_JOB"

# Step 2: Wait for completion
while true; do
  STATUS=$(curl -s -X GET "$BASE_URL/api/v1/ai/footage-to-video/$VIDEO_JOB" \
    -H "X-API-Key: $API_KEY" | jq -r '.status')

  if [ "$STATUS" = "completed" ]; then
    echo "✅ Video generation completed!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "❌ Video generation failed!"
    exit 1
  else
    echo "⏳ Video status: $STATUS"
    sleep 30
  fi
done

# Step 3: Generate AI-powered social media content for Twitter
echo "✨ Generating AI content for Twitter..."
TWITTER_CONTENT=$(curl -s -X POST "$BASE_URL/api/v1/postiz/generate-content" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$VIDEO_JOB\",
    \"platform\": \"twitter\",
    \"content_style\": \"viral\",
    \"max_length\": 280,
    \"user_instructions\": \"Make it exciting and add relevant emojis\"
  }")

echo "Twitter content: $(echo $TWITTER_CONTENT | jq -r '.content')"
TWITTER_TAGS=$(echo $TWITTER_CONTENT | jq -r '.tags | join(", ")')
echo "Tags: $TWITTER_TAGS"

# Step 4: Generate AI content for LinkedIn
echo "✨ Generating AI content for LinkedIn..."
LINKEDIN_CONTENT=$(curl -s -X POST "$BASE_URL/api/v1/postiz/generate-content" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$VIDEO_JOB\",
    \"platform\": \"linkedin\",
    \"content_style\": \"professional\",
    \"user_instructions\": \"Highlight business value and ROI\"
  }")

echo "LinkedIn content: $(echo $LINKEDIN_CONTENT | jq -r '.content')"

# Step 5: Schedule to Twitter
echo "📤 Scheduling to Twitter..."
curl -X POST "$BASE_URL/api/v1/postiz/schedule-job" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$VIDEO_JOB\",
    \"content\": $(echo $TWITTER_CONTENT | jq -r '.content' | jq -R .),
    \"integrations\": [\"twitter_123\"],
    \"post_type\": \"now\",
    \"tags\": $(echo $TWITTER_CONTENT | jq -r '.tags')
  }"

# Step 6: Schedule to LinkedIn
echo "📤 Scheduling to LinkedIn..."
curl -X POST "$BASE_URL/api/v1/postiz/schedule-job" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$VIDEO_JOB\",
    \"content\": $(echo $LINKEDIN_CONTENT | jq -r '.content' | jq -R .),
    \"integrations\": [\"linkedin_456\"],
    \"post_type\": \"now\",
    \"tags\": $(echo $LINKEDIN_CONTENT | jq -r '.tags')
  }"

echo "🎉 Content generated and scheduled successfully!"
```

### Python Example: Multi-Platform AI Content Generation

```python
import requests
import time
import json

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000"

def generate_video(topic: str) -> str:
    """Generate a video and return the job ID."""
    response = requests.post(
        f"{BASE_URL}/api/v1/ai/footage-to-video",
        headers={"X-API-Key": API_KEY},
        json={
            "topic": topic,
            "duration": 60,
            "voice_provider": "kokoro",
            "voice_name": "af_bella"
        }
    )
    return response.json()["job_id"]

def wait_for_completion(job_id: str, endpoint: str) -> dict:
    """Poll job until completion and return result."""
    while True:
        response = requests.get(
            f"{BASE_URL}{endpoint}/{job_id}",
            headers={"X-API-Key": API_KEY}
        )
        data = response.json()

        if data["status"] == "completed":
            print(f"✅ Job {job_id} completed!")
            return data
        elif data["status"] == "failed":
            raise Exception(f"Job failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"⏳ Job {job_id} status: {data['status']}")
            time.sleep(30)

def generate_ai_content(job_id: str, platform: str, style: str, instructions: str = None) -> dict:
    """Generate AI-powered social media content."""
    payload = {
        "job_id": job_id,
        "platform": platform,
        "content_style": style
    }

    if instructions:
        payload["user_instructions"] = instructions

    if platform == "twitter":
        payload["max_length"] = 280

    response = requests.post(
        f"{BASE_URL}/api/v1/postiz/generate-content",
        headers={"X-API-Key": API_KEY},
        json=payload
    )
    return response.json()

def schedule_post(job_id: str, content: str, tags: list, integrations: list):
    """Schedule content to social media platforms."""
    response = requests.post(
        f"{BASE_URL}/api/v1/postiz/schedule-job",
        headers={"X-API-Key": API_KEY},
        json={
            "job_id": job_id,
            "content": content,
            "integrations": integrations,
            "post_type": "now",
            "tags": tags
        }
    )
    return response.json()

# Main workflow
def main():
    # Platform configurations
    platforms = [
        {
            "name": "Twitter",
            "platform": "twitter",
            "style": "viral",
            "instructions": "Make it exciting, use emojis, create curiosity",
            "integrations": ["twitter_123"]
        },
        {
            "name": "LinkedIn",
            "platform": "linkedin",
            "style": "professional",
            "instructions": "Highlight business value, ROI, and professional insights",
            "integrations": ["linkedin_456"]
        },
        {
            "name": "Instagram",
            "platform": "instagram",
            "style": "engaging",
            "instructions": "Visual and engaging, add call-to-action, use 3-5 hashtags",
            "integrations": ["instagram_789"]
        }
    ]

    # Step 1: Generate video
    print("🎬 Generating video...")
    job_id = generate_video("The Future of AI in Healthcare")

    # Step 2: Wait for completion
    print("⏳ Waiting for video completion...")
    result = wait_for_completion(job_id, "/api/v1/ai/footage-to-video")

    # Step 3: Generate and schedule for each platform
    for platform_config in platforms:
        print(f"\n✨ Generating content for {platform_config['name']}...")

        # Generate AI content
        ai_content = generate_ai_content(
            job_id=job_id,
            platform=platform_config["platform"],
            style=platform_config["style"],
            instructions=platform_config["instructions"]
        )

        print(f"Content: {ai_content['content']}")
        print(f"Tags: {', '.join(ai_content['tags'])}")

        # Schedule to platform
        print(f"📤 Scheduling to {platform_config['name']}...")
        schedule_result = schedule_post(
            job_id=job_id,
            content=ai_content["content"],
            tags=ai_content["tags"],
            integrations=platform_config["integrations"]
        )

        if schedule_result.get("success"):
            print(f"✅ Successfully scheduled to {platform_config['name']}")
        else:
            print(f"❌ Failed to schedule to {platform_config['name']}")

    print("\n🎉 All content generated and scheduled successfully!")

if __name__ == "__main__":
    main()
```

### JavaScript Example: Frontend Integration

```javascript
// React component for AI content generation in schedule dialog

async function generateAIContent(jobId, userInstructions) {
  const apiKey = localStorage.getItem('griot_api_key');

  try {
    const response = await fetch('/api/v1/postiz/generate-content', {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        job_id: jobId,
        user_instructions: userInstructions || undefined,
        content_style: 'engaging',
        platform: 'general'
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Update form with generated content and tags
    setFormData(prev => ({
      ...prev,
      content: data.content,
      tags: [...new Set([...prev.tags, ...data.tags])] // Merge and deduplicate
    }));

    console.log('✅ AI content generated successfully');
    console.log('Content:', data.content);
    console.log('Tags:', data.tags);

  } catch (error) {
    console.error('❌ Failed to generate content:', error);
    throw error;
  }
}

// Usage in React component
function ScheduleDialog({ job }) {
  const [formData, setFormData] = useState({
    content: '',
    tags: [],
    userInstructions: ''
  });
  const [generating, setGenerating] = useState(false);

  const handleGenerateContent = async () => {
    setGenerating(true);
    try {
      await generateAIContent(job.id, formData.userInstructions);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Instructions for AI (optional)"
        value={formData.userInstructions}
        onChange={(e) => setFormData({...formData, userInstructions: e.target.value})}
      />

      <button onClick={handleGenerateContent} disabled={generating}>
        {generating ? 'Generating...' : 'Generate AI Content'}
      </button>

      <textarea
        value={formData.content}
        onChange={(e) => setFormData({...formData, content: e.target.value})}
        placeholder="Post content..."
      />

      <div>
        Tags: {formData.tags.map(tag => <span key={tag}>#{tag}</span>)}
      </div>
    </div>
  );
}
```

## Performance Optimization Tips

1. **Batch Operations**: Process multiple jobs before scheduling
2. **Rate Limiting**: Respect social media platform limits
3. **Error Recovery**: Implement retry logic for failed requests
4. **Caching**: Cache integration data to reduce API calls
5. **Monitoring**: Log all scheduling activities for debugging
6. **AI Content Caching**: Cache generated content for similar jobs to reduce AI API calls

## Security Best Practices

1. **API Key Protection**: Never expose API keys in client-side code
2. **Input Validation**: Validate all user inputs before API calls
3. **Rate Limiting**: Implement proper rate limiting in your applications
4. **Error Handling**: Don't expose internal errors in API responses
5. **Audit Logging**: Keep logs of all scheduling activities

---

*These examples demonstrate various integration patterns. Adapt them to your specific use case and requirements.*