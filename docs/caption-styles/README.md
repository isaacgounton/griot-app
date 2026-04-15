# Caption Styles Configuration

Caption styling parameters are stored in `app/config/caption_styles.json`. This file contains pre-configured styles for different use cases, best practices guidelines, and optimal parameters for various video types.

## Configuration File Location

```
app/config/caption_styles.json
```

## Configuration Structure

### Optimal Caption Parameters

Pre-configured styles for different use cases:

```json
{
  "optimal_params": {
    "viral_bounce": {
      "name": "Viral Bounce",
      "description": "Bouncy animation with word highlights",
      "font_size": 55,
      "font_name": "Montserrat-ExtraBold",
      "position": "bottom",
      "y_offset": 150,
      "word_highlight": true,
      "highlight_color": "#FFD700",
      "animation": "bounce",
      "animation_duration": 0.15,
      "background": "blur",
      "background_color": "#000000",
      "background_opacity": 0.5,
      "text_color": "#FFFFFF",
      "use_stroke": false,
      "stroke_color": "#000000",
      "stroke_width": 2
    },
    "standard_bottom": {
      "name": "Standard Bottom",
      "description": "Classic bottom-centered captions",
      "font_size": 48,
      "font_name": "Roboto-Regular",
      "position": "bottom",
      "y_offset": 100,
      "word_highlight": false,
      "background": "solid",
      "background_color": "#000000",
      "background_opacity": 0.7,
      "text_color": "#FFFFFF",
      "use_stroke": false
    },
    "mobile_optimized": {
      "name": "Mobile Optimized",
      "description": "Optimized for vertical mobile viewing",
      "font_size": 60,
      "font_name": "OpenSans-SemiBold",
      "position": "bottom",
      "y_offset": 180,
      "background": "blur",
      "background_opacity": 0.6,
      "text_color": "#FFFFFF",
      "max_line_length": 20
    }
  }
}
```

### Best Practices Guidelines

Guidelines for creating effective captions:

```json
{
  "best_practices": {
    "font_size": {
      "portrait": {
        "min": 50,
        "max": 70,
        "recommended": 60,
        "note": "Larger fonts for 9:16 vertical videos"
      },
      "landscape": {
        "min": 40,
        "max": 55,
        "recommended": 48,
        "note": "Smaller fonts for 16:9 horizontal videos"
      },
      "square": {
        "min": 45,
        "max": 60,
        "recommended": 52,
        "note": "Medium fonts for 1:1 square videos"
      }
    },
    "positioning": {
      "safe_zones": {
        "portrait": {
          "top": 200,
          "bottom": 200,
          "sides": 100
        },
        "landscape": {
          "top": 100,
          "bottom": 100,
          "sides": 200
        }
      },
      "recommendation": "Keep captions in bottom third for mobile"
    },
    "readability": {
      "max_characters_per_line": 20,
      "max_lines": 2,
      "min_duration_per_word": 0.5,
      "recommended_duration_per_line": 3.0
    }
  }
}
```

### Viral Content Tips

Guidelines for creating engaging captions:

```json
{
  "viral_content_tips": {
    "attention_grabbing": {
      "use_emoji": true,
      "bold_keywords": true,
      "color_highlights": true,
      "bounce_animation": true
    },
    "timing": {
      "sync_with_audio": true,
      "word_pacing": "natural",
      "pause_duration": 0.3,
      "emphasis_duration": 0.5
    },
    "styling": {
      "font_weights": ["Bold", "ExtraBold", "Black"],
      "colors": ["#FFFFFF", "#FFD700", "#FF6B6B"],
      "effects": ["bounce", "glow", "scale"]
    },
    "engagement": {
      "call_to_action": "Use contrasting colors for CTAs",
      "hashtags": "Highlight hashtags with special color",
      "keywords": "Emphasize key words with animations"
    }
  }
}
```

## Available Styles

### Viral Bounce

**Best For:** TikTok, Instagram Reels, viral content

**Characteristics:**
- Bouncy animation on word transitions
- Gold color highlighting on current word
- Blurred background for readability
- Large, bold font (55pt)
- Bottom positioning with 150px offset

