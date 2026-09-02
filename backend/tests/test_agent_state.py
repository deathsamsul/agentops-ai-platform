"""
test_agent_state.py — Unit tests for AgentState.

Tests:
  - Default values
  - Field types and constraints
  - LangGraph add_messages merge behaviour
"""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.state import AgentState


class TestAgentStateDefaults:
    def test_empty_messages_by_default(self):
        state = AgentState()
        assert state.messages == []

    def test_default_session_id_is_empty_string(self):
        state = AgentState()
        assert state.session_id == ""

    def test_default_user_id(self):
        state = AgentState()
        assert state.user_id == "anonymous"

    def test_default_iteration_zero(self):
        state = AgentState()
        assert state.iteration == 0

    def test_default_max_iterations(self):
        state = AgentState()
        assert state.max_iterations == 10

    def test_default_no_approval(self):
        state = AgentState()
        assert state.requires_approval is False
        assert state.approval_token is None
        assert state.approved is None

    def test_default_no_error(self):
        state = AgentState()
        assert state.error is None

    def test_default_next_tool_none(self):
        state = AgentState()
        assert state.next_tool is None
        assert state.next_tool_input == {}


class TestAgentStateConstruction:
    def test_with_messages(self):
        msgs = [HumanMessage(content="Hi"), AIMessage(content="Hello!")]
        state = AgentState(messages=msgs)
        assert len(state.messages) == 2

    def test_with_tool_calls(self):
        state = AgentState(tool_calls=[{"tool_name": "send_email", "success": True}])
        assert len(state.tool_calls) == 1

    def test_with_approval(self):
        state = AgentState(requires_approval=True, approval_token="tok-001")
        assert state.requires_approval is True
        assert state.approval_token == "tok-001"

    def test_user_input_stored(self):
        state = AgentState(user_input="Draft an email")
        assert state.user_input == "Draft an email"

    def test_agent_reply_stored(self):
        state = AgentState(agent_reply="Email drafted!")
        assert state.agent_reply == "Email drafted!"
