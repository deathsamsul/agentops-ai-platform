# Run & Test Guide — Enterprise AI Agent Platform

Complete local setup, run, and test instructions for Phase 1.

---

## Prerequisites

| Tool | Minimum version | Check |
|------|----------------|-------|
| Python | 3.11+ | `python --version` |
| pip | any recent | `pip --version` |
| Git | any | `git --version` |

You do NOT need PostgreSQL, Docker, or Kubernetes for Phase 1.
Everything runs in memory.

---

## 1. Project Setup

### 1.1 Clone / enter the project

```bash
cd enterprise-ai-agent-platform
```

### 1.2 Create a virtual environment

Always use a venv. Never install into system Python.

```bash
# Create
python -m venv .venv

# Activate — Linux / macOS
source .venv/bin/activate

# Activate — Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activate — Windows (CMD)
.venv\Scripts\activate.bat
```

You should see `(.venv)` at the start of your terminal prompt.

### 1.3 Install dependencies

```bash
pip install -r requirements.txt
```

This installs: FastAPI, Uvicorn, LangGraph, LangChain, Streamlit, Pytest, and all LLM provider libraries.

---

## 2. Environment Configuration

### 2.1 Create your .env file

```bash
cp .env.example .env
```

### 2.2 Edit .env — pick ONE provider

**Option A — OpenAI (GPT-4o)**
```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=sk-...your-key-here...
LLM_MODEL=gpt-4o
```

**Option B — Anthropic (Claude)**
```env
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
LLM_MODEL=claude-opus-4-6
```

**Option C — Ollama (free, runs locally, no API key)**
```bash
# First install Ollama: https://ollama.ai
ollama pull llama3          # or mistral, phi3, gemma2
```
```env
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3
```

---

## 3. Import Path Setup

The backend uses `from app.xxx import ...` style imports.
You need to tell Python where `app` is.

```bash
# From the project root:
cd backend

# Set PYTHONPATH so `app` resolves correctly
# Linux / macOS:
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Windows PowerShell:
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)"

# Windows CMD:
set PYTHONPATH=%PYTHONPATH%;%CD%
```

Or add this to your .env (python-dotenv picks it up automatically):
```env
PYTHONPATH=./backend
```

---

## 4. Run the Backend

```bash
# Make sure you are in enterprise-ai-agent-platform/backend/
cd backend

uvicorn app.main:app --reload --port 8000
```

Expected output:
```
🚀  Agent platform starting up…
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Verify it works:**
```bash
# In a new terminal (with venv activated)
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"enterprise-ai-agent-platform"}
```

Or open **http://localhost:8000/docs** in your browser for the interactive Swagger UI.

---

## 5. Run the Frontend

Open a **second terminal**, activate venv, then:

```bash
cd enterprise-ai-agent-platform/frontend

streamlit run streamlit_app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

Open **http://localhost:8501** to see the chat UI.

---

## 6. Manual API Testing

### 6.1 Using curl

```bash
# Health check
curl http://localhost:8000/health

# Send a chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a task to review the Q3 report", "session_id": "test-001"}'

# Get conversation history
curl http://localhost:8000/api/history/test-001

# Approve a pending action (replace TOKEN with value from chat response)
curl -X POST "http://localhost:8000/api/approve?approval_token=TOKEN&approved=true&session_id=test-001"
```

### 6.2 Using the Swagger UI (recommended)

1. Open http://localhost:8000/docs
2. Click **POST /api/chat** → **Try it out**
3. Paste this body:
```json
{
  "message": "Draft an email to my manager about the Q3 report",
  "session_id": "swagger-test-001",
  "user_id": "dev"
}
```
4. Click **Execute**
5. Check the response — you will see `requires_approval: true` and a draft email

### 6.3 Manual test checklist

Try each of these messages in the chat UI or Swagger:

| Message | Expected behaviour |
|---------|-------------------|
| `hello` | Direct reply, no tool call |
| `Create a task: finish the report by Friday` | `create_task` tool call, task created |
| `Draft an email to boss@company.com about the sprint review` | `send_email` tool call, `requires_approval: true` |
| `Schedule a team meeting tomorrow at 3pm` | `schedule_meeting` tool call |
| `Search docs for deployment architecture` | `search_docs` tool call |
| `Book conference room A for next Monday` | `book_resource` tool call, `requires_approval: true` |

---

## 7. Running the Tests

All tests are in `backend/tests/`. They use mocked LLMs — no API calls, no cost.

### 7.1 Run all tests

```bash
# From enterprise-ai-agent-platform/backend/
cd backend
pytest
```

### 7.2 Run with verbose output (see each test name)

```bash
pytest -v
```

### 7.3 Run a specific test file

```bash
pytest tests/test_tools.py
pytest tests/test_schemas.py
pytest tests/test_agent_nodes.py
pytest tests/test_api.py
pytest tests/test_agent_state.py
```

### 7.4 Run a specific test class or function

```bash
# Single class
pytest tests/test_tools.py::TestEmailTool

# Single test function
pytest tests/test_tools.py::TestEmailTool::test_requires_approval

# All tests matching a keyword
pytest -k "approval"
pytest -k "email or calendar"
```

### 7.5 Run with coverage report

```bash
pip install pytest-cov

pytest --cov=app --cov-report=term-missing
```

