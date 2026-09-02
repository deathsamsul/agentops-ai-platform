"""
test_tools.py — Unit tests for tools layer.

Tests:
  - BaseTool contract (name, description, execute, success/error helpers)
  - Every mock tool returns correct shape
  - Registry: register, get, list, duplicate detection
  - Executor: happy path, unknown tool, exception safety
"""

from __future__ import annotations

import pytest
from app.tools.base import BaseTool
from app.tools.mock_tools import (
    EmailTool,
    CalendarTool,
    DatabaseTool,
    BookingTool,
    SearchDocsTool,
)
from app.tools.registry import ToolRegistry
from app.tools.executor import PythonToolExecutor


# ══════════════════════════════════════════════════════════════════════════════
# BaseTool helpers
# ══════════════════════════════════════════════════════════════════════════════
class _DummyTool(BaseTool):
    name = "dummy_tool"
    description = "A tool used only in tests."

    def execute(self, data):
        return self.success(echo=data.get("value"))


def test_base_tool_success_shape():
    t = _DummyTool()
    result = t.execute({"value": "hello"})
    assert result["status"] == "ok"
    assert result["tool"] == "dummy_tool"
    assert result["echo"] == "hello"


def test_base_tool_error_shape():
    t = _DummyTool()
    err = t.error("something broke")
    assert err["status"] == "error"
    assert err["tool"] == "dummy_tool"
    assert "something broke" in err["message"]


def test_base_tool_schema_has_name():
    t = _DummyTool()
    schema = t.schema()
    assert schema["name"] == "dummy_tool"


def test_base_tool_repr():
    t = _DummyTool()
    assert "dummy_tool" in repr(t)


# ══════════════════════════════════════════════════════════════════════════════
# EmailTool
# ══════════════════════════════════════════════════════════════════════════════
class TestEmailTool:
    def setup_method(self):
        self.tool = EmailTool()

    def test_name(self):
        assert self.tool.name == "send_email"

    def test_returns_ok_status(self):
        result = self.tool.execute({
            "to": "boss@company.com",
            "subject": "Weekly update",
            "body": "Hi, here is the update.",
        })
        assert result["status"] == "ok"

    def test_requires_approval(self):
        result = self.tool.execute({"to": "a@b.com", "subject": "s", "body": "b"})
        assert result["requires_approval"] is True

    def test_draft_contains_fields(self):
        result = self.tool.execute({"to": "x@y.com", "subject": "Sub", "body": "Body"})
        draft = result["draft"]
        assert draft["to"] == "x@y.com"
        assert draft["subject"] == "Sub"
        assert draft["body"] == "Body"

    def test_schema_has_input_schema(self):
        schema = self.tool.schema()
        assert "to" in schema["input_schema"]
        assert "subject" in schema["input_schema"]
        assert "body" in schema["input_schema"]

    def test_missing_fields_use_defaults(self):
        # Should not raise even with empty input
        result = self.tool.execute({})
        assert result["status"] == "ok"


# ══════════════════════════════════════════════════════════════════════════════
# CalendarTool
# ══════════════════════════════════════════════════════════════════════════════
class TestCalendarTool:
    def setup_method(self):
        self.tool = CalendarTool()

    def test_name(self):
        assert self.tool.name == "schedule_meeting"

    def test_returns_ok(self):
        result = self.tool.execute({
            "title": "Sprint planning",
            "date": "2025-06-10T10:00:00",
            "attendees": ["alice@co.com", "bob@co.com"],
        })
        assert result["status"] == "ok"

    def test_event_has_expected_keys(self):
        result = self.tool.execute({"title": "T", "date": "2025-01-01", "attendees": []})
        event = result["event"]
        for key in ("event_id", "title", "date", "attendees", "created_at"):
            assert key in event, f"Missing key: {key}"

    def test_no_approval_required(self):
        result = self.tool.execute({"title": "T", "date": "2025-01-01", "attendees": []})
        assert result.get("requires_approval", False) is False


# ══════════════════════════════════════════════════════════════════════════════
# DatabaseTool (create_task)
# ══════════════════════════════════════════════════════════════════════════════
class TestDatabaseTool:
    def setup_method(self):
        self.tool = DatabaseTool()
        self.tool._tasks = []   # reset in-memory store between tests

    def test_name(self):
        assert self.tool.name == "create_task"

    def test_creates_task(self):
        result = self.tool.execute({"title": "Write tests", "priority": "high"})
        assert result["status"] == "ok"
        assert result["task"]["title"] == "Write tests"

    def test_task_has_id(self):
        result = self.tool.execute({"title": "Check CI"})
        assert result["task"]["task_id"].startswith("task_")

    def test_task_stored_in_memory(self):
        self.tool.execute({"title": "Task A"})
        self.tool.execute({"title": "Task B"})
        assert len(self.tool._tasks) == 2

    def test_default_priority(self):
        result = self.tool.execute({"title": "No priority given"})
        assert result["task"]["priority"] == "medium"

    def test_default_status_is_pending(self):
        result = self.tool.execute({"title": "New task"})
        assert result["task"]["status"] == "pending"


