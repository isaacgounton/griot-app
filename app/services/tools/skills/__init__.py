"""
Griot Skill Registry for /dashboard/chat.

Auto-discovers skills from *_skill.py files in this directory and serves them
as OpenAI function-calling tool definitions for the LLM chat pipeline.

Supports two modes (auto-selected based on total action count):
- Direct mode (<= threshold): Each action is an individual tool definition.
  Best accuracy, highest token cost.
- Grouped mode (> threshold): One tool per skill with an ``action`` enum and
  merged parameter schemas.  Good accuracy at ~1/3 the token cost.

Usage:
    from app.services.tools.skills import get_registry

    registry = get_registry()

    # For GET /api/v1/tools
    tool_defs = registry.get_tool_definitions()
    system_prompt = registry.get_system_prompt()

    # For POST /api/v1/tools/execute
    result = await registry.execute_tool("text_to_speech", {"text": "hello"})
"""

import importlib
import logging
import os
from pathlib import Path
from typing import Any

from app.services.tools.skills.base import Skill, SkillAction  # noqa: F401

logger = logging.getLogger(__name__)

DISPATCH_THRESHOLD = int(os.getenv("SKILL_DISPATCH_THRESHOLD", "30"))

SYSTEM_PROMPT = (
    "You are a helpful AI assistant with access to various tools. "
    "When the user asks you to do something that requires a tool "
    "(like generating images, searching the web, creating audio, etc.), "
    "use the appropriate tool. Always explain what you're doing before "
    "using a tool. After receiving tool results, present them naturally "
    "to the user. For media results (images, audio, video), mention that "
    "the content has been generated and include any relevant details."
)


