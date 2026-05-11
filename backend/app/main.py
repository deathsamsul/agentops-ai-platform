from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Enterprise AI Agent Platform",
    version="0.1.0"
)


class ChatRequest(BaseModel):
    message: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    reply: str


def run_agent(message: str, user_id: str | None = None) -> str:
    """
    Temporary agent function.
    Later this will call LangGraph agent.
    """
    return f"Agent received your message: {message}"


@app.get("/")
def root():
    return {"status": "running", "message": "AI Agent API is live"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    agent_reply = run_agent(
        message=request.message,
        user_id=request.user_id
    )

    return ChatResponse(reply=agent_reply)


"""
main.py — FastAPI application entry point.

Responsibilities:
  - Create the FastAPI app instance
  - Register all routers (chat, tasks, tools, auth)
  - Set up CORS, lifespan events, and health check
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
# Uncomment as you build each module:
# from app.api.routes_tasks  import router as tasks_router
# from app.api.routes_tools  import router as tools_router
# from app.api.routes_auth   import router as auth_router


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown logic (DB pool, MCP connections, etc.)."""
    print("🚀  Agent platform starting up…")
    # TODO Phase 1: await database.connect()
    # TODO Phase 8: await mcp_client.connect()
    yield
    print("🛑  Agent platform shutting down…")
    # TODO: await database.disconnect()


# ─── App factory ─────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise AI Agent Platform",
        description="Autonomous AI agent with LangGraph, RAG, and MCP tool calling.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow Streamlit frontend and local dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(chat_router, prefix="/api", tags=["Chat"])
    # app.include_router(tasks_router, prefix="/api", tags=["Tasks"])
    # app.include_router(tools_router, prefix="/api", tags=["Tools"])
    # app.include_router(auth_router,  prefix="/api", tags=["Auth"])

    return app


app = create_app()


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "enterprise-ai-agent-platform"}
