# AI Video Search

Intelligent video search and query generation powered by AI. Find relevant stock videos and generate visual search queries from script content.

## Overview

The AI Video Search service combines intelligent query generation with multi-provider stock video integration. It analyzes script content to extract visually concrete concepts and automatically finds matching background footage from Pexels and Pixabay.

## Features

- **🤖 AI Query Generation**: Extract visual concepts from scripts with precise timing
- **📹 Multi-Provider Support**: Access Pexels and Pixabay with automatic fallback
- **⏱️ Timing-Aware**: Generate time-synchronized video segments
- **🎯 Visual Intelligence**: Focus on concrete, searchable visual elements
- **🔍 Smart Filtering**: Resolution, duration, and orientation filtering
- **🔄 Provider Fallback**: Automatic switching between video providers for best results
- **🎨 Manual Browsing**: Direct provider selection for custom video searches

## Quick Start

### 1. Generate Video Search Queries

```bash
curl -X POST "http://localhost:8000/v1/ai/video-search/generate-queries" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "The ocean is home to incredible creatures. Giant whales migrate thousands of miles, while tiny seahorses dance in coral reefs.",
    "segment_duration": 3.0,
    "provider": "auto"
  }'
```

### 2. Search Stock Videos

```bash
curl -X POST "http://localhost:8000/v1/ai/video-search/stock-videos" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ocean waves",
    "orientation": "landscape",
    "min_duration": 5,
    "max_duration": 30,
    "per_page": 10
  }'
```

### 3. Browse Videos with Provider Selection

```bash
curl -X POST "http://localhost:8000/api/v1/ai/video-browse" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ocean waves",
    "provider": "pexels",
    "orientation": "landscape",
    "per_page": 15,
    "page": 1
  }'
```

## Multi-Provider Video Search

### Supported Providers

The video search system now supports multiple providers with automatic fallback:

#### Pexels (Primary Provider)
- **API Key Required**: `PEXELS_API_KEY` environment variable
- **Content**: High-quality stock videos, curated collection
- **Rate Limits**: 200 requests/hour (standard), 20,000/month (with API key)
- **Orientation Support**: Landscape, Portrait, Square
- **Quality**: HD and 4K videos available

#### Pixabay (Secondary Provider)
- **API Key Required**: `PIXABAY_API_KEY` environment variable
- **Content**: Community-contributed videos, diverse selection
- **Rate Limits**: 5,000 requests/day (with API key)
- **Orientation Support**: Horizontal, Vertical, All
- **Quality**: Various qualities including HD

### Provider Selection

#### Manual Provider Selection

Choose a specific provider for your video search:

```bash
# Use Pexels specifically
curl -X POST "http://localhost:8000/api/v1/ai/video-browse" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mountain landscape",
    "provider": "pexels",
    "orientation": "landscape"
  }'

# Use Pixabay specifically  
curl -X POST "http://localhost:8000/api/v1/ai/video-browse" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mountain landscape",
    "provider": "pixabay",
    "orientation": "landscape"
  }'
```

#### Automatic Fallback

When no provider is specified or one fails, the system automatically tries alternatives:

1. **Primary Attempt**: Uses Pexels (if API key available)
2. **Fallback**: Switches to Pixabay on failure
3. **Error Handling**: Returns appropriate error if all providers fail

```bash
# Automatic provider selection with fallback
curl -X POST "http://localhost:8000/api/v1/ai/video-browse" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ocean sunset",
    "orientation": "landscape"
  }'
```

### Response Format with Provider Information

All video search responses include provider information:

```json
{
  "videos": [
    {
      "id": 123456,
      "url": "https://player.vimeo.com/external/...",
      "duration": 15,
      "width": 1920,
      "height": 1080,
      "tags": ["ocean", "sunset", "nature"],
      "user": {"name": "John Photographer"},
      "source": "pexels"
    }
  ],
  "total_results": 42,
  "page": 1,
  "per_page": 15,
  "query_used": "ocean sunset",
  "provider_used": "pexels",
  "note": "Pixabay failed (API key missing), using Pexels instead"
}
```

### Provider Configuration

#### Environment Variables

```bash
# Pexels API Key (recommended)
PEXELS_API_KEY=your_pexels_api_key_here

# Pixabay API Key (optional, for fallback)
PIXABAY_API_KEY=your_pixabay_api_key_here
```