class SkillRegistry:
    """Registry that discovers skills and serves OpenAI tool definitions."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._action_lookup: dict[str, tuple[Skill, SkillAction]] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def register(self, skill: Skill) -> None:
        """Register a skill and index its actions."""
        if skill.name in self._skills:
            logger.warning("Skill '%s' already registered, overwriting", skill.name)
        self._skills[skill.name] = skill

        for action_name, action in skill.actions.items():
            if action_name in self._action_lookup:
                existing_skill = self._action_lookup[action_name][0]
                logger.warning(
                    "Action '%s' already registered by skill '%s', overwriting with '%s'",
                    action_name, existing_skill.name, skill.name,
                )
            self._action_lookup[action_name] = (skill, action)

        logger.info(
            "Registered skill: %s (%d actions)", skill.name, len(skill.actions)
        )

    def load_directory(self, directory: str | None = None) -> None:
        """Auto-discover and load all *_skill.py modules from a directory."""
        if directory is None:
            directory = str(Path(__file__).parent)

        for filename in sorted(os.listdir(directory)):
            if not filename.endswith("_skill.py"):
                continue

            module_name = filename[:-3]
            try:
                module = importlib.import_module(f"{__package__}.{module_name}")
                skill_obj = getattr(module, "skill", None)
                if isinstance(skill_obj, Skill):
                    self.register(skill_obj)
                else:
                    logger.warning(
                        "Module '%s' has no valid 'skill' attribute, skipping",
                        module_name,
                    )
            except Exception as e:
                logger.error("Failed to load skill module '%s': %s", module_name, e)

        self._loaded = True
        logger.info(
            "Skill registry loaded: %d skills, %d total actions",
            len(self._skills),
            len(self._action_lookup),
        )

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_directory()

    # ------------------------------------------------------------------
    # Tool definitions (OpenAI format)
    # ------------------------------------------------------------------

    @property
    def total_action_count(self) -> int:
        self._ensure_loaded()
        return len(self._action_lookup)

    def get_tool_definitions(self, mode: str | None = None) -> list[dict[str, Any]]:
        """
        Return tool definitions in OpenAI function-calling format.

        Modes:
          - "direct": one tool definition per action (best accuracy)
          - "grouped": one tool per skill with action enum (scales well)
          - None: auto-select based on action count vs threshold
        """
        self._ensure_loaded()

        use_grouped = (
            mode == "grouped"
            or (mode is None and self.total_action_count > DISPATCH_THRESHOLD)
        )

        if use_grouped:
            logger.info(
                "Skill grouped mode: %d actions in %d skill tools",
                self.total_action_count, len(self._skills),
            )
            return self._create_grouped_definitions()
        else:
            logger.info(
                "Skill direct mode: %d individual tool definitions",
                self.total_action_count,
            )
            return [
                skill_action.to_tool_definition()
                for _, skill_action in self._action_lookup.values()
            ]

    def _create_grouped_definitions(self) -> list[dict[str, Any]]:
        """Build one tool definition per skill.

        Each skill becomes a tool whose ``action`` property is an enum of
        its action names and whose remaining properties are the merged
        (deduplicated) parameters from all actions.
        """
        definitions = []

        for name, skill in sorted(self._skills.items()):
            action_names = list(skill.actions.keys())

            # Start with the action selector
            merged_props: dict[str, Any] = {}
            merged_required: list[str] = ["action"]

            if len(action_names) == 1:
                # Single-action skill: no need for action enum
                only_action = skill.actions[action_names[0]]
                merged_props = dict(only_action.properties)
                merged_required = list(only_action.required)
                description = f"{skill.description}. {only_action.description}"
            else:
                # Multi-action skill: add action enum + merge params
                action_desc_parts = []
                for a_name, a in skill.actions.items():
                    req = f" (requires: {', '.join(a.required)})" if a.required else ""
                    action_desc_parts.append(f"{a_name}{req}: {a.description}")

                merged_props["action"] = {
                    "type": "string",
                    "enum": action_names,
                    "description": "Action to perform:\n" + "\n".join(
                        f"- {part}" for part in action_desc_parts
                    ),
                }

                # Merge parameters from all actions (first definition wins)
                for a in skill.actions.values():
                    for prop_name, prop_def in a.properties.items():
                        if prop_name not in merged_props:
                            merged_props[prop_name] = dict(prop_def)

                description = skill.description

            definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": merged_props,
                        "required": merged_required,
                    },
                },
            })

        return definitions

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name.

        Handles three call patterns:
        1. Direct mode — name is an action name (e.g. ``web_search``)
        2. Grouped mode — name is a skill name (e.g. ``search``) with an
           ``action`` key in arguments
        3. Legacy dispatch — name is ``use_skill``
        """
        self._ensure_loaded()
        logger.info("Executing tool: %s with arguments: %s", name, arguments)

        try:
            # Legacy dispatch: use_skill meta-tool
            if name == "use_skill":
                skill_name = arguments.get("skill_name", "")
                action = arguments.get("action", "help")
                params = arguments.get("parameters", {})

                # Fallback: LLMs sometimes put params at top level
                if not params:
                    params = {
                        k: v for k, v in arguments.items()
                        if k not in ("skill_name", "action", "parameters")
                    }

                skill = self._skills.get(skill_name)
                if not skill:
                    available = ", ".join(sorted(self._skills.keys()))
                    return {"error": f"Unknown skill '{skill_name}'. Available: {available}"}

                return await skill.execute(action, params)

            # Direct mode: action name lookup
            entry = self._action_lookup.get(name)
            if entry:
                _, action = entry
                return await action.handler(arguments)

            # Grouped mode: skill name with action in arguments
            skill = self._skills.get(name)
            if skill:
                action_name = arguments.pop("action", None)
                # Single-action skill: use the only action
                if not action_name and len(skill.actions) == 1:
                    action_name = next(iter(skill.actions))
                return await skill.execute(action_name or "help", arguments)

            return {"error": f"Unknown tool: {name}"}

        except Exception as e:
            logger.error("Tool execution failed for %s: %s", name, e)
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def get_system_prompt(self) -> str:
        """Return the system prompt for tool-enabled chat."""
        return SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_default_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """Get the default skill registry singleton. Loads skills on first access."""
    global _default_registry
    if _default_registry is None:
        _default_registry = SkillRegistry()
        _default_registry.load_directory()
    return _default_registry
