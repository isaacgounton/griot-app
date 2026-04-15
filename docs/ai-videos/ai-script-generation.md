# AI Script Generation

Generate engaging video scripts from topics using AI language models. Perfect for YouTube Shorts, TikTok videos, and educational content.

## Overview

The AI Script Generation service uses advanced language models to create compelling scripts optimized for short-form video content. It supports multiple AI providers with intelligent fallback and produces scripts tailored for viral engagement.

## Supported AI Providers

- **OpenAI GPT-4o**: High-quality script generation with excellent creativity
- **Groq Mixtral-8x7b**: Ultra-fast generation with competitive quality
- **Auto-Selection**: Automatically chooses the best available provider

## Quick Start

### 1. Generate Script

```bash
curl -X POST "http://localhost:8000/v1/ai/script/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "weird animal facts",
    "script_type": "facts",
    "max_duration": 45,
    "provider": "auto"
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Check Status

```bash
curl "http://localhost:8000/v1/ai/script/generate/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key"
```

**Response (when completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "script": "Weird animal facts you didn't know: Did you know that octopuses have three hearts and blue blood? Or that a shrimp's heart is in its head? Here's another mind-blowing fact: elephants can't jump, but they're excellent swimmers! And get this - a group of flamingos is called a 'flamboyance'. Nature is absolutely incredible!",
    "word_count": 52,
    "estimated_duration": 18.6,
    "provider_used": "groq",
    "model_used": "mixtral-8x7b-32768"
  },
  "error": null
}
```

## API Reference

### POST `/v1/ai/script/generate`

Create a script generation job.

#### Request Body

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | **required** | The topic or theme for script generation |
| `provider` | string | `"auto"` | AI provider: `"openai"`, `"groq"`, or `"auto"` |
| `script_type` | string | `"facts"` | Script type (see Script Types section below) |
| `max_duration` | integer | `50` | Maximum video duration (20-120 seconds) |
| `target_words` | integer | `140` | Target word count (50-300 words) |

#### Script Types

**Facts (`"facts"`)**: 
- Optimized for viral fact-based content
- List format with engaging statistics
- Perfect for YouTube Shorts and TikTok

**Story (`"story"`)**:
- Narrative-driven content with character development
- Compelling hooks and emotional engagement
- Great for storytelling channels

**Educational (`"educational"`)**:
- Step-by-step instructional content
- Clear learning objectives and takeaways
- Ideal for how-to and tutorial videos

**Motivation (`"motivation"`)**:
- Deeply inspirational and emotionally resonant content
- Authentic vulnerability and personal empowerment
- Soul-stirring wisdom that touches the heart
- Profound insights about resilience and self-worth

**Life Wisdom (`"life_wisdom"`)**:
- Profound philosophical insights about life and relationships
- Deep emotional authenticity and vulnerability
- Universal truths about love, trust, forgiveness, and healing
- Poetic language with conversational intimacy
- Perfect for content that resonates deeply with viewers

**Prayer (`"prayer"`)**:
- Spiritual content with biblical truth and divine comfort
- Faith-based encouragement addressing real struggles
- Gentle healing language for those who are hurting
- Emphasis on God's faithfulness and perfect timing

**POV (`"pov"`)**:
- Point-of-view scenarios ("POV: You are...")
- Immersive second-person perspective
- Relatable everyday situations
- Viral TikTok-style content

**Conspiracy (`"conspiracy"`)**:
- Mystery and intrigue content
- "What they don't want you to know"
- Historical mysteries and phenomena
- Engaging evidence presentation

**Life Hacks (`"life_hacks"`)**:
- Quick, actionable tips and tricks
- Problem-solving focus
- Money/time saving benefits
- "You'll wish you knew this sooner"

**Would You Rather (`"would_you_rather"`)**:
- Engaging dilemma scenarios
- Impossible choices between options
- Drives viewer engagement
- Perfect for comment interaction

**Before You Die (`"before_you_die"`)**:
- Bucket-list experiences
- Sense of urgency and FOMO
- Inspirational and aspirational
- Life-changing content

**Dark Psychology (`"dark_psychology"`)**:
- Educational psychological content
- Manipulation awareness and defense
- Body language and influence
- Ethical educational approach

**Reddit Stories (`"reddit_stories"`)**:
- Dramatic personal narratives
- Plot twists and revelations
- Relationship and workplace drama
- Engaging confession-style content

**Shower Thoughts (`"shower_thoughts"`)**:
- Mind-bending observations
- Philosophical everyday insights
- Paradoxes and thought experiments
- Simple but profound realizations

### GET `/v1/ai/script/generate/{job_id}`

