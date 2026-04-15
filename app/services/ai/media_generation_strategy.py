"""
Base strategy interface for media generation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class MediaGenerationStrategy(ABC):
    """Abstract base class for media generation strategies."""
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the human-readable name of this strategy."""
        pass
    
    @abstractmethod
    async def generate_media_segments(
        self, 
        video_queries: List[Dict], 
        orientation: str,
        params: Dict[str, Any]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Generate media segments based on video queries.
        
        Args:
            video_queries: List of query dictionaries with 'query', 'start_time', 'end_time', 'duration'
            orientation: Video orientation ('landscape', 'portrait', 'square')
            params: Additional parameters for generation
            
        Returns:
            List of media segment dictionaries or None for failed generations
        """
        pass