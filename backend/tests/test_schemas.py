"""
test_schemas.py — Unit tests for Pydantic schemas.

Tests:
  - ChatRequest: valid input, missing required field, field constraints
  - ChatResponse: correct defaults, tool_calls structure
  - ToolCall: success/failure shape
  - auto-generated session_id and timestamp
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from app.schemas.chat_schema import ChatRequest, ChatResponse, ToolCall, ChatMessage


# ══════════════════════════════════════════════════════════════════════════════
# ChatRequest
# ══════════════════════════════════════════════════════════════════════════════
class TestChatRequest:
    def test_valid_minimal(self):
        req = ChatRequest(message="Hello agent")
        assert req.message == "Hello agent"
        assert req.user_id == "anonymous"
        assert req.session_id != ""          # auto-generated UUID

    def test_valid_full(self):
        req = ChatRequest(
            message="Schedule a meeting",
            session_id="sess-abc-123",
            user_id="user-42",
        )
        assert req.session_id == "sess-abc-123"
        assert req.user_id == "user-42"

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest()
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("message",) for e in errors)

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")            # min_length=1

    def test_message_too_long_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 4001)   # max_length=4000

    def test_session_id_auto_generated_is_unique(self):
        r1 = ChatRequest(message="a")
        r2 = ChatRequest(message="b")
        assert r1.session_id != r2.session_id

    def test_message_boundary_ok(self):
        # Exactly 4000 chars should pass
        req = ChatRequest(message="a" * 4000)
        assert len(req.message) == 4000


# ══════════════════════════════════════════════════════════════════════════════
# ToolCall
# ══════════════════════════════════════════════════════════════════════════════
class TestToolCall:
    def test_defaults(self):
        tc = ToolCall(tool_name="send_email")
        assert tc.input_data == {}
        assert tc.output is None
        assert tc.success is True

    def test_failure_flag(self):
        tc = ToolCall(tool_name="send_email", success=False, output={"error": "timeout"})
        assert tc.success is False

    def test_full_construction(self):
        tc = ToolCall(
            tool_name="create_task",
            input_data={"title": "Test"},
            output={"task_id": "task_0001"},
            success=True,
        )
        assert tc.tool_name == "create_task"


# ══════════════════════════════════════════════════════════════════════════════
# ChatResponse
# ══════════════════════════════════════════════════════════════════════════════
class TestChatResponse:
    def test_minimal_valid(self):
        resp = ChatResponse(session_id="s1", reply="Done!")
        assert resp.reply == "Done!"
        assert resp.tool_calls == []
        assert resp.requires_approval is False
        assert resp.approval_token is None
        assert resp.timestamp is not None

    def test_with_tool_calls(self):
        tc = ToolCall(tool_name="send_email", success=True)
        resp = ChatResponse(session_id="s1", reply="Email drafted", tool_calls=[tc])
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].tool_name == "send_email"

    def test_requires_approval_with_token(self):
        resp = ChatResponse(
            session_id="s1",
            reply="Please approve",
            requires_approval=True,
            approval_token="tok-abc-123",
        )
        assert resp.requires_approval is True
        assert resp.approval_token == "tok-abc-123"

    def test_missing_reply_raises(self):
        with pytest.raises(ValidationError):
            ChatResponse(session_id="s1")


# ══════════════════════════════════════════════════════════════════════════════
# ChatMessage
# ══════════════════════════════════════════════════════════════════════════════
class TestChatMessage:
    def test_user_role(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_assistant_role(self):
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"

    def test_timestamp_auto(self):
        msg = ChatMessage(role="user", content="test")
        assert msg.timestamp is not None
