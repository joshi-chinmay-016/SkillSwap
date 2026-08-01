"""
ToolRegistry — intent-to-tool mapping without if-else chains.

Tools self-register based on their ``supported_intents`` property.
Future tools can be added without modifying the dispatcher or registry.
"""
import logging
from typing import Dict, List, Optional

from app.ai.models.mentor_intent import MentorIntent
from app.ai.tools.mentor_tool import MentorTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry of available MentorTools, keyed by MentorIntent.
    """

    def __init__(self):
        self._registry: Dict[MentorIntent, List[MentorTool]] = {}

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def register(self, tool: MentorTool) -> None:
        """
        Register a tool for each of its supported intents.

        A single tool may support multiple intents.
        Multiple tools may be registered for the same intent — the
        first registered tool takes precedence via ``resolve()``.
        """
        for intent in tool.supported_intents:
            if intent not in self._registry:
                self._registry[intent] = []
            self._registry[intent].append(tool)
            logger.info(
                "ToolRegistry: registered %s for intent %s",
                tool.name,
                intent.value,
            )

    def resolve(self, intent: MentorIntent) -> Optional[MentorTool]:
        """
        Return the first registered tool for the given intent.

        Returns None if no tool is registered for this intent.
        """
        tools = self._registry.get(intent)
        if tools:
            return tools[0]
        return None

    def list_tools(self) -> List[str]:
        """Return names of all registered tools (for observability)."""
        seen: set[str] = set()
        names: List[str] = []
        for tool_list in self._registry.values():
            for tool in tool_list:
                if tool.name not in seen:
                    seen.add(tool.name)
                    names.append(tool.name)
        return names

    def list_intent_mappings(self) -> Dict[str, str]:
        """Return a dict of intent → tool name for observability."""
        return {
            intent.value: tools[0].name
            for intent, tools in self._registry.items()
            if tools
        }
