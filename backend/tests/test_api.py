"""
test_api.py — Integration tests for FastAPI endpoints.

Uses TestClient (no real server, no real LLM — patches agent_graph.invoke).
Tests the full request→response cycle through FastAPI middleware,
route validation, and response serialisation.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.agents.state import AgentState
from langchain_core.messages import HumanMessage, AIMessage


# ─── Helpers ──────────────────────────────────────────────────────────────────
def make_final_state(reply: str, tool_calls=None, requires_approval=False, token=None):
    """Build a fake AgentState that agent_graph.invoke() will return."""
    state = AgentState(
        messages=[HumanMessage(content="test"), AIMessage(content=reply)],
        session_id="test-session",
        user_id="test-user",
        user_input="test",
        agent_reply=reply,
        tool_calls=tool_calls or [],
        requires_approval=requires_approval,
        approval_token=token,
    )
    return state


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ══════════════════════════════════════════════════════════════════════════════
# GET /health
# ══════════════════════════════════════════════════════════════════════════════
class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_body(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"
        assert "service" in data


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/chat
# ══════════════════════════════════════════════════════════════════════════════
class TestChatEndpoint:
    def test_valid_request_returns_200(self, client):
        fake_state = make_final_state("Hello! I can help with that.")
        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.return_value = fake_state
            resp = client.post("/api/chat", json={
                "message": "Hello agent",
                "session_id": "sess-001",
                "user_id": "user-001",
            })
        assert resp.status_code == 200

    def test_reply_in_response(self, client):
        fake_state = make_final_state("I scheduled the meeting!")
        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.return_value = fake_state
            resp = client.post("/api/chat", json={"message": "Schedule a meeting"})
        data = resp.json()
        assert data["reply"] == "I scheduled the meeting!"

    def test_session_id_returned(self, client):
        fake_state = make_final_state("Done")
        fake_state.session_id = "my-session-xyz"
        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.return_value = fake_state
            resp = client.post("/api/chat", json={
                "message": "Do something",
                "session_id": "my-session-xyz",
            })
        data = resp.json()
        assert data["session_id"] == "my-session-xyz"

    def test_tool_calls_in_response(self, client):
        tool_records = [{
            "tool_name": "create_task",
            "input_data": {"title": "Test"},
            "output": {"status": "ok", "task": {"task_id": "task_0001"}},
            "success": True,
        }]
        fake_state = make_final_state("Task created!", tool_calls=tool_records)
        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.return_value = fake_state
            resp = client.post("/api/chat", json={"message": "Create a task"})
        data = resp.json()
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool_name"] == "create_task"

    def test_requires_approval_response(self, client):
        fake_state = make_final_state(
            "Please approve",
            requires_approval=True,
            token="tok-approval-123",
        )
        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.return_value = fake_state
            resp = client.post("/api/chat", json={"message": "Send an email"})
        data = resp.json()
        assert data["requires_approval"] is True
        assert data["approval_token"] == "tok-approval-123"

    def test_empty_message_returns_422(self, client):
        resp = client.post("/api/chat", json={"message": ""})
        assert resp.status_code == 422

    def test_missing_message_returns_422(self, client):
        resp = client.post("/api/chat", json={"session_id": "s1"})
        assert resp.status_code == 422

    def test_agent_error_returns_500(self, client):
        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.side_effect = RuntimeError("LLM API is down")
            resp = client.post("/api/chat", json={"message": "hello"})
        assert resp.status_code == 500
        assert "Agent error" in resp.json()["detail"]

    def test_fallback_reply_when_agent_reply_empty(self, client):
        fake_state = make_final_state("")    # empty reply
        fake_state.agent_reply = ""
        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.return_value = fake_state
            resp = client.post("/api/chat", json={"message": "hello"})
        data = resp.json()
        assert data["reply"] != ""            # fallback message used


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/history/{session_id}
# ══════════════════════════════════════════════════════════════════════════════
class TestHistoryEndpoint:
    def test_empty_history_for_new_session(self, client):
        resp = client.get("/api/history/brand-new-session-999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["messages"] == []
        assert data["session_id"] == "brand-new-session-999"

    def test_history_populated_after_chat(self, client):
        session = "history-test-session-abc"
        fake_state = make_final_state("I remember this conversation!")
        fake_state.session_id = session

        with patch("app.api.routes_chat.agent_graph") as mock_graph:
            mock_graph.invoke.return_value = fake_state
            client.post("/api/chat", json={
                "message": "Remember me",
                "session_id": session,
            })

        resp = client.get(f"/api/history/{session}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/approve
# ══════════════════════════════════════════════════════════════════════════════
class TestApproveEndpoint:
    def test_approve_returns_200(self, client):
        resp = client.post("/api/approve", params={
            "approval_token": "tok-test-001",
            "approved": True,
            "session_id": "sess-001",
        })
        assert resp.status_code == 200

    def test_approve_body_contains_token(self, client):
        resp = client.post("/api/approve", params={
            "approval_token": "tok-xyz",
            "approved": True,
            "session_id": "sess-001",
        })
        data = resp.json()
        assert data["approval_token"] == "tok-xyz"
        assert data["approved"] is True

    def test_reject_returns_200(self, client):
        resp = client.post("/api/approve", params={
            "approval_token": "tok-xyz",
            "approved": False,
            "session_id": "sess-001",
        })
        assert resp.status_code == 200
        assert resp.json()["approved"] is False