#### API Key Acquisition

**Pexels API Key:**
1. Visit [pexels.com/api](https://www.pexels.com/api/)
2. Create account and request API key
3. Free tier: 200 requests/hour

**Pixabay API Key:**
1. Visit [pixabay.com/api](https://pixabay.com/api/docs/)
2. Register and get API key from account settings
3. Free tier: 5,000 requests/day

### Provider Comparison

| Feature | Pexels | Pixabay |
|---------|--------|---------|
| **Content Quality** | Professional, curated | Mixed, community-driven |
| **Collection Size** | ~3M videos | ~2.7M videos |
| **Rate Limits** | 200/hour | 5,000/day |
| **Commercial Use** | Free | Free |
| **Attribution** | Optional | Optional |
| **Search Accuracy** | High | Good |
| **Processing Speed** | Fast | Moderate |

### Best Practices

#### Provider Strategy

1. **Dual Setup**: Configure both API keys for maximum reliability
2. **Primary Choice**: Use Pexels for high-quality, professional content
3. **Fallback Usage**: Let Pixabay provide additional coverage
4. **Monitoring**: Track which provider is used in responses

#### Query Optimization

```bash
# For professional/commercial content
{
  "query": "business meeting",
  "provider": "pexels",
  "orientation": "landscape"
}

# For diverse/creative content
{
  "query": "abstract art",
  "provider": "pixabay", 
  "orientation": "landscape"
}

# For maximum coverage (try both)
{
  "query": "rare wildlife",
  "orientation": "landscape"
  // No provider specified = automatic fallback
}
```

## API Reference

### Video Search Query Generation

#### POST `/v1/ai/video-search/generate-queries`

Generate timed video search queries from script content using AI.

**Request Body:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `script` | string | **required** | Script text to analyze (1-2000 chars) |
| `segment_duration` | float | `3.0` | Target duration per video segment (1.0-10.0s) |
| `provider` | string | `"auto"` | AI provider: `"openai"`, `"groq"`, or `"auto"` |
| `language` | string | `"en"` | Language code (currently only 'en' supported) |

**Example Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "queries": [
      {
        "query": "ocean waves",
        "start_time": 0.0,
        "end_time": 3.0,
        "duration": 3.0,
        "visual_concept": "Ocean waves crashing on shore"
      },
      {
        "query": "whale migration",
        "start_time": 3.0,
        "end_time": 6.0,
        "duration": 3.0,
        "visual_concept": "Whales swimming in deep ocean"
      },
      {
        "query": "seahorse coral reef",
        "start_time": 6.0,
        "end_time": 9.0,
        "duration": 3.0,
        "visual_concept": "Seahorses in colorful coral reef"
      }
    ],
    "total_duration": 9.0,
    "total_segments": 3,
    "provider_used": "groq"
  }
}
```

#### GET `/v1/ai/video-search/generate-queries/{job_id}`

Get the status and results of a video search query generation job.

### Stock Video Search

#### POST `/v1/ai/video-search/stock-videos`

Search for high-quality stock videos using the Pexels API.

**Request Body:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | **required** | Search query (1-100 chars) |
| `per_page` | integer | `15` | Results per search (1-80) |
| `min_duration` | integer | `5` | Minimum video duration in seconds |
| `max_duration` | integer | `60` | Maximum video duration in seconds |
| `orientation` | string | `"landscape"` | Video orientation |
| `size` | string | `"large"` | Video size preference |

**Orientation Options:**
- `"landscape"`: 16:9 aspect ratio (1920x1080)
- `"portrait"`: 9:16 aspect ratio (1080x1920)
- `"square"`: 1:1 aspect ratio (1080x1080)

**Size Options:**
- `"large"`: HD quality (preferred for production)
- `"medium"`: Standard quality
- `"small"`: Lower resolution (faster downloads)

**Example Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "videos": [
      {
        "id": 123456,
        "url": "https://www.pexels.com/video/ocean-waves-123456/",
        "download_url": "https://player.vimeo.com/external/123456.hd.mp4",
        "duration": 15,
        "width": 1920,
        "height": 1080,
        "file_size": 5242880,
        "quality": "hd",
        "file_type": "mp4",
        "tags": ["ocean", "waves", "nature", "water"]
      }
    ],
    "total_results": 42,
    "page": 1,
    "per_page": 15,
    "query_used": "ocean waves"
  }
}
```

