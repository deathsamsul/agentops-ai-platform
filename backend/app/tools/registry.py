from __future__ import annotations
from typing import Any
from app.tools.base import BaseTool
# ── Import concrete tools here as you build them ─────────────────────────────
from app.tools.mock_tools import ( EmailTool,CalendarTool,DatabaseTool,BookingTool,SearchDocsTool,)



"""
tools/registry.py — Maps tool names to tool instances.
The ToolRegistry is the single source of truth for which tools exist.
Usage:
    from app.tools.registry import registry
    tool = registry.get("send_email")
    result = tool.execute({"to": "...", "subject": "...", "body": "..."})
Adding a new tool:
    1. Create MyTool(BaseTool) in tools/my_tool.py
    2. Import it here and call registry.register(MyTool())
MCP upgrade path:
    When you switch to MCP servers, register MCPToolWrapper instances
    instead of Python tool instances. The executor/agent code stays the same.
"""

class ToolRegistry:
    """Holds all registered tool instances, keyed by tool.name."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance. Raises if name already registered."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Get a tool by name. Raises KeyError if not found."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool: '{name}'. Available: {self.list_names()}")
        return self._tools[name]

    def list_names(self) -> list[str]:
        return list(self._tools.keys())

    def all_schemas(self) -> list[dict[str, Any]]:
        """Return all tool schemas — useful for passing to the LLM."""
        return [t.schema() for t in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ─── Global registry instance ────────────────────────────────────────────────
registry = ToolRegistry()

# Register all tools
registry.register(EmailTool())
registry.register(CalendarTool())
registry.register(DatabaseTool())
registry.register(BookingTool())
registry.register(SearchDocsTool())
