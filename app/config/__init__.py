"""
Configuration module for Griot application.
Contains configuration files and utilities for loading settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

# Get the directory where this config module is located
CONFIG_DIR = Path(__file__).parent

def load_caption_styles() -> Dict[str, Any]:
    """
    Load caption styles configuration from caption_styles.json.
    
    Returns:
        Dict containing caption style configurations
    """
    caption_styles_path = CONFIG_DIR / "caption_styles.json"
    
    if not caption_styles_path.exists():
        raise FileNotFoundError(f"Caption styles configuration not found at {caption_styles_path}")
    
    with open(caption_styles_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_caption_style(style_name: str) -> Dict[str, Any]:
    """
    Get a specific caption style configuration.
    
    Args:
        style_name: Name of the caption style to retrieve
        
    Returns:
        Dict containing the caption style configuration
        
    Raises:
        KeyError: If the style name is not found
    """
    styles = load_caption_styles()
    
    if style_name in styles.get("optimal_caption_parameters_2025", {}):
        return styles["optimal_caption_parameters_2025"][style_name]
    
    raise KeyError(f"Caption style '{style_name}' not found")

def get_available_caption_styles() -> list[str]:
    """
    Get list of available caption style names.
    
    Returns:
        List of available caption style names
    """
    styles = load_caption_styles()
    return list(styles.get("optimal_caption_parameters_2025", {}).keys())

def get_caption_best_practices() -> Dict[str, Any]:
    """
    Get caption best practices configuration.
    
    Returns:
        Dict containing best practices guidelines
    """
    styles = load_caption_styles()
    return styles.get("best_practices_2025", {})

def get_caption_style_preset(style_name: str) -> Dict[str, Any]:
    """
    Get a caption style preset with frontend-compatible parameters.
    
    Args:
        style_name: Name of the caption style to retrieve
        
    Returns:
        Dict containing preset values for caption_color, font_size, font_family, words_per_line
        
    Raises:
        KeyError: If the style name is not found
    """
    styles = load_caption_styles()
    
    presets = styles.get("caption_style_presets", {})
    if style_name in presets:
        return presets[style_name]
    
    raise KeyError(f"Caption style preset '{style_name}' not found")

def get_available_caption_style_presets() -> list[str]:
    """
    Get list of available caption style preset names.
    
    Returns:
        List of available caption style preset names
    """
    styles = load_caption_styles()
    return list(styles.get("caption_style_presets", {}).keys())

def apply_caption_style_preset(style_name: str, current_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply a caption style preset to current parameters, preserving user overrides.
    
    Args:
        style_name: Name of the caption style preset to apply
        current_params: Current caption parameters that may contain user overrides
        
    Returns:
        Dict with preset values applied, preserving explicit user overrides
    """
    try:
        preset = get_caption_style_preset(style_name)
        
        # Create a copy of current params
        result = current_params.copy()
        
        # Apply preset values only if not explicitly set by user
        for key, value in preset.items():
            if key not in result or result[key] is None:
                result[key] = value
        
        return result
        
    except KeyError:
        # If preset not found, return current params unchanged
        return current_params

def get_style_recommendations(content_type: str = "youtube_shorts") -> list[str]:
    """
    Get style recommendations for specific content types.
    
    Args:
        content_type: Type of content ('tiktok_viral', 'youtube_shorts', 'instagram_reels', 
                     'professional', 'educational', 'entertainment')
        
    Returns:
        List of recommended caption style names for the content type
    """
    best_practices = get_caption_best_practices()
    recommendations = best_practices.get("style_recommendations", {})
    
    if content_type in recommendations:
        # Split comma-separated string into list
        return [style.strip() for style in recommendations[content_type].split(",")]
    
    # Default recommendations
    return ["viral_bounce", "highlight", "modern_neon"]