# ══════════════════════════════════════════════════════════════════════════════
# BookingTool
# ══════════════════════════════════════════════════════════════════════════════
class TestBookingTool:
    def setup_method(self):
        self.tool = BookingTool()

    def test_name(self):
        assert self.tool.name == "book_resource"

    def test_requires_approval(self):
        result = self.tool.execute({"resource": "Conference Room A", "date": "2025-06-15"})
        assert result["requires_approval"] is True

    def test_booking_pending_status(self):
        result = self.tool.execute({"resource": "Projector", "date": "2025-06-20"})
        assert result["booking"]["status"] == "pending_approval"


# ══════════════════════════════════════════════════════════════════════════════
# SearchDocsTool
# ══════════════════════════════════════════════════════════════════════════════
class TestSearchDocsTool:
    def setup_method(self):
        self.tool = SearchDocsTool()

    def test_name(self):
        assert self.tool.name == "search_docs"

    def test_returns_results_list(self):
        result = self.tool.execute({"query": "LangGraph architecture"})
        assert result["status"] == "ok"
        assert isinstance(result["results"], list)
        assert len(result["results"]) > 0

    def test_result_has_score(self):
        result = self.tool.execute({"query": "pgvector"})
        chunk = result["results"][0]
        assert "score" in chunk
        assert "text" in chunk


# ══════════════════════════════════════════════════════════════════════════════
# ToolRegistry
# ══════════════════════════════════════════════════════════════════════════════
class TestToolRegistry:
    def setup_method(self):
        # Fresh registry for each test — don't touch the global one
        self.registry = ToolRegistry()

    def test_register_and_get(self):
        self.registry.register(_DummyTool())
        tool = self.registry.get("dummy_tool")
        assert tool.name == "dummy_tool"

    def test_get_unknown_raises_key_error(self):
        with pytest.raises(KeyError, match="unknown_tool"):
            self.registry.get("unknown_tool")

    def test_duplicate_register_raises(self):
        self.registry.register(_DummyTool())
        with pytest.raises(ValueError, match="already registered"):
            self.registry.register(_DummyTool())

    def test_list_names(self):
        self.registry.register(_DummyTool())
        names = self.registry.list_names()
        assert "dummy_tool" in names

    def test_contains(self):
        self.registry.register(_DummyTool())
        assert "dummy_tool" in self.registry
        assert "nonexistent" not in self.registry

    def test_all_schemas(self):
        self.registry.register(_DummyTool())
        schemas = self.registry.all_schemas()
        assert any(s["name"] == "dummy_tool" for s in schemas)


# ══════════════════════════════════════════════════════════════════════════════
# PythonToolExecutor
# ══════════════════════════════════════════════════════════════════════════════
class TestPythonToolExecutor:
    def setup_method(self):
        # Use a fresh registry + executor — don't touch the global singleton
        from app.tools.registry import ToolRegistry
        self.registry = ToolRegistry()
        self.registry.register(_DummyTool())
        self.registry.register(DatabaseTool())

        from app.tools.executor import PythonToolExecutor
        self.executor = PythonToolExecutor()
        # Patch the executor's internal registry reference
        self.executor._registry = self.registry

    def test_execute_known_tool(self):
        # Using the global executor which has the real registry
        from app.tools.executor import executor
        result = executor.execute("create_task", {"title": "Executor test task"})
        assert result["status"] == "ok"

    def test_execute_unknown_tool_returns_error(self):
        from app.tools.executor import executor
        result = executor.execute("tool_that_does_not_exist", {})
        assert result["status"] == "error"
        assert "unknown" in result["message"].lower() or "Unknown" in result["message"]

    def test_list_tools_returns_list(self):
        from app.tools.executor import executor
        names = executor.list_tools()
        assert isinstance(names, list)
        assert len(names) >= 5   # we registered 5 mock tools

    def test_tool_schemas_returns_list_of_dicts(self):
        from app.tools.executor import executor
        schemas = executor.tool_schemas()
        assert all("name" in s for s in schemas)
