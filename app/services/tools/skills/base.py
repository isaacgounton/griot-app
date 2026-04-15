"""
Base classes for the Griot skill system (OpenAI function-calling format).

To create a new skill:
1. Create a file named `<name>_skill.py` in this directory
2. Define async handler functions: async (args: dict) -> dict
3. Create a module-level `skill` variable of type `Skill`
4. Register actions with OpenAI JSON Schema parameters

The SkillRegistry auto-discovers all *_skill.py files on startup.

Example (weather_skill.py):

    from app.services.tools.skills.base import Skill

    async def get_weather(args: dict) -> dict:
        city = args["city"]
        # ... call weather service ...
        return {"temperature": 22, "city": city}

    skill = Skill(name="weather", description="Weather information")

    skill.action(
        name="get_weather",
        description="Get current weather conditions",
        handler=get_weather,
        properties={
            "city": {"type": "string", "description": "City name"},
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature units",
                "default": "celsius",
            },
        },
        required=["city"],
    )
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# Handler signature: async (args: dict[str, Any]) -> dict[str, Any]
AsyncHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class SkillAction:
    """A single tool action with OpenAI function-calling metadata."""

    name: str
    description: str
    handler: AsyncHandler
    properties: dict[str, Any] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)

    def to_tool_definition(self) -> dict[str, Any]:
        """Generate an OpenAI function-calling tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.properties,
                    "required": self.required,
                },
            },
        }


@dataclass
class Skill:
    """
    A modular skill that groups related tool actions.

    Skills are auto-discovered from *_skill.py files. Each skill can
    contain multiple actions that become individual OpenAI tools (direct mode)
    or are dispatched through a single `use_skill` meta-tool (dispatch mode).
    """

    name: str
    description: str
    actions: dict[str, SkillAction] = field(default_factory=dict)

    def action(
        self,
        name: str,
        description: str,
        handler: AsyncHandler,
        properties: dict[str, Any] | None = None,
        required: list[str] | None = None,
    ) -> None:
        """Register an action on this skill."""
        self.actions[name] = SkillAction(
            name=name,
            description=description,
            handler=handler,
            properties=properties or {},
            required=required or [],
        )

    async def execute(self, action_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute an action by name (used in dispatch mode)."""
        if action_name == "help":
            return self.get_help()

        skill_action = self.actions.get(action_name)
        if not skill_action:
            available = ", ".join(self.actions.keys())
            return {
                "error": (
                    f"Unknown action '{action_name}' in skill '{self.name}'. "
                    f"Available: {available}"
                ),
            }

        try:
            return await skill_action.handler(params)
        except TypeError as e:
            return {
                "error": f"Invalid parameters for '{self.name}.{action_name}': {e}",
                "expected": {
                    k: v.get("description", "")
                    for k, v in skill_action.properties.items()
                },
            }
        except Exception as e:
            logger.error("Skill '%s' action '%s' failed: %s", self.name, action_name, e)
            return {"error": f"Skill action failed: {e}"}

    def get_help(self) -> dict[str, Any]:
        """Return help info for this skill."""
        return {
            "skill": self.name,
            "description": self.description,
            "actions": {
                name: {
                    "description": a.description,
                    "parameters": a.properties,
                    "required": a.required,
                }
                for name, a in self.actions.items()
            },
        }
