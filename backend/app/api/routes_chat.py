from __future__ import annotations
import logging
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage
from app.agents.graph import agent_graph
from app.agents.state import AgentState
from app.schemas.chat_schema import ChatRequest, ChatResponse, ToolCall


"""
api/routes_chat.py — FastAPI router for chat endpoints.
Endpoints:
  POST /api/chat           — send a message, get agent reply
  GET  /api/history/{sid} — fetch conversation history for a session
  POST /api/approve        — approve a pending agent action

This file is intentionally thin. Business logic lives in the agent graph
and services, not here.

At first it has:
old messages + latest user message
session_id
user_id
user_input

Other fields are default:
agent_reply = ""
tool_calls = []
next_tool = None
next_tool_input = {}
iteration = 0
requires_approval = False
approval_token = None
error = None
"""

# TODO real approval, you need storage _pending_approvals = {}
# TODO use uuid4 for session id
# TODO add authentication and associate sessions with users
# TODO async function with await if langgraph supports async execution in the future
# TODO ainvoke should be async final_state = await agent_graph.ainvoke(initial_state)

logger = logging.getLogger(__name__)   # name means python file name  app.api.routes_chat
router = APIRouter()

# In-memory session store — replace with PostgreSQL in Phase 2
_sessions: dict[str, list] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.
    Flow:
      1. Build AgentState from the request
      2. Run the LangGraph agent graph
      3. Extract reply, tool calls, and approval info
      4. Return ChatResponse
    """
    logger.info("Chat request: session=%s user=%s msg='%s'",
                request.session_id, request.user_id, request.message[:80])

    # Build initial state
    history = _sessions.get(request.session_id, [])
    initial_state = AgentState(
        messages=history + [HumanMessage(content=request.user_input)],     # HumanMessage represents a message sent by the user/human to an AI model
        session_id=request.session_id,                                     # LangChain stores that as a HumanMessage.
        user_id=request.user_id,
        user_input=request.message,)


    # Run the agent graph
    try:
        final_state: AgentState = agent_graph.invoke(initial_state)
    except Exception as exc:
        logger.exception("Agent graph error")
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    # Persist updated conversation history
    _sessions[request.session_id] = list(final_state.messages)

    # Build response
    tool_calls = [
        ToolCall(
            tool_name=tc["tool_name"],
            input_data=tc.get("input_data", {}),
            output=tc.get("output"),
            success=tc.get("success", True),
        )
        for tc in final_state.tool_calls
    ]

    return ChatResponse(
        session_id=request.session_id,
        reply=final_state.agent_reply or "I'm sorry, I could not generate a response.",
        tool_calls=tool_calls,
        requires_approval=final_state.requires_approval,
        approval_token=final_state.approval_token,
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str):
# fetch conversation history for a session This converts LangChain message objects into simple JSON structures with "role" and "content" for the frontend to display.
    """Return conversation history for a session."""
    messages = _sessions.get(session_id, [])
    # TODO role = "human" if isinstance(m, HumanMessage) else "assistant"
    history = [
        {"role": "human" if m.__class__.__name__ == "HumanMessage" else "assistant",
         "content": m.content}
        for m in messages
    ]
    return {"session_id": session_id, "messages": history}


@router.post("/approve")
async def approve_action(approval_token: str, approved: bool, session_id: str):  
    # Unique token for the pending action ,Which conversation this approval belongs to.
    """
    Frontend calls this to approve or reject a pending agent action.

    Phase 3 will implement proper resumable workflows via LangGraph checkpoints.
    For now this is a stub that logs the decision.
    """
    logger.info("Approval decision: token=%s approved=%s session=%s",
                approval_token, approved, session_id)
# For real app, need store pending approvals somewhere use LangGraph checkpointer
    # TODO Phase 3: resume the paused workflow using LangGraph checkpointer
    return {
        "approval_token": approval_token,
        "approved": approved,
        "message": "Decision recorded. Full resumable workflow coming in Phase 3.",
    }
