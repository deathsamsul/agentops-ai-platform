"""
streamlit_app.py — Enterprise AI Agent Platform frontend.

Run with:
    streamlit run frontend/streamlit_app.py

Pages:
  This file = Chat UI (main page)
  pages/    = Tasks, Workflows, Documents (add in Phase 2+)
"""

from __future__ import annotations

import uuid
from datetime import datetime

import requests
import streamlit as st

# ─── Config ───────────────────────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Enterprise AI Agent",
    page_icon="🤖",
    layout="wide",
)

# ─── Session state initialisation ─────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []          # list of {"role", "content", "meta"}

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None    # {"token": str, "summary": str}


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 AI Agent Platform")
    st.caption("Enterprise Autonomous Operations")
    st.divider()

    st.markdown("**Session**")
    st.code(st.session_state.session_id[:8] + "…", language=None)

    if st.button("🔄 New session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.pending_approval = None
        st.rerun()

    st.divider()
    st.markdown("**Quick actions**")
    examples = [
        "Draft an email to my manager about the project update",
        "Schedule a meeting with the team tomorrow at 3pm",
        "Create a task: review the Q3 report by Friday",
        "Search documents for deployment architecture",
        "Book the large conference room for next Monday",
    ]
    for example in examples:
        if st.button(example, use_container_width=True, key=f"ex_{example[:20]}"):
            st.session_state._quick_msg = example
            st.rerun()

    st.divider()
    # Backend health check
    try:
        r = requests.get(f"{BACKEND_URL.replace('/api', '')}/health", timeout=2)
        if r.status_code == 200:
            st.success("✅ Backend online")
        else:
            st.warning("⚠️ Backend unhealthy")
    except Exception:
        st.error("❌ Backend offline")


# ─── Main area ────────────────────────────────────────────────────────────────
st.title("💬 Enterprise AI Agent")
st.caption("Autonomous AI operations platform · Phase 1")

# Show conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show tool calls if present
        if msg.get("tool_calls"):
            with st.expander(f"🔧 {len(msg['tool_calls'])} tool call(s)", expanded=False):
                for tc in msg["tool_calls"]:
                    status_icon = "✅" if tc.get("success") else "❌"
                    st.markdown(f"**{status_icon} {tc['tool_name']}**")
                    st.json({"input": tc.get("input_data", {}), "output": tc.get("output", {})})


# ─── Approval widget ─────────────────────────────────────────────────────────
if st.session_state.pending_approval:
    st.warning("⏸ **Agent is waiting for your approval** before proceeding.")
    token = st.session_state.pending_approval["token"]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve", type="primary", use_container_width=True):
            _send_approval(token, approved=True)
    with col2:
        if st.button("❌ Reject", use_container_width=True):
            _send_approval(token, approved=False)


# ─── Chat input ──────────────────────────────────────────────────────────────
# Handle quick-action button clicks
pre_fill = st.session_state.pop("_quick_msg", None)
user_input = st.chat_input("Ask the agent to do something…") or pre_fill

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Agent thinking…"):
            response = _call_backend(user_input)

        if response:
            st.markdown(response["reply"])

            if response.get("tool_calls"):
                with st.expander(f"🔧 {len(response['tool_calls'])} tool call(s)", expanded=True):
                    for tc in response["tool_calls"]:
                        status_icon = "✅" if tc.get("success") else "❌"
                        st.markdown(f"**{status_icon} {tc['tool_name']}**")
                        st.json({"input": tc.get("input_data", {}), "output": tc.get("output", {})})

            # Approval required?
            if response.get("requires_approval") and response.get("approval_token"):
                st.session_state.pending_approval = {
                    "token": response["approval_token"],
                }
                st.rerun()

        # Save assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["reply"] if response else "⚠️ No response from backend.",
            "tool_calls": response.get("tool_calls", []) if response else [],
        })


# ─── Helper functions ─────────────────────────────────────────────────────────
def _call_backend(message: str) -> dict | None:
    """POST /api/chat and return the response dict."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "user_id": "streamlit_user",
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot reach the backend. Is it running? (`uvicorn app.main:app --reload`)")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱ Request timed out. The agent may be processing a complex task.")
        return None
    except Exception as exc:
        st.error(f"Backend error: {exc}")
        return None


def _send_approval(token: str, approved: bool):
    """POST /api/approve with the user's decision."""
    try:
        requests.post(
            f"{BACKEND_URL}/approve",
            params={
                "approval_token": token,
                "approved": approved,
                "session_id": st.session_state.session_id,
            },
            timeout=10,
        )
        st.session_state.pending_approval = None
        action = "approved ✅" if approved else "rejected ❌"
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Action {action} by user.",
        })
        st.rerun()
    except Exception as exc:
        st.error(f"Approval error: {exc}")
