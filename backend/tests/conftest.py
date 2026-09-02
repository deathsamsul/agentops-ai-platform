"""
conftest.py — Pytest fixtures shared across all test files.

What lives here:
  - FastAPI test client (no real server needed)
  - A minimal AgentState factory
  - A mock LLM that never calls OpenAI (fast, free, deterministic)
  - A mock executor that never runs real tools
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage

from app.main import app
from app.agents.state import AgentState


# ─── FastAPI test client 
@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Returns a synchronous TestClient wrapping the FastAPI app.
    No real server is started — requests go directly to the ASGI app.
    """
    with TestClient(app) as c:
        yield c


# ─── Minimal AgentState factory
def base_state() -> AgentState:
    """A clean AgentState for unit-testing nodes in isolation."""
    return AgentState(
        messages=[HumanMessage(content="Hello agent")],
        session_id="test-session-001",
        user_id="test-user",
        user_input="Hello agent",
    )


# ─── Mock LLM (no API calls, no cost) 
@pytest.fixture
def mock_llm_direct_reply():
    """
    Patches _get_llm_with_tools() so the planner returns a plain text reply
    without calling any tool. Use for testing the direct-reply code path.
    """
    fake_response = AIMessage(content="Hello! I am the mock agent reply.")
    fake_response.tool_calls = []          # no tool calls

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = fake_response
    mock_llm.bind_tools.return_value = mock_llm

    with patch("app.agents.nodes._get_llm_with_tools", return_value=mock_llm):
        yield mock_llm


@pytest.fixture
def mock_llm_tool_call():
    """
    Patches _get_llm_with_tools() so the planner requests a tool call.
    Use for testing the tool-execution code path.
    """
    fake_response = AIMessage(content="")
    fake_response.tool_calls = [{
        "name": "create_task",
        "args": {"title": "Test task from mock LLM", "priority": "high"},
        "id": "mock_tool_call_id_001",
    }]

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = fake_response
    mock_llm.bind_tools.return_value = mock_llm

    with patch("app.agents.nodes._get_llm_with_tools", return_value=mock_llm):
        yield mock_llm
