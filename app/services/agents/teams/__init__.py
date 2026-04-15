"""
Teams module.
Contains team agents that work together to accomplish complex tasks.
"""

from .content_team import get_content_team
from .news_agency_team import get_news_agency_team

__all__ = [
    "get_content_team",
    "get_news_agency_team",
]

