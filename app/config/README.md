# Configuration Directory

This directory contains configuration files for the Griot application.

## Files

### `caption_styles.json`
Contains optimal caption parameters and styling configurations for video generation.

**Moved from:** `optimal_caption_params.json` (project root)  
**New location:** `app/config/caption_styles.json`

**Usage:**
```python
from app.config import (
    get_caption_style,
    get_available_caption_styles,
    get_caption_best_practices
)

# Get a specific caption style
style = get_caption_style("viral_bounce")

# List all available styles  
styles = get_available_caption_styles()

# Get best practices guidelines
practices = get_caption_best_practices()
```

## Adding New Configuration Files

When adding new configuration files to this directory:

1. Place JSON/YAML config files directly in this directory
2. Add corresponding loader functions to `__init__.py`
3. Update this README with usage examples
4. Document in the main CLAUDE.md file if it's a major configuration

## Configuration Best Practices

- Use descriptive filenames (e.g., `caption_styles.json` instead of `optimal_caption_params.json`)
- Provide type-safe loader functions in `__init__.py`
- Include validation and error handling in loader functions
- Document configuration schemas and examples