"""
Tool registry for LLM function calling.

Thin wrapper around the skill registry. Tools are auto-discovered from
*_skill.py files in app/services/tools/skills/.

To add a new tool, create a skill file — see skills/base.py for the guide.
"""

from typing import Any

from app.services.tools.skills import get_registry


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return all tool definitions in OpenAI function calling format."""
    return get_registry().get_tool_definitions()


def get_system_prompt() -> str:
    """Return the system prompt for tool-enabled chat."""
    return get_registry().get_system_prompt()


async def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name and return the result."""
    return await get_registry().execute_tool(name, arguments)