**Parameters:**
```json
{
  "font_size": 55,
  "font_name": "Montserrat-ExtraBold",
  "animation": "bounce",
  "animation_duration": 0.15,
  "word_highlight": true,
  "highlight_color": "#FFD700",
  "background": "blur",
  "background_opacity": 0.5
}
```

### Standard Bottom

**Best For:** YouTube videos, educational content, documentaries

**Characteristics:**
- Classic bottom-centered placement
- Solid black background
- Clean, readable font (48pt)
- No animations or highlights
- Traditional caption appearance

**Parameters:**
```json
{
  "font_size": 48,
  "font_name": "Roboto-Regular",
  "position": "bottom",
  "y_offset": 100,
  "background": "solid",
  "background_opacity": 0.7
}
```

### Mobile Optimized

**Best For:** Vertical videos, social media stories

**Characteristics:**
- Larger font for mobile screens (60pt)
- Optimized for 9:16 aspect ratio
- Blurred background
- Maximum 20 characters per line
- Higher positioning for better visibility

**Parameters:**
```json
{
  "font_size": 60,
  "font_name": "OpenSans-SemiBold",
  "position": "bottom",
  "y_offset": 180,
  "max_line_length": 20,
  "background": "blur"
}
```

### Typewriter

**Best For:** Narrative content, storytelling, tutorials

**Characteristics:**
- Word-by-word appearance
- Typewriter animation effect
- Monospace font aesthetic
- Color transitions on new words
- Smooth animations

**Parameters:**
```json
{
  "font_size": 50,
  "font_name": "CourierNew-Bold",
  "animation": "typewriter",
  "animation_duration": 0.1,
  "background": "none",
  "text_color": "#00FF00"
}
```

### Fade In

**Best For:** Elegant content, luxury brands, calm videos

**Characteristics:**
- Smooth fade-in transitions
- Subtle animations
- Elegant appearance
- Professional look
- Less distracting

**Parameters:**
```json
{
  "font_size": 52,
  "font_name": "PlayfairDisplay-Bold",
  "animation": "fade_in",
  "animation_duration": 0.3,
  "background": "blur",
  "background_opacity": 0.4
}
```

## Usage

### API Usage

Specify caption style when creating videos:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/scenes-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [...],
    "add_captions": true,
    "caption_style": "viral_bounce"
  }'
```

### Programmatic Usage

```python
from app.config import get_caption_style, get_available_caption_styles

# Get a specific caption style
viral_style = get_caption_style("viral_bounce")
print(viral_style["font_size"])  # 55
print(viral_style["animation"])  # "bounce"

