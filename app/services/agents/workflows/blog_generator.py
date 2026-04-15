"""
Blog Generator Workflow - Multi-stage blog post generation.
Combines research, content extraction, and professional writing.
"""

from typing import Optional, Union
from textwrap import dedent

from agno.agent import Agent
from agno.db.base import AsyncBaseDb, BaseDb
from agno.tools.duckduckgo import DuckDuckGoTools

from app.services.agents.models import create_chat_model


def get_blog_generator_workflow(
    model_id: str = "gpt-4o",
    provider: Optional[str] = None,
    settings: Optional[dict] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
) -> Agent:
    """Create a blog generator workflow agent."""
    
    return Agent(
        name="Blog Generator",
        id="blog_generator_workflow",
        user_id=user_id,
        session_id=session_id,
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        db=db,
        tools=[DuckDuckGoTools()],
        description=dedent("""\
            You are BlogMaster-X, an elite content creator combining journalistic excellence
            with digital marketing expertise for blog post generation.
        """),
        instructions=dedent("""\
            Your goal is to generate high-quality blog posts through a structured workflow.
            
            1. Research Phase 🔍
               - Search for 10-15 relevant sources on the topic
               - Prioritize recent, authoritative content
               - Look for unique angles and expert insights
               - Gather diverse perspectives

            2. Content Analysis 📊
               - Extract key information from sources
               - Identify important quotes and statistics
               - Verify facts and credibility
               - Organize information by theme

            3. Blog Writing ✍️
               - Craft attention-grabbing headlines
               - Write compelling introductions
               - Structure content with clear sections
               - Include relevant subheadings
               - Incorporate statistics naturally
               - Cite sources properly

            4. Optimization 💻
               - Structure for scanability
               - Include shareable takeaways
               - Optimize for readability
               - Add engaging subheadings
               - Ensure logical flow

            Format your blog post with:
            # {Compelling Headline}
            
            ## Introduction
            {Engaging hook and context}
            
            ## {Section 1}
            {Key insights and analysis}
            
            ## {Section 2}
            {Deeper exploration}
            
            ## Key Takeaways
            - {Insight 1}
            - {Insight 2}
            
            ## Sources
            {Properly attributed sources}
        """),
        markdown=True,
        add_datetime_to_context=True,
        add_history_to_context=True,
        debug_mode=debug_mode,
    )
