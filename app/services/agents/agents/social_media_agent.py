"""
Social Media Agent - Analyzes social media sentiment and trends.
Provides brand intelligence and engagement insights.
"""

from typing import Optional, Union
from textwrap import dedent

from agno.agent import Agent
from agno.db.base import AsyncBaseDb, BaseDb
from app.services.agents.models import create_chat_model


def get_social_media_agent(
    model_id: str = "gpt-4-mini",
    provider: Optional[str] = None,
    settings: Optional[dict] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
) -> Agent:
    """Create a social media analysis agent."""
    return Agent(
        name="Social Media Analyst",
        id="social_media_agent",
        user_id=user_id,
        session_id=session_id,
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        db=db,
        description=dedent("""\
            You are a senior Brand Intelligence Analyst specializing in social media listening.
            Your job is to transform raw social content into executive-ready intelligence reports.
        """),
        instructions=dedent("""\
            1. Sentiment Analysis 📊
               - Classify content as Positive / Negative / Neutral / Mixed
               - Capture reasoning for each classification
               - Detect patterns in engagement metrics

            2. Theme Detection 🎯
               - Extract thematic clusters and recurring keywords
               - Identify feature praise and pain points
               - Surface UX and performance issues
               - Track customer service interactions

            3. Influence Analysis 👥
               - Identify key influencers and advocates
               - Detect viral advocacy patterns
               - Surface controversy indicators
               - Track influence concentration

            4. Actionable Insights 💡
               - Produce prioritized recommendations
               - Suggest response strategies
               - Identify engagement opportunities
               - Highlight emerging use-cases

            5. Reporting 📋
               - Provide executive summary with brand health score
               - Include quantitative dashboard with metrics
               - List key themes with representative quotes
               - Suggest strategic recommendations
        """),
        markdown=True,
        add_datetime_to_context=True,
        add_history_to_context=True,
        debug_mode=debug_mode,
    )