Get script generation job status and results.

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `script` | string | The generated script text |
| `word_count` | integer | Number of words in the script |
| `estimated_duration` | float | Estimated speaking duration in seconds |
| `provider_used` | string | AI provider that generated the script |
| `model_used` | string | Specific AI model used |

## Advanced Usage

### Custom Duration Targeting

```json
{
  "topic": "space exploration milestones",
  "script_type": "educational",
  "max_duration": 90,
  "target_words": 250
}
```

### Provider-Specific Generation

```json
{
  "topic": "cooking tips for beginners",
  "provider": "openai",
  "script_type": "educational"
}
```

### Viral Content Optimization

```json
{
  "topic": "mind-blowing psychology facts",
  "script_type": "facts",
  "max_duration": 30,
  "target_words": 100
}
```

## Best Practices

### Topic Selection
- **Be Specific**: "weird ocean animals" > "animals"
- **Use Engaging Words**: "mind-blowing", "shocking", "incredible"
- **Target Trending Topics**: Current events, viral trends, popular subjects

### Duration Guidelines
- **TikTok/Shorts**: 15-30 seconds (40-85 words)
- **Instagram Reels**: 30-60 seconds (85-170 words)
- **YouTube Shorts**: 45-60 seconds (125-170 words)

### Content Strategy
- **Hook First 3 Seconds**: Scripts start with attention-grabbing statements
- **List Format**: Facts work best as numbered or bulleted lists
- **Call-to-Action**: Scripts can include engagement prompts

## Error Handling

### Common Errors

**Missing API Keys**:
```json
{
  "detail": "No AI provider available. Please set OPENAI_API_KEY or GROQ_API_KEY environment variable."
}
```

**Invalid Parameters**:
```json
{
  "detail": "Topic is required for script generation"
}
```

**Generation Failures**:
```json
{
  "status": "failed",
  "error": "AI service temporarily unavailable. Please try again."
}
```

## Environment Variables

```bash
# Required (at least one)
OPENAI_API_KEY=sk-...                      # OpenAI API key
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: Custom OpenAI-compatible endpoint
OPENAI_MODEL=gpt-4o                        # Optional: Custom model name
GROQ_API_KEY=gsk_...                       # Groq API key (alternative)
GROQ_MODEL=mixtral-8x7b-32768              # Optional: Custom Groq model

# Optional
LOG_LEVEL=INFO                             # Logging verbosity
```

## Integration Examples

### Python Client

```python
import requests
import time

def generate_script(topic, api_key):
    # Create job
    response = requests.post(
        "http://localhost:8000/v1/ai/script/generate",
        headers={"X-API-Key": api_key},
        json={"topic": topic, "script_type": "facts"}
    )
    job_id = response.json()["job_id"]
    
    # Poll for completion
    while True:
        status_response = requests.get(
            f"http://localhost:8000/v1/ai/script/generate/{job_id}",
            headers={"X-API-Key": api_key}
        )
        status_data = status_response.json()
        
        if status_data["status"] == "completed":
            return status_data["result"]["script"]
        elif status_data["status"] == "failed":
            raise Exception(status_data["error"])
        
        time.sleep(2)

script = generate_script("amazing space facts", "your_api_key")
print(script)
```

### JavaScript/Node.js

```javascript
async function generateScript(topic, apiKey) {
  // Create job
  const response = await fetch('http://localhost:8000/v1/ai/script/generate', {
    method: 'POST',
    headers: {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ topic, script_type: 'facts' })
  });
  
  const { job_id } = await response.json();
  
  // Poll for completion
  while (true) {
    const statusResponse = await fetch(
      `http://localhost:8000/v1/ai/script/generate/${job_id}`,
      { headers: { 'X-API-Key': apiKey } }
    );
    
    const statusData = await statusResponse.json();
    
    if (statusData.status === 'completed') {
      return statusData.result.script;
    } else if (statusData.status === 'failed') {
      throw new Error(statusData.error);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

const script = await generateScript('incredible technology facts', 'your_api_key');
console.log(script);
```

## Performance Notes

- **Groq**: Ultra-fast generation (~2-5 seconds)
- **OpenAI**: High-quality results (~5-15 seconds)
- **Auto-selection**: Chooses Groq for speed when available
- **Concurrent Jobs**: Supports multiple simultaneous generations

## Next Steps

- Use generated scripts with [Topic-to-Video Pipeline](footage-to-video-pipeline.md) for complete automation
- Convert scripts to audio with [Text-to-Speech](audio/speech.md)
- Add captions to videos with [Video Captions](videos/add_captions.md)

---

*For more examples and advanced usage, see the [examples directory](examples/).*