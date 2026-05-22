# Enterprise AI Agent Platform

Autonomous AI operations platform built with ** AI MODEL API + FastAPI + LangGraph + LangChain + PostgreSQL + Streamlit **.

## Architecture

```
Streamlit UI
     ↓
FastAPI Gateway  (/api/chat, /api/approve, /api/history)
     ↓
LangGraph Agent  (planner → executor → approval → responder)
     ↓
Tool Executor    (Phase 1: Python tools | Phase 8: MCP servers)
     ↓
PostgreSQL + pgvector  (Phase 2+)
```

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env → add your OPENAI_API_KEY (or ANTHROPIC_API_KEY)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# 4. Start frontend (new terminal)
cd frontend
streamlit run streamlit_app.py
```

Open http://localhost:8501 — you should see the chat UI.
Open http://localhost:8000/docs — FastAPI interactive docs.

## Project Structure

```
enterprise-ai-agent-platform/
├── .env.example                  ← environment variables template
├── requirements.txt
├── backend/app/
│   ├── main.py                   ← FastAPI app + routers
│   ├── config.py                 ← settings from .env
│   ├── api/
│   │   └── routes_chat.py        ← /chat, /history, /approve endpoints
│   ├── agents/
│   │   ├── state.py              ← AgentState (LangGraph shared memory)
│   │   ├── nodes.py              ← planner, executor, approval, responder
│   │   └── graph.py              ← LangGraph workflow wiring
│   ├── tools/
│   │   ├── base.py               ← BaseTool interface
│   │   ├── registry.py           ← tool name → instance mapping
│   │   ├── executor.py           ← PythonToolExecutor + MCPToolExecutor stub
│   │   └── mock_tools.py         ← simulated email/calendar/task/RAG tools
│   └── schemas/
│       └── chat_schema.py        ← Pydantic request/response models
└── frontend/
    └── streamlit_app.py          ← chat UI with approval widget
```

## Build Phases

| Phase | Goal | Status |
|-------|------|--------|
| 1 | FastAPI + LangGraph + Streamlit | ✅ **This file** |
| 2 | PostgreSQL + real tools | 🔜 |
| 3 | Stateful workflows + approval service | 🔜 |
| 4 | RAG + pgvector | 🔜 |
| 5 | Multi-agent system | 🔜 |
| 6 | Prometheus + Grafana + OpenTelemetry | 🔜 |
| 7 | Kubernetes deployment | 🔜 |
| 8 | MCP server integration | 🔜 |

## Supported LLM Providers

Set `MODEL_PROVIDER` in `.env`:
- `openai` → GPT-4o (default)
- `anthropic` → Claude Sonnet
- `ollama` → local model (no API key needed)
