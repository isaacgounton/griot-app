"""
Content Team - Collaborative team for high-quality content creation.
Combines research and writing expertise for comprehensive content generation.
"""

from typing import Optional, Union
from textwrap import dedent

from agno.agent import Agent
from agno.db.base import AsyncBaseDb, BaseDb
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

from app.services.agents.models import create_chat_model


def get_content_team(
    model_id: str = "gpt-4o-mini",
    provider: Optional[str] = None,
    settings: Optional[dict] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
) -> Team:
    """Create a content creation team with researcher and writer."""
    
    # Researcher agent
    researcher = Agent(
        name="Researcher",
        role="Expert at finding and analyzing information",
        tools=[DuckDuckGoTools()],
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        instructions=dedent("""\
            Your role is to research topics thoroughly and provide comprehensive information.
            - Search for authoritative sources
            - Gather diverse perspectives
            - Extract key facts and statistics
            - Identify trends and patterns
        """),
        markdown=True,
        add_datetime_to_context=True,
    )

    # Writer agent
    writer = Agent(
        name="Writer",
        role="Expert at writing clear, engaging, and compelling content",
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        instructions=dedent("""\
            Your role is to transform research into engaging content.
            - Create compelling narratives
            - Maintain clarity and readability
            - Structure content logically
            - Engage the target audience
        """),
        markdown=True,
        add_datetime_to_context=True,
    )

    # Create the team
    return Team(
        name="Content Team",
        id="content_team",
        user_id=user_id,
        session_id=session_id,
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        db=db,
        members=[researcher, writer],
        instructions=dedent("""\
            You are a team of researchers and writers that work together to create high-quality content.

            1. Researcher: Gather comprehensive information on the topic
            2. Writer: Transform the research into engaging, well-structured content
            3. Collaborate: Ensure accuracy, clarity, and engagement
        """),
        show_members_responses=True,
        store_member_responses=True,
        markdown=True,
        add_datetime_to_context=True,
        add_history_to_context=True,
        num_history_runs=3,
        debug_mode=debug_mode,
    )
