from __future__ import annotations
from datetime import datetime
from typing import Any
from app.tools.base import BaseTool



"""
tools/mock_tools.py — Simulated tools for Phase 1 development.
These tools return realistic fake responses so you can build and test
the agent loop WITHOUT needing real email servers, calendar APIs, etc.
Upgrade path:
  - Replace each mock with a real implementation in its own file:
      email_tool.py, calendar_tool.py, postgres_tool.py, rag_tool.py
  - Keep the same class name and execute() signature so registry.py
    needs zero changes.
"""

# TODO ; if user send message with approval then directly execute task without asking approval again

# ─── Email Tool ───────────────────────────────────────────────────────────────
class EmailTool(BaseTool):
    name = "send_email"
    description = (
        "Draft and send an email. "
        "Requires: to (str), subject (str), body (str). "
        "Returns a draft for user approval before sending."
    )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        to      = data.get("to", "unknown@example.com")
        subject = data.get("subject", "(no subject)")
        body    = data.get("body", "")

        # MOCK: In Phase 2, call real SMTP / Gmail API here
        draft = {
            "to": to,
            "subject": subject,
            "body": body,
            "drafted_at": datetime.utcnow().isoformat(),     # utcnow() is important to show the email is "freshly drafted" each time
        }
        return self.success(
            draft=draft,
            message=f"Email to '{to}' drafted. Awaiting user approval to send.",
            requires_approval=True,
        )

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
        }


# ─── Calendar Tool ────────────────────────────────────────────────────────────
class CalendarTool(BaseTool):
    name = "schedule_meeting"
    description = (
        "Schedule a calendar meeting. "
        "Requires: title (str), date (str ISO-8601), attendees (list[str]). "
        "Returns the created event details."
    )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        title     = data.get("title", "Meeting")
        date      = data.get("date", datetime.utcnow().date().isoformat())
        attendees = data.get("attendees", [])

        # MOCK: In Phase 2, call Google Calendar / Outlook API here
        event = {
            "event_id": "evt_mock_001",
            "title": title,
            "date": date,
            "attendees": attendees,
            "location": "Google Meet (link will be generated)",
            "created_at": datetime.utcnow().isoformat(),
        }
        return self.success(event=event, message=f"Meeting '{title}' scheduled for {date}.")

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "title": {"type": "string"},
                "date": {"type": "string", "description": "ISO-8601 date, e.g. 2025-06-01T14:00:00"},
                "attendees": {"type": "array", "items": {"type": "string"}},
            },
        }


# ─── Database / Task Tool ─────────────────────────────────────────────────────
class DatabaseTool(BaseTool):
    name = "create_task"
    description = (
        "Create a task in the database. "
        "Requires: title (str). Optional: due_date (str), priority (str)."
    )

    # In-memory store for Phase 1 (replace with PostgreSQL in Phase 2)
    _tasks: list[dict] = []

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        task = {
            "task_id": f"task_{len(self._tasks) + 1:04d}",
            "title": data.get("title", "Untitled task"),
            "due_date": data.get("due_date"),
            "priority": data.get("priority", "medium"),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }
        self._tasks.append(task)
        return self.success(task=task, message=f"Task '{task['title']}' created.")

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "title": {"type": "string"},
                "due_date": {"type": "string", "description": "Optional ISO-8601 date"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            },
        }


# ─── Booking Tool (mock) ──────────────────────────────────────────────────────
class BookingTool(BaseTool):
    name = "book_resource"
    description = (
        "Book a resource (room, equipment, service). "
        "Requires: resource (str), date (str). "
        "Always asks for approval — never books automatically."
    )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        resource = data.get("resource", "unknown")
        date     = data.get("date", "TBD")

        booking = {
            "booking_id": "bkg_mock_001",
            "resource": resource,
            "date": date,
            "status": "pending_approval",
        }
        return self.success(
            booking=booking,
            message=f"Booking request for '{resource}' on {date} created. Approval required.",
            requires_approval=True,
        )


# ─── RAG / Document Search Tool ───────────────────────────────────────────────
class SearchDocsTool(BaseTool):
    name = "search_docs"
    description = (
        "Search the internal knowledge base (RAG). "
        "Requires: query (str). "
        "Returns relevant document chunks."
    )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        query = data.get("query", "")

        # MOCK: In Phase 4, call pgvector retriever here
        mock_results = [
            {
                "chunk_id": "doc_001_chunk_3",
                "source": "architecture.md",
                "score": 0.91,
                "text": f"[Mock result for query: '{query}'] "
                        "The platform uses LangGraph for stateful agent workflows "
                        "and pgvector for semantic document retrieval.",
            }
        ]
        return self.success(results=mock_results, query=query, total=len(mock_results))

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "query": {"type": "string", "description": "Natural language search query"},
            },
        }
