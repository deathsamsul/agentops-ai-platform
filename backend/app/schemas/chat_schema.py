"""
chat_schema.py — Pydantic models for the /chat endpoint.
FastAPI uses these to:
  1. Validate incoming JSON requests.
  2. Serialise outgoing responses.
  3. Auto-generate OpenAPI docs at /docs.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """What the frontend sends to POST /api/chat."""
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(default="anonymous")


class ToolCall(BaseModel):
    """One tool the agent called during its reasoning loop."""
    tool_name: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    success: bool = True


class ChatResponse(BaseModel):
    """What POST /api/chat returns."""
    session_id: str
    reply: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    requires_approval: bool = False
    approval_token: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(BaseModel):
    """Single message in conversation history."""
    role: str        # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)