#### GET `/v1/ai/video-search/stock-videos/{job_id}`

Get the status and results of a stock video search job.

## Advanced Usage

### Script Analysis for Multiple Segments

```json
{
  "script": "Space exploration has revealed incredible discoveries. From the vast emptiness of deep space to the scorching surface of Mars, each planet tells a unique story. Saturn's rings dance in cosmic harmony while Jupiter's storms rage for centuries.",
  "segment_duration": 4.0,
  "provider": "openai"
}
```

**Generated Queries:**
- `0.0-4.0s`: "deep space stars"
- `4.0-8.0s`: "Mars planet surface"
- `8.0-12.0s`: "Saturn rings orbit"
- `12.0-16.0s`: "Jupiter storm clouds"

### High-Quality Video Search

```json
{
  "query": "professional chef cooking",
  "orientation": "landscape",
  "size": "large",
  "min_duration": 10,
  "max_duration": 20,
  "per_page": 20
}
```

### Portrait Mode for Social Media

```json
{
  "query": "fitness workout gym",
  "orientation": "portrait",
  "size": "large",
  "min_duration": 8,
  "max_duration": 15
}
```

## AI Query Generation Guidelines

### Visual Concreteness Rules

The AI follows strict guidelines to ensure search queries are visually searchable:

**✅ Good Examples:**
- "ocean waves crashing"
- "chef preparing food"
- "mountain sunrise landscape"
- "children playing playground"

**❌ Bad Examples:**
- "emotional moment" (too abstract)
- "successful business" (not visual)
- "feeling happy" (internal state)
- "important decision" (not concrete)

### Timing Optimization

- **Short Segments (2-3s)**: Fast-paced content, music videos
- **Medium Segments (3-5s)**: Standard talking head content
- **Long Segments (5-8s)**: Detailed explanations, slower pace

### Provider Selection

- **Groq (Llama3-70b)**: Fast generation, excellent for video search
- **OpenAI (GPT-4o)**: Slightly slower but very reliable
- **Auto**: Prefers Groq for speed, falls back to OpenAI

## Best Practices

### Script Preparation

1. **Use Visual Language**: Focus on concrete, observable elements
2. **Avoid Abstractions**: Replace emotions with visual expressions
3. **Be Specific**: "golden retriever running" > "happy dog"
4. **Consider Timing**: Match script pace to desired video segments

### Search Query Optimization

1. **2-3 Word Queries**: Most effective for stock video search
2. **Action Words**: "running", "swimming", "cooking" work well
3. **Descriptive Adjectives**: "sunset", "stormy", "peaceful"
4. **Avoid Complex Phrases**: Keep queries simple and direct

### Video Selection

1. **Check Duration**: Ensure videos meet your minimum length needs
2. **Preview Quality**: Download URLs provide direct access
3. **Consider Licensing**: Pexels videos are free for commercial use
4. **Aspect Ratio**: Match your target platform requirements

## Integration Examples

### Python: Complete Workflow

```python
import requests
import time

class VideoSearchClient:
    def __init__(self, api_key, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def generate_queries(self, script, segment_duration=3.0):
        response = requests.post(
            f"{self.base_url}/v1/ai/video-search/generate-queries",
            headers=self.headers,
            json={
                "script": script,
                "segment_duration": segment_duration
            }
        )
        job_id = response.json()["job_id"]
        
        # Poll for completion
        while True:
            status = requests.get(
                f"{self.base_url}/v1/ai/video-search/generate-queries/{job_id}",
                headers=self.headers
            ).json()
            
            if status["status"] == "completed":
                return status["result"]["queries"]
            elif status["status"] == "failed":
                raise Exception(status["error"])
            
            time.sleep(2)
    
    def search_videos(self, query, orientation="landscape"):
        response = requests.post(
            f"{self.base_url}/v1/ai/video-search/stock-videos",
            headers=self.headers,
            json={
                "query": query,
                "orientation": orientation,
                "per_page": 10
            }
        )
        job_id = response.json()["job_id"]
        
        # Poll for completion
        while True:
            status = requests.get(
                f"{self.base_url}/v1/ai/video-search/stock-videos/{job_id}",
                headers=self.headers
            ).json()
            
            if status["status"] == "completed":
                return status["result"]["videos"]
            elif status["status"] == "failed":
                raise Exception(status["error"])
            
            time.sleep(2)

# Usage
client = VideoSearchClient("your_api_key")

script = "The Amazon rainforest contains incredible biodiversity. Colorful parrots fly through the canopy while jaguars hunt below."

# Generate search queries
queries = client.generate_queries(script)
print(f"Generated {len(queries)} video queries")

# Find videos for each query
for query_data in queries:
    videos = client.search_videos(query_data["query"])
    if videos:
        print(f"Found {len(videos)} videos for '{query_data['query']}'")
        print(f"Best video: {videos[0]['download_url']}")
```

