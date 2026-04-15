"""
Text generation and processing services.
"""

from .script_generator import AIScriptGenerator
from .image_prompt_generator import ImagePromptGenerator
from .topic_discovery_service import TopicDiscoveryService

# Create service instances
script_generator = AIScriptGenerator()
image_prompt_generator = ImagePromptGenerator()
topic_discovery_service = TopicDiscoveryService()

__all__ = [
    "script_generator",
    "image_prompt_generator",
    "topic_discovery_service",
    "AIScriptGenerator",
    "ImagePromptGenerator",
    "TopicDiscoveryService"
]