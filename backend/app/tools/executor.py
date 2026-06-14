from __future__ import annotations
import logging
from typing import Any
from app.tools.registry import registry


"""
Agent does not directly call tools.
Agent calls executor.
Executor finds the correct tool and runs it.
tools/executor.py — Central controller that runs tools on behalf of the agent.
This is the KEY architectural decision:
  Phase 1 (now):    Agent → PythonToolExecutor → Python function in tools/
  Phase 8 (later):  Agent → MCPToolExecutor    → MCP server
The agent only ever calls:
    executor.execute(tool_name, data)
So when you upgrade to MCP, you swap the executor — NOT the agent.
"""

# TODO in phase 1, paythontoolexecutor will change with mcptollexecutor, but the agent nodes will not. This is the key to making the architecture flexible and future-proof.


logger = logging.getLogger(__name__)


class PythonToolExecutor:
    """
    Executes tools by looking them up in the registry and calling .execute().
    This is your Phase 1 executor.
    Later you will add MCPToolExecutor with the same interface.
    """

    def execute(self, tool_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Run a tool by name.
        Args:
            tool_name: Must match a registered BaseTool.name
            data:      Parameters dict forwarded to tool.execute() data is only for tools not full agent state full message history
        Returns:
            Tool result dict (always has "status" key)
        """
        logger.info("Executing tool '%s' with input keys: %s", tool_name, list(data.keys()))
        try:
            tool = registry.get(tool_name)
            result = tool.execute(data)  #this executor function is inherite from tool own shemas 
            logger.info("Tool '%s' completed with status: %s", tool_name, result.get("status"))
            return result

        except KeyError as exc:
            logger.warning("Tool not found: %s", exc)
            return {
                "status": "error",
                "tool": tool_name,
                "message": str(exc),
                "available_tools": registry.list_names(),
            }

        except Exception as exc:
            logger.exception("Tool '%s' raised an unexpected error", tool_name)
            return {
                "status": "error",
                "tool": tool_name,
                "message": f"Tool execution failed: {exc}",
            }

    def list_tools(self) -> list[str]:
        return registry.list_names()

    def tool_schemas(self) -> list[dict[str, Any]]:
        """Pass these to the LLM so it knows what tools it can call."""
        return registry.all_schemas()


# ─── Singleton — import this in agents/nodes.py ──────────────────────────────
executor = PythonToolExecutor()


# ─── Future MCP executor (scaffold — implement in Phase 8) ────────────────
class MCPToolExecutor:
    """
    Calls tools on remote MCP servers instead of local Python functions.
    Usage will be identical to PythonToolExecutor:
        result = executor.execute("send_email", data)
    Implementation notes (Phase 8):
        - Maintain a map of tool_name → mcp_server_url
        - Use httpx or the official MCP client to call the server
        - Server returns the same dict shape as BaseTool.execute()
    """

    TOOL_SERVER_MAP: dict[str, str] = {
        "send_email":          "http://localhost:8001",   # email_mcp_server
        "create_task":         "http://localhost:8002",   # postgres_mcp_server
        "get_tasks":           "http://localhost:8002",
        "search_docs":         "http://localhost:8003",   # rag_mcp_server
        "get_pods":            "http://localhost:8004",   # kubernetes_mcp_server
        "restart_deployment":  "http://localhost:8004",
    }

    def execute(self, tool_name: str, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Implement in Phase 8 using httpx MCP client")
