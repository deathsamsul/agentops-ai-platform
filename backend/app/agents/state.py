from __future__ import annotations
from typing import Any, Annotated
from operator import add        # used by LangGraph to merge list fields
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


"""
agents/state.py — LangGraph agent state schema.

AgentState is the single object that flows through every node in the graph.
Each node reads from it and writes back to it.

Think of it as the agent's working memory for one conversation turn.
"""


# TODO With checkpointer + thread_id 
class AgentState(BaseModel):
    """
    Shared state threaded through every node of the LangGraph workflow.

    LangGraph uses type annotations to decide how to merge state when
    running nodes in parallel:
      - list fields annotated with Annotated[list, add] are APPENDED
      - plain fields are REPLACED with the new value
    """

    # ── Conversation ──────────────────────────────────────────────────────────
    messages: Annotated[list[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="Full conversation history (LangChain message objects)",
    )
    session_id: str = ""
    user_id: str = "anonymous"

    # ── Current turn ──────────────────────────────────────────────────────────
    user_input: str = ""
    agent_reply: str = ""

    # ── Tool tracking ─────────────────────────────────────────────────────────
    # List of {tool_name, input_data, output, success} dicts
    tool_calls: Annotated[list[dict[str, Any]], add] = Field(default_factory=list)

    # Next tool the planner decided to call (set by planner, consumed by executor)
    next_tool: str | None = None
    next_tool_input: dict[str, Any] = Field(default_factory=dict)

    # ── Workflow control ──────────────────────────────────────────────────────
    # How many tool-calling iterations we've done (guard against infinite loops)
    iteration: int = 0
    max_iterations: int = 10

    # When True, the agent pauses and asks the human to approve before proceeding
    requires_approval: bool = False
    approval_token: str | None = None
    approved: bool | None = None     # None = waiting, True = approved, False = rejected

    # ── Error state ───────────────────────────────────────────────────────────
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True   # needed for LangChain BaseMessage ,It allows non-normal Python/Pydantic types is a LangChain object, not a simple type like string/int/list.
        