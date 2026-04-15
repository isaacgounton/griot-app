"""Lazy strategy registry wrapping existing strategy classes."""
from app.services.ai.media_generation_strategy import MediaGenerationStrategy

_registry: dict[str, MediaGenerationStrategy] = {}


def get_strategy(key: str) -> MediaGenerationStrategy:
    """Get a strategy instance by key. Lazy-imports to avoid circular deps."""
    if key not in _registry:
        _registry[key] = _create_strategy(key)
    return _registry[key]


def _create_strategy(key: str) -> MediaGenerationStrategy:
    if key == 'stock_video':
        from app.services.ai.strategies.stock_video_strategy import StockVideoStrategy
        return StockVideoStrategy()
    elif key == 'stock_image':
        from app.services.ai.strategies.stock_image_strategy import StockImageStrategy
        return StockImageStrategy()
    elif key == 'ai_video':
        from app.services.ai.strategies.ai_video_strategy import AIVideoStrategy
        return AIVideoStrategy()
    elif key == 'ai_image':
        from app.services.ai.strategies.ai_image_strategy import AIImageStrategy
        return AIImageStrategy()
    else:
        raise ValueError(f"Unknown media strategy: '{key}'")
