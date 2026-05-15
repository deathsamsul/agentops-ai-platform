from __future__ import annotations
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import (planner_node,executor_node,approval_node,responder_node,should_continue,after_executor,)



"""
agents/graph.py — LangGraph workflow definition.

This file wires the nodes together into a directed graph:

    START
      |
    planner ──(tool chosen)──► executor ──(needs approval)──► approval ──► END
      |                           |
      |                     (no approval)
      |                           |
      └──(direct reply)───────────┤
                                  |
                                responder ──► END

How LangGraph works:
  - Each node is a function: (AgentState) -> dict
  - Edges are either FIXED or CONDITIONAL (decided by a routing function)
  - State is automatically merged after each node
"""



def build_graph() -> StateGraph:
    """
    Construct and compile the LangGraph agent workflow.

    Returns a compiled graph ready to call with:
        graph.invoke({"user_input": "...", "session_id": "..."})
    """

    # ── 1. Create graph with our state schema ─────────────────────────────────
    builder = StateGraph(AgentState)

    # ── 2. Register nodes ─────────────────────────────────────────────────────
    builder.add_node("planner",   planner_node)
    builder.add_node("executor",  executor_node)
    builder.add_node("approval",  approval_node)
    builder.add_node("responder", responder_node)

    # ── 3. Entry point ────────────────────────────────────────────────────────
    builder.set_entry_point("planner")

    # ── 4. Edges from planner ─────────────────────────────────────────────────
    # Conditional: does planner want to call a tool or reply directly?
    builder.add_conditional_edges(
        "planner",
        should_continue,
        {
            "execute": "executor",   # planner chose a tool
            "end":     "responder",  # planner replied directly
        },
    )

    # ── 5. Edges from executor ────────────────────────────────────────────────
    builder.add_conditional_edges(
        "executor",
        after_executor,
        {
            "approve": "approval",   # tool result needs human sign-off
            "plan":    "planner",    # go back to planner for next tool / reply
            "end":     "responder",  # iteration limit hit
        },
    )

    # ── 6. Terminal edges ─────────────────────────────────────────────────────
    builder.add_edge("approval",  END)
    builder.add_edge("responder", END)

    # ── 7. Compile ────────────────────────────────────────────────────────────
    return builder.compile()


# ─── Singleton compiled graph ─────────────────────────────────────────────────
# Import this in routes_chat.py:
#   from app.agents.graph import agent_graph
agent_graph = build_graph()
