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
# not builed api routers yet, but will be added in future phases
# from app.api.routes_tasks  import router as tasks_router
# from app.api.routes_tools  import router as tools_router
# from app.api.routes_auth   import router as auth_router


# Lifespan ────────────────────────────────────────────────────────────────
# Start something before app runs (e.g. DB pool, MCP client) and clean up on shutdown Cleanup after app stops  Avoid resource leaks
@asynccontextmanager     # 
async def lifespan(app: FastAPI): #  app: FastAPI is the application instance that can be used to access app state, config, etc. during startup/shutdown
    """Startup / shutdown logic (DB pool, MCP connections, etc.)."""
    print(" Agent platform starting up…")
    # TODO Phase 1: await database.connect()  
    # TODO Phase 8: await mcp_client.connect()
    yield                                   # Everything BEFORE yield runs on startup, everything AFTER runs on shutdown
    print(" Agent platform shutting down…")
    # TODO: await database.disconnect()


#  App factory ─────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise AI Agent Platform",
        description="Autonomous AI agent with LangGraph, RAG, and MCP tool calling.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow Streamlit frontend and local dev
    # like a security gate or checkpoint that controls which external origins can access your API
    # CORS = Cross-Origin Resource Sharing a browser security rule
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers prefix=/api means become /api/chat , tags=["Chat"] is for API docs grouping in documantation                      
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



