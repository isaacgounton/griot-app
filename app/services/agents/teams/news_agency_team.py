"""
News Agency Team - Professional news production team.
Combines searching, writing, and editing for high-quality journalism.
"""

from typing import Optional, Union
from textwrap import dedent

from agno.agent import Agent
from agno.db.base import AsyncBaseDb, BaseDb
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

from app.services.agents.models import create_chat_model


def get_news_agency_team(
    model_id: str = "gpt-4-mini",
    provider: Optional[str] = None,
    settings: Optional[dict] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
) -> Team:
    """Create a news agency team with searcher, writer, and editor."""
    
    # Searcher agent
    searcher = Agent(
        name="Searcher",
        role="Searches the top URLs for a topic",
        tools=[DuckDuckGoTools()],
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        instructions=dedent("""\
            Given a topic, generate search terms and find the most relevant URLs.
            - Create 3 search terms related to the topic
            - Search the web for each term
            - Return the 10 most relevant URLs
            - Prioritize quality sources
        """),
        markdown=True,
        add_datetime_to_context=True,
    )

    # Writer agent
    writer = Agent(
        name="Writer",
        role="Writes high-quality, engaging articles",
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        instructions=dedent("""\
            Write professional, well-structured articles.
            - Structure content logically with clear sections
            - Write at least 15 paragraphs for comprehensive coverage
            - Provide nuanced and balanced opinions
            - Quote facts and provide proper attribution
            - Focus on clarity, coherence, and quality
        """),
        markdown=True,
        add_datetime_to_context=True,
    )

    # Create the team with editor coordination
    return Team(
        name="News Agency Team",
        id="news_agency_team",
        user_id=user_id,
        session_id=session_id,
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        db=db,
        members=[searcher, writer],
        description="Professional news production team for high-quality journalism",
        instructions=dedent("""\
            You are a senior news editor. Your goal is to produce high-quality articles.

            1. Ask the searcher to find the most relevant URLs for the topic
            2. Ask the writer to create an engaging draft article
            3. Edit, proofread, and refine the article
            4. Ensure it meets high journalistic standards
            5. Verify facts and attributions
        """),
        add_datetime_to_context=True,
        add_history_to_context=True,
        num_history_runs=3,
        markdown=True,
        show_members_responses=True,
        store_member_responses=True,
        debug_mode=debug_mode,
    )
