"""
AI Service Health Monitoring Utilities
"""
import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AIServiceHealthChecker:
    """Monitor health status of AI services."""

    def __init__(self):
        self.services_status = {}

    def check_pollinations_health(self) -> Dict[str, Any]:
        """Check Pollinations service health."""
        try:
            pollinations_key = os.getenv('POLLINATIONS_API_KEY')
            base_url = os.getenv('POLLINATIONS_BASE_URL', 'https://text.pollinations.ai')
            model = os.getenv('POLLINATIONS_MODEL')

            return {
                'service': 'Pollinations',
                'available': bool(pollinations_key and model),
                'api_key_configured': bool(pollinations_key),
                'model_configured': bool(model),
                'model': model or 'not_configured',
                'base_url': base_url,
            }
        except Exception as e:
            logger.error(f"Error checking Pollinations health: {e}")
            return {'service': 'Pollinations', 'available': False, 'error': str(e)}

    def check_openai_health(self) -> Dict[str, Any]:
        """Check OpenAI service health."""
        try:
            openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
            base_url = os.getenv('OPENAI_BASE_URL')

            return {
                'service': 'OpenAI',
                'available': bool(openai_key),
                'api_key_configured': bool(openai_key),
                'custom_base_url': bool(base_url),
                'base_url': base_url if base_url else 'https://api.openai.com/v1',
            }
        except Exception as e:
            logger.error(f"Error checking OpenAI health: {e}")
            return {'service': 'OpenAI', 'available': False, 'error': str(e)}

    def check_groq_health(self) -> Dict[str, Any]:
        """Check Groq service health."""
        try:
            groq_key = os.getenv('GROQ_API_KEY')
            base_url = os.getenv('GROQ_BASE_URL')
            model = os.getenv('GROQ_MODEL', 'llama3-70b-8192')

            return {
                'service': 'Groq',
                'available': bool(groq_key and len(groq_key) > 30),
                'api_key_configured': bool(groq_key),
                'key_length_valid': bool(groq_key and len(groq_key) > 30),
                'model': model,
                'custom_base_url': bool(base_url),
                'base_url': base_url if base_url else 'https://api.groq.com/openai/v1',
            }
        except Exception as e:
            logger.error(f"Error checking Groq health: {e}")
            return {'service': 'Groq', 'available': False, 'error': str(e)}

    def check_together_ai_health(self) -> Dict[str, Any]:
        """Check Together AI service health."""
        try:
            together_key = os.getenv('TOGETHER_API_KEY')
            model = os.getenv('TOGETHER_DEFAULT_MODEL', 'black-forest-labs/FLUX.1-schnell')

            return {
                'service': 'Together AI',
                'available': bool(together_key),
                'api_key_configured': bool(together_key),
                'default_model': model,
                'max_rps': os.getenv('TOGETHER_MAX_RPS', '2'),
                'max_concurrent': os.getenv('TOGETHER_MAX_CONCURRENT', '3'),
            }
        except Exception as e:
            logger.error(f"Error checking Together AI health: {e}")
            return {'service': 'Together AI', 'available': False, 'error': str(e)}

    def get_all_service_status(self) -> Dict[str, Any]:
        """Get health status of all AI services."""
        try:
            services = {
                'pollinations': self.check_pollinations_health(),
                'openai': self.check_openai_health(),
                'groq': self.check_groq_health(),
                'together_ai': self.check_together_ai_health(),
            }

            return {
                'timestamp': int(time.time()),
                'services': services,
                'summary': {
                    'total_services': len(services),
                    'available_services': sum(1 for status in services.values() if status['available']),
                    'primary_provider': self._get_primary_provider(services),
                }
            }
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {'error': str(e), 'timestamp': int(time.time())}

    def _get_primary_provider(self, services: Dict[str, Dict[str, Any]]) -> str:
        """Determine the primary provider based on availability and priority."""
        # Priority order: Pollinations > OpenAI > Groq > Together AI
        priority_order = ['pollinations', 'openai', 'groq', 'together_ai']

        for provider in priority_order:
            if services.get(provider, {}).get('available', False):
                return provider

        return 'none'


# Global instance
ai_health_checker = AIServiceHealthChecker()
