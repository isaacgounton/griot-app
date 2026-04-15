"""
Agent selector and factory for Agno integration.
Provides a centralized way to create and manage different types of agents.
"""

import logging
from enum import Enum
from typing import List, Optional

from agno.agent import Agent

from app.services.agents.agents import (
    get_finance_agent,
    get_research_agent,
    get_social_media_agent,
    get_sage,
    get_scholar,
    get_media_agent,
)
from app.services.agents.teams import (
    get_content_team,
    get_news_agency_team,
)
from app.services.agents.workflows import (
    get_blog_generator_workflow,
)

logger = logging.getLogger(__name__)

_agent_db = None


def _get_agent_db():
    """Get or create a shared AsyncPostgresDb instance for agent session storage."""
    global _agent_db
    if _agent_db is not None:
        return _agent_db
    try:
        from agno.db.postgres import AsyncPostgresDb
        from app.database import get_async_db_url
        _agent_db = AsyncPostgresDb(
            db_url=get_async_db_url(),
            session_table="agno_agent_sessions",
        )
        return _agent_db
    except Exception as e:
        logger.warning(f"Failed to create AsyncPostgresDb for agent storage: {e}")
        return None


class AgentType(Enum):
    """Available agent types"""
    # General
    CHAT = "chat"

    # Individual Agents
    RESEARCH_AGENT = "research_agent"
    SOCIAL_MEDIA_AGENT = "social_media_agent"
    FINANCE_AGENT = "finance_agent"
    SAGE = "sage"
    SCHOLAR = "scholar"
    MEDIA_AGENT = "media_agent"

    # Teams
    CONTENT_TEAM = "content_team"
    NEWS_AGENCY_TEAM = "news_agency_team"

    # Workflows
    BLOG_GENERATOR = "blog_generator"


def get_available_agents() -> List[dict]:
    """Returns a list of all available agents with their details."""
    return [
        # Individual Agents
        {
            "id": AgentType.RESEARCH_AGENT.value,
            "name": "Research Agent",
            "type": "agent",
            "description": "Elite investigative journalist with deep research and web search capabilities",
            "capabilities": ["web_search", "research"]
        },
        {
            "id": AgentType.SOCIAL_MEDIA_AGENT.value,
            "name": "Social Media Analyst",
            "type": "agent",
            "description": "Analyzes social media sentiment and trends for brand intelligence",
            "capabilities": ["sentiment_analysis", "trend_tracking"]
        },
        {
            "id": AgentType.FINANCE_AGENT.value,
            "name": "Finance Agent",
            "type": "agent",
            "description": "Get financial information and market data",
            "capabilities": ["financial_data", "market_analysis"]
        },
        {
            "id": AgentType.SAGE.value,
            "name": "Sage",
            "type": "agent",
            "description": "Advanced Knowledge Agent with access to knowledge base and web search capabilities",
            "capabilities": ["knowledge_base", "web_search"]
        },
        {
            "id": AgentType.SCHOLAR.value,
            "name": "Scholar",
            "type": "agent",
            "description": "Precision answer engine delivering context-rich, engaging responses from web search",
            "capabilities": ["web_search", "research"]
        },
        {
            "id": AgentType.MEDIA_AGENT.value,
            "name": "Media Agent",
            "type": "agent",
            "description": "AI-powered content creation for short-form videos (TikTok, Instagram, YouTube Shorts)",
            "capabilities": ["video_generation", "social_media_posting"]
        },
        # Teams
        {
            "id": AgentType.CONTENT_TEAM.value,
            "name": "Content Team",
            "type": "team",
            "description": "Collaborative team for high-quality content creation",
            "capabilities": ["research", "writing"]
        },
        {
            "id": AgentType.NEWS_AGENCY_TEAM.value,
            "name": "News Agency Team",
            "type": "team",
            "description": "Professional news production team for high-quality journalism",
            "capabilities": ["journalism", "writing"]
        },
        # Workflows
        {
            "id": AgentType.BLOG_GENERATOR.value,
            "name": "Blog Generator",
            "type": "workflow",
            "description": "Multi-stage blog post generation with research and writing",
            "capabilities": ["blog_writing", "content_creation"]
        }
    ]


def get_agent(
    agent_type: AgentType,
    model_id: str = "gpt-5-mini",
    provider: Optional[str] = None,
    settings: Optional[dict] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
):
    """
    Factory function to get an agent/team/workflow instance.

    Args:
        agent_type: The type of agent to create
        model_id: The model ID to use (default: gpt-4-mini)
        provider: Optional AnyLLM provider name
        settings: Optional session settings with generation parameters
        user_id: User ID for personalization
        session_id: Session ID for conversation continuity
        debug_mode: Whether to enable debug logging

    Returns:
        Agent, Team, or Workflow instance

    Raises:
        ValueError: If agent_type is not supported
    """
    agent_db = _get_agent_db()

    # Individual Agents
    if agent_type == AgentType.RESEARCH_AGENT:
        return get_research_agent(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    elif agent_type == AgentType.SOCIAL_MEDIA_AGENT:
        return get_social_media_agent(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    elif agent_type == AgentType.FINANCE_AGENT:
        return get_finance_agent(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    elif agent_type == AgentType.SAGE:
        return get_sage(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    elif agent_type == AgentType.SCHOLAR:
        return get_scholar(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    elif agent_type == AgentType.MEDIA_AGENT:
        return get_media_agent(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    # Teams
    elif agent_type == AgentType.CONTENT_TEAM:
        return get_content_team(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    elif agent_type == AgentType.NEWS_AGENCY_TEAM:
        return get_news_agency_team(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    # Workflows
    elif agent_type == AgentType.BLOG_GENERATOR:
        return get_blog_generator_workflow(
            model_id=model_id,
            provider=provider,
            settings=settings,
            user_id=user_id,
            session_id=session_id,
            debug_mode=debug_mode,
            db=agent_db,
        )
    else:
        raise ValueError(f"Agent type {agent_type} not supported")