### JavaScript: Automated Video Collection

```javascript
class VideoSearchAPI {
  constructor(apiKey, baseUrl = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.headers = {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    };
  }

  async generateQueries(script, segmentDuration = 3.0) {
    const response = await fetch(`${this.baseUrl}/v1/ai/video-search/generate-queries`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ script, segment_duration: segmentDuration })
    });
    
    const { job_id } = await response.json();
    
    // Poll for completion
    while (true) {
      const statusResponse = await fetch(
        `${this.baseUrl}/v1/ai/video-search/generate-queries/${job_id}`,
        { headers: { 'X-API-Key': this.apiKey } }
      );
      
      const status = await statusResponse.json();
      
      if (status.status === 'completed') {
        return status.result.queries;
      } else if (status.status === 'failed') {
        throw new Error(status.error);
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  async searchVideos(query, options = {}) {
    const searchParams = {
      query,
      orientation: 'landscape',
      per_page: 10,
      ...options
    };

    const response = await fetch(`${this.baseUrl}/v1/ai/video-search/stock-videos`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(searchParams)
    });
    
    const { job_id } = await response.json();
    
    // Poll for completion
    while (true) {
      const statusResponse = await fetch(
        `${this.baseUrl}/v1/ai/video-search/stock-videos/${job_id}`,
        { headers: { 'X-API-Key': this.apiKey } }
      );
      
      const status = await statusResponse.json();
      
      if (status.status === 'completed') {
        return status.result.videos;
      } else if (status.status === 'failed') {
        throw new Error(status.error);
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  async getVideoTimeline(script) {
    const queries = await this.generateQueries(script);
    const timeline = [];

    for (const queryData of queries) {
      const videos = await this.searchVideos(queryData.query);
      timeline.push({
        ...queryData,
        video: videos[0] || null
      });
    }

    return timeline;
  }
}

// Usage
const api = new VideoSearchAPI('your_api_key');

const script = "Technology is transforming our world. Artificial intelligence powers smart devices while robots work alongside humans in factories.";

const timeline = await api.getVideoTimeline(script);
console.log('Video Timeline:', timeline);
```

## Environment Variables

```bash
# Required for stock video search
PEXELS_API_KEY=your_pexels_api_key

# Required for AI query generation (at least one)
OPENAI_API_KEY=sk-...                      # OpenAI API key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: Custom OpenAI-compatible endpoint
OPENAI_MODEL=gpt-4o                        # Optional: Custom model name
GROQ_API_KEY=gsk_...                       # Groq API key (alternative)
GROQ_MODEL=llama3-70b-8192                 # Optional: Custom Groq model
```

## Error Handling

### Common Issues

**Missing Pexels API Key:**
```json
{
  "detail": "Pexels API key not configured"
}
```

**No Videos Found:**
```json
{
  "result": {
    "videos": [],
    "total_results": 0,
    "query_used": "very specific query"
  }
}
```

**AI Generation Failure:**
```json
{
  "status": "failed",
  "error": "Failed to generate video search queries: AI service timeout"
}
```

## Performance Notes

- **Query Generation**: 2-10 seconds depending on script length
- **Video Search**: 1-3 seconds per search
- **Concurrent Requests**: Supports multiple simultaneous searches
- **Rate Limits**: Pexels API has rate limits (check their documentation)

## Next Steps

- Combine with [AI Script Generation](ai-script-generation.md) for automated workflows
- Use in [Topic-to-Video Pipeline](footage-to-video-pipeline.md) for complete automation
- Download videos and process with [Video Processing](videos/README.md) endpoints

---

*For more examples and advanced usage, see the [examples directory](examples/).*