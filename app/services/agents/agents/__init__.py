"""
Individual agents module.
Contains standalone agents for specific tasks.
"""

from .finance_agent import get_finance_agent
from .research_agent import get_research_agent
from .social_media_agent import get_social_media_agent
from .sage import get_sage
from .scholar import get_scholar
from .media_agent import get_media_agent

__all__ = [
    "get_finance_agent",
    "get_research_agent",
    "get_social_media_agent",
    "get_sage",
    "get_scholar",
    "get_media_agent",
]

