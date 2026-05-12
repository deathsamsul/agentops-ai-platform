"""
tools/base.py — Common interface every tool must follow.

Why a base class?
  The agent calls tools via:
      tool.execute(data)
  Having one contract means you can swap, mock, or extend any tool
  without changing the agent code.

Future MCP upgrade path:
  When you move to MCP servers, your MCP tool wrappers will also
  subclass BaseTool — so agent code stays the same.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Every tool MUST define:
      name        — unique snake_case identifier, e.g. "send_email"
      description — one sentence; the LLM reads this to decide which tool to use
      execute()   — does the actual work
    """

    name: str
    description: str

    @abstractmethod
    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Run the tool.

        Args:
            data: Dictionary of parameters (validated by the caller).

        Returns:
            Dictionary with at minimum {"status": "ok"|"error", ...result fields...}
        """
        raise NotImplementedError

    # ── Convenience helpers ───────────────────────────────────────────────────

    def success(self, **kwargs) -> dict[str, Any]:
        """Return a standard success payload."""
        return {"status": "ok", "tool": self.name, **kwargs}

    def error(self, message: str) -> dict[str, Any]:
        """Return a standard error payload."""
        return {"status": "error", "tool": self.name, "message": message}

    def schema(self) -> dict[str, Any]:
        """
        Return tool schema in MCP-compatible format.
        Override in subclass to add input_schema details.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {},
        }

    def __repr__(self) -> str:
        return f"<Tool name={self.name!r}>"
