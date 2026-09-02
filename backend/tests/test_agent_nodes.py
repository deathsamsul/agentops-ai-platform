"""
test_agent_nodes.py — Unit tests for LangGraph agent nodes.

Key principle: every test patches _get_llm_with_tools()
so NO real LLM API calls are made. Tests are fast, free, deterministic.

Tests:
  - planner_node: direct reply path
  - planner_node: tool call path
  - executor_node: runs correct tool, records result
  - executor_node: sets requires_approval when tool needs it
  - approval_node: returns correct reply shape
  - responder_node: skips when agent_reply already set
  - should_continue routing
  - after_executor routing
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agents.state import AgentState
from app.agents.nodes import (
    planner_node,
    executor_node,
    approval_node,
    responder_node,
    should_continue,
    after_executor,
)


# ─── Shared state factory ─────────────────────────────────────────────────────
def make_state(**kwargs) -> AgentState:
    defaults = dict(
        messages=[HumanMessage(content="Test message")],
        session_id="test-session",
        user_id="test-user",
        user_input="Test message",
    )
    defaults.update(kwargs)
    return AgentState(**defaults)


# ── Helper: build a mock LLM ──────────────────────────────────────────────────
def _mock_llm_direct(reply_text: str):
    """LLM that returns a plain text reply (no tool call)."""
    resp = AIMessage(content=reply_text)
    resp.tool_calls = []
    m = MagicMock()
    m.invoke.return_value = resp
    m.bind_tools.return_value = m
    return m


def _mock_llm_tool(tool_name: str, tool_args: dict):
    """LLM that requests a tool call."""
    resp = AIMessage(content="")
    resp.tool_calls = [{"name": tool_name, "args": tool_args, "id": "tc_001"}]
    m = MagicMock()
    m.invoke.return_value = resp
    m.bind_tools.return_value = m
    return m


# ══════════════════════════════════════════════════════════════════════════════
# planner_node
# ══════════════════════════════════════════════════════════════════════════════
class TestPlannerNode:
    def test_direct_reply_sets_agent_reply(self):
        state = make_state()
        mock_llm = _mock_llm_direct("Hello from mock LLM!")
        with patch("app.agents.nodes._get_llm_with_tools", return_value=mock_llm):
            result = planner_node(state)
        assert result["agent_reply"] == "Hello from mock LLM!"
        assert result["next_tool"] is None

    def test_tool_call_sets_next_tool(self):
        state = make_state()
        mock_llm = _mock_llm_tool("create_task", {"title": "Review docs"})
        with patch("app.agents.nodes._get_llm_with_tools", return_value=mock_llm):
            result = planner_node(state)
        assert result["next_tool"] == "create_task"
        assert result["next_tool_input"] == {"title": "Review docs"}
        assert result["agent_reply"] == "" or "agent_reply" not in result

    def test_iteration_incremented_on_tool_call(self):
        state = make_state(iteration=2)
        mock_llm = _mock_llm_tool("send_email", {"to": "a@b.com", "subject": "s", "body": "b"})
        with patch("app.agents.nodes._get_llm_with_tools", return_value=mock_llm):
            result = planner_node(state)
        assert result["iteration"] == 3

    def test_message_appended(self):
        state = make_state()
        mock_llm = _mock_llm_direct("OK")
        with patch("app.agents.nodes._get_llm_with_tools", return_value=mock_llm):
            result = planner_node(state)
        assert len(result["messages"]) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# executor_node
# ══════════════════════════════════════════════════════════════════════════════
class TestExecutorNode:
    def test_runs_tool_and_records_result(self):
        state = make_state(
            next_tool="create_task",
            next_tool_input={"title": "Node executor test", "priority": "low"},
        )
        result = executor_node(state)

        assert len(result["tool_calls"]) == 1
        tc = result["tool_calls"][0]
        assert tc["tool_name"] == "create_task"
        assert tc["success"] is True

    def test_tool_message_appended(self):
        state = make_state(
            next_tool="create_task",
            next_tool_input={"title": "Msg test"},
        )
        result = executor_node(state)
        assert any(isinstance(m, ToolMessage) for m in result["messages"])

    def test_unknown_tool_records_failure(self):
        state = make_state(
            next_tool="nonexistent_tool_xyz",
            next_tool_input={},
        )
        result = executor_node(state)
        tc = result["tool_calls"][0]
        assert tc["success"] is False

    def test_approval_tool_sets_flag(self):
        # send_email requires approval
        state = make_state(
            next_tool="send_email",
            next_tool_input={"to": "a@b.com", "subject": "s", "body": "b"},
        )
        result = executor_node(state)
        assert result["requires_approval"] is True
        assert result["approval_token"] is not None

    def test_non_approval_tool_clears_flag(self):
        # search_docs does NOT require approval
        state = make_state(
            next_tool="search_docs",
            next_tool_input={"query": "architecture"},
        )
        result = executor_node(state)
        assert result["requires_approval"] is False
        assert result["approval_token"] is None

    def test_next_tool_cleared_after_execution(self):
        state = make_state(
            next_tool="create_task",
            next_tool_input={"title": "Clear test"},
        )
        result = executor_node(state)
        assert result["next_tool"] is None
        assert result["next_tool_input"] == {}


# ══════════════════════════════════════════════════════════════════════════════
# approval_node
# ══════════════════════════════════════════════════════════════════════════════
class TestApprovalNode:
    def test_sets_agent_reply(self):
        state = make_state(
            requires_approval=True,
            approval_token="tok-abc-999",
        )
        result = approval_node(state)
        assert "approval" in result["agent_reply"].lower() or "approve" in result["agent_reply"].lower()

    def test_token_appears_in_reply(self):
        state = make_state(approval_token="tok-abc-999")
        result = approval_node(state)
        assert "tok-abc-999" in result["agent_reply"]


# ══════════════════════════════════════════════════════════════════════════════
# responder_node
# ══════════════════════════════════════════════════════════════════════════════
class TestResponderNode:
    def test_skips_when_reply_already_set(self):
        state = make_state(agent_reply="I already replied")
        result = responder_node(state)
        # Should return empty dict (nothing to do)
        assert result == {}

    def test_calls_llm_when_no_reply(self):
        state = make_state(agent_reply="")
        mock_llm = _mock_llm_direct("Summary from responder LLM")
        with patch("app.agents.nodes._get_llm_with_tools", return_value=mock_llm):
            result = responder_node(state)
        assert result["agent_reply"] == "Summary from responder LLM"


# ══════════════════════════════════════════════════════════════════════════════
# Routing functions
# ══════════════════════════════════════════════════════════════════════════════
class TestRouting:
    # should_continue
    def test_routes_to_execute_when_tool_set(self):
        state = make_state(next_tool="send_email", iteration=1)
        assert should_continue(state) == "execute"

    def test_routes_to_end_when_no_tool(self):
        state = make_state(next_tool=None)
        assert should_continue(state) == "end"

    def test_routes_to_end_when_max_iterations(self):
        state = make_state(next_tool="send_email", iteration=10, max_iterations=10)
        assert should_continue(state) == "end"

    # after_executor
    def test_routes_to_approve_when_approval_needed(self):
        state = make_state(requires_approval=True, iteration=1)
        assert after_executor(state) == "approve"

    def test_routes_to_plan_when_no_approval_and_iterations_left(self):
        state = make_state(requires_approval=False, iteration=1, max_iterations=10)
        assert after_executor(state) == "plan"

    def test_routes_to_end_when_iteration_limit(self):
        state = make_state(requires_approval=False, iteration=10, max_iterations=10)
        assert after_executor(state) == "end"