# List all available styles
available_styles = get_available_caption_styles()
print(available_styles)  # ["viral_bounce", "standard_bottom", "mobile_optimized", ...]
```

## Font Management

### Available Fonts

Fonts are stored in `/app/static/fonts/`:

- **Montserrat-ExtraBold**: Modern, bold sans-serif
- **Roboto-Regular**: Clean, readable sans-serif
- **OpenSans-SemiBold**: Friendly, open sans-serif
- **PlayfairDisplay-Bold**: Elegant serif font
- **CourierNew-Bold**: Monospace typewriter font

### Adding Custom Fonts

1. Add TTF font file to `/app/static/fonts/`
2. Update `caption_styles.json` with new font name
3. Reference font name in caption style parameters
4. Restart application

Example:
```json
{
  "custom_style": {
    "font_name": "YourCustomFont-Regular",
    "font_size": 50
  }
}
```

## Custom Styles

### Creating Custom Styles

Add custom styles to `caption_styles.json`:

```json
{
  "optimal_params": {
    "my_custom_style": {
      "name": "My Custom Style",
      "description": "Custom caption style for specific use case",
      "font_size": 58,
      "font_name": "Montserrat-Bold",
      "position": "bottom",
      "y_offset": 160,
      "word_highlight": true,
      "highlight_color": "#FF6B6B",
      "animation": "bounce",
      "animation_duration": 0.2,
      "background": "blur",
      "background_opacity": 0.55,
      "text_color": "#FFFFFF",
      "use_stroke": true,
      "stroke_color": "#000000",
      "stroke_width": 3
    }
  }
}
```

### Style Parameters Reference

| Parameter | Type | Description | Values |
|-----------|------|-------------|--------|
| `font_size` | integer | Font size in points | 40-70 |
| `font_name` | string | Font file name (without .ttf) | Any in /static/fonts/ |
| `position` | string | Vertical position | "top", "center", "bottom" |
| `y_offset` | integer | Pixel offset from position | 0-300 |
| `word_highlight` | boolean | Highlight current word | true, false |
| `highlight_color` | string | Color for highlighted word | Hex color code |
| `animation` | string | Animation type | "bounce", "typewriter", "fade_in", "none" |
| `animation_duration` | float | Animation duration in seconds | 0.0-1.0 |
| `background` | string | Background type | "solid", "blur", "none" |
| `background_color` | string | Background color | Hex color code |
| `background_opacity` | float | Background opacity | 0.0-1.0 |
| `text_color` | string | Text color | Hex color code |
| `use_stroke` | boolean | Add text stroke/outline | true, false |
| `stroke_color` | string | Stroke color | Hex color code |
| `stroke_width` | integer | Stroke width in pixels | 1-5 |
| `max_line_length` | integer | Max characters per line | 10-30 |

## Platform-Specific Recommendations

### TikTok/Instagram Reels

```json
{
  "platform": "tiktok",
  "style": "viral_bounce",
  "settings": {
    "font_size": 60,
    "use_emoji": true,
    "animation": "bounce",
    "max_line_length": 18
  }
}
```

### YouTube Shorts

```json
{
  "platform": "youtube_shorts",
  "style": "viral_bounce",
  "settings": {
    "font_size": 58,
    "use_emoji": false,
    "animation": "bounce",
    "background": "blur"
  }
}
```

### YouTube Standard

```json
{
  "platform": "youtube_standard",
  "style": "standard_bottom",
  "settings": {
    "font_size": 44,
    "position": "bottom",
    "background": "solid",
    "background_opacity": 0.8
  }
}
```

### LinkedIn

```json
{
  "platform": "linkedin",
  "style": "mobile_optimized",
  "settings": {
    "font_size": 52,
    "animation": "fade_in",
    "professional": true
  }
}
```

## Troubleshooting

### Font Not Found

**Problem:** Caption generation fails with font error

**Solutions:**
1. Verify font file exists in `/app/static/fonts/`
2. Check font name matches exactly (case-sensitive)
3. Ensure font is valid TTF format
4. Restart application after adding fonts

### Style Not Applied

**Problem:** Captions don't appear with expected style

**Solutions:**
1. Verify style name exists in `caption_styles.json`
2. Check JSON syntax is valid
3. Ensure all required parameters are present
4. Check application logs for errors

### Positioning Issues

**Problem:** Captions appear off-screen or cut off

**Solutions:**
1. Adjust `y_offset` parameter
2. Check video resolution matches style
3. Verify safe zone margins
4. Test with different `position` values

## Best Practices

### For Mobile Content

1. **Use Larger Fonts**: 55-60pt for better readability
2. **Keep Text Short**: Max 18-20 characters per line
3. **Use Blurred Background**: Improves readability
4. **Position Carefully**: Bottom 1/3 of screen
5. **Test on Device**: Preview on actual mobile device

### For Viral Content

1. **Use Animations**: Bounce or typewriter effects
2. **Highlight Keywords**: Color emphasis on important words
3. **Add Emojis**: Visual interest and engagement
4. **Keep Pace Natural**: Sync with speech rhythm
5. **Test A/B Variations**: Try different styles

### For Educational Content

1. **Keep It Simple**: Standard bottom style
2. **Use Clear Fonts**: Roboto or OpenSans
4. **Ensure Readability**: Solid background
5. **Perfect Timing**: Sync precisely with audio
6. **Minimize Distractions**: Avoid excessive animations

## Resources

- **Font Directory**: `/app/static/fonts/`
- **Config File**: `/app/config/caption_styles.json`
- **Caption Utility**: `/app/utils/video/captions.py`
- **Main Docs**: [../README.md](../README.md)

---

*Last updated: January 2025*