Example output:
```
---------- coverage: platform linux, python 3.11 ----------
Name                              Stmts   Miss  Cover
------------------------------------------------------
app/agents/graph.py                  28      4    86%
app/agents/nodes.py                  72     12    83%
app/agents/state.py                  22      0   100%
app/api/routes_chat.py               38      4    89%
app/schemas/chat_schema.py           18      0   100%
app/tools/base.py                    24      0   100%
app/tools/executor.py                28      8    71%
app/tools/mock_tools.py              58      2    97%
app/tools/registry.py                22      0   100%
------------------------------------------------------
TOTAL                               310     30    90%
```

### 7.6 What each test file covers

| File | What it tests |
|------|--------------|
| `test_tools.py` | BaseTool, all 5 mock tools, ToolRegistry, PythonToolExecutor |
| `test_schemas.py` | ChatRequest validation, ChatResponse, ToolCall, ChatMessage |
| `test_agent_nodes.py` | planner/executor/approval/responder nodes, routing functions |
| `test_agent_state.py` | AgentState defaults and construction |
| `test_api.py` | FastAPI endpoints (200s, 422s, 500s, full request→response) |

---

## 8. Common Errors and Fixes

### `ModuleNotFoundError: No module named 'app'`

You are running pytest or uvicorn from the wrong directory, or PYTHONPATH is not set.

```bash
# Make sure you are in the backend/ directory
cd backend
export PYTHONPATH=$(pwd)
pytest
```

### `ValidationError: MODEL_PROVIDER must be openai | anthropic | ollama`

Your .env file is not being loaded, or MODEL_PROVIDER has a typo.

```bash
# Check your .env exists
cat .env | grep MODEL_PROVIDER

# Make sure python-dotenv is installed
pip install python-dotenv
```

### `ConnectionRefusedError` when Streamlit tries to talk to backend

The backend is not running. Start it first:

```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend && streamlit run streamlit_app.py
```

### `AuthenticationError: 401` from OpenAI / Anthropic

Your API key is wrong or missing from .env.

```bash
# Check it is in the file
cat .env | grep API_KEY

# Check it is being loaded by Python
python -c "from app.config import settings; print(settings.OPENAI_API_KEY[:10])"
```

### `ollama: command not found`

Ollama is not installed. Install it from https://ollama.ai then:

```bash
ollama serve           # Start the Ollama server
ollama pull llama3     # Download the model (one-time, ~4GB)
```

### Tests fail with `ImportError` on `langgraph`

LangGraph is not installed or the wrong version.

```bash
pip install "langgraph>=0.2.0" "langchain>=0.3.0" "langchain-core>=0.3.0"
```

### Port 8000 already in use

```bash
# Find and kill the process using port 8000
# Linux / macOS:
lsof -i :8000 | grep LISTEN
kill -9 <PID>

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 9. Project File Structure Reference

```
enterprise-ai-agent-platform/
├── .env.example                      ← copy to .env, add your API key
├── requirements.txt                  ← all Python dependencies
│
├── backend/
│   ├── pytest.ini                    ← pytest configuration
│   ├── app/
│   │   ├── main.py                   ← FastAPI app: uvicorn app.main:app
│   │   ├── config.py                 ← reads .env → settings object
│   │   ├── api/
│   │   │   └── routes_chat.py        ← POST /chat, GET /history, POST /approve
│   │   ├── agents/
│   │   │   ├── state.py              ← AgentState (LangGraph shared memory)
│   │   │   ├── nodes.py              ← planner, executor, approval, responder
│   │   │   └── graph.py              ← LangGraph workflow wiring
│   │   ├── tools/
│   │   │   ├── base.py               ← BaseTool abstract class
│   │   │   ├── registry.py           ← tool name → instance map
│   │   │   ├── executor.py           ← PythonToolExecutor (+ MCPToolExecutor stub)
│   │   │   └── mock_tools.py         ← 5 mock tools for Phase 1
│   │   └── schemas/
│   │       └── chat_schema.py        ← Pydantic request/response models
│   └── tests/
│       ├── conftest.py               ← shared fixtures (client, mock LLMs)
│       ├── test_tools.py             ← tools layer tests
│       ├── test_schemas.py           ← Pydantic schema tests
│       ├── test_agent_nodes.py       ← node and routing tests
│       ├── test_agent_state.py       ← AgentState tests
│       └── test_api.py               ← FastAPI endpoint integration tests
│
└── frontend/
    └── streamlit_app.py              ← Streamlit chat UI
```

---

## 10. Quick Reference Commands

```bash
# ── Setup ─────────────────────────────────────────────────────────────────────
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env with your API key

# ── Run ───────────────────────────────────────────────────────────────────────
cd backend && export PYTHONPATH=$(pwd)
uvicorn app.main:app --reload --port 8000   # Terminal 1 (backend)
cd frontend && streamlit run streamlit_app.py  # Terminal 2 (UI)

# ── Test ──────────────────────────────────────────────────────────────────────
cd backend && pytest                        # all tests
pytest -v                                   # verbose
pytest tests/test_api.py -v                 # one file
pytest -k "email" -v                        # by keyword
pytest --cov=app --cov-report=term-missing  # with coverage

# ── Verify backend is alive ───────────────────────────────────────────────────
curl http://localhost:8000/health
open http://localhost:8000/docs             # Swagger UI
open http://localhost:8501                  # Streamlit UI
```
