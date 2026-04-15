"""
Finance Agent - Your Personal Market Analyst!
Provides comprehensive market insights using real-time data, combining stock market data,
analyst recommendations, company information, and latest news for professional-grade financial analysis.
"""

from typing import Optional, Union
from textwrap import dedent

from agno.agent import Agent
from agno.db.base import AsyncBaseDb, BaseDb
from agno.tools.yfinance import YFinanceTools

from app.services.agents.models import create_chat_model


def get_finance_agent(
    model_id: str = "gpt-4o",
    provider: Optional[str] = None,
    settings: Optional[dict] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
    db: Optional[Union[BaseDb, AsyncBaseDb]] = None,
) -> Agent:
    """Create a sophisticated financial analyst agent with comprehensive market insights."""
    return Agent(
        name="Finance Agent",
        id="finance_agent",
        user_id=user_id,
        session_id=session_id,
        model=create_chat_model(model_id=model_id, provider=provider, settings=settings),
        db=db,
        tools=[YFinanceTools()],
        description=dedent("""\
            You are a seasoned Wall Street analyst with deep expertise in market analysis! 📊
            You combine stock market data, analyst recommendations, company information, and latest news
            to deliver professional-grade financial analysis and market insights.
        """),
        instructions=dedent("""\
            You are a seasoned Wall Street analyst with deep expertise in market analysis! 📊

            Follow these steps for comprehensive financial analysis:
            1. Market Overview
               - Latest stock price
               - 52-week high and low
            2. Financial Deep Dive
               - Key metrics (P/E, Market Cap, EPS)
            3. Professional Insights
               - Analyst recommendations breakdown
               - Recent rating changes

            4. Market Context
               - Industry trends and positioning
               - Competitive analysis
               - Market sentiment indicators

            Your reporting style:
            - Begin with an executive summary
            - Use tables for data presentation
            - Include clear section headers
            - Add emoji indicators for trends (📈 📉)
            - Highlight key insights with bullet points
            - Compare metrics to industry averages
            - Include technical term explanations
            - End with a forward-looking analysis

            Risk Disclosure:
            - Always highlight potential risk factors
            - Note market uncertainties
            - Mention relevant regulatory concerns

            Additional Information:
            - You are interacting with user_id: {current_user_id}
        """),
        markdown=True,
        add_datetime_to_context=True,
        add_history_to_context=True,
        debug_mode=debug_mode,
    )
