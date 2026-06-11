import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agents.store_protocol import DEFAULT_STORE, MemoryGraphStore
from api.agents import router as agents_router
from api.export import router as export_router
from api.feed import router as feed_router
from api.integrations import router as integrations_router
from api.nodes import router as nodes_router
from api.voice import router as voice_router
from api.workspace import router as workspace_router
from mdb_mcp.agent_store import agent_store_mode, set_agent_store, use_mongodb_mcp_enabled

logger = logging.getLogger(__name__)


async def _bootstrap_stores(app: FastAPI) -> None:
    mongodb_uri = os.getenv("MONGODB_URI", "").strip()
    app.state.store = "memory"
    app.state.agent_store = "default"
    DEFAULT_STORE.set(MemoryGraphStore())

    if mongodb_uri:
        try:
            from db.atlas_store import AtlasGraphStore
            from db.connection import connect_db

            db = await connect_db()
            DEFAULT_STORE.set(AtlasGraphStore(db))
            app.state.db = db
            app.state.store = "atlas"
            logger.info("Connected to MongoDB Atlas for API routes")
        except Exception as exc:
            logger.warning("MongoDB connection failed, using in-memory store: %s", exc)
            DEFAULT_STORE.set(MemoryGraphStore())
            app.state.store = "memory"
    else:
        logger.info("MONGODB_URI not set — using in-memory store")

    if use_mongodb_mcp_enabled():
        try:
            from db import collections as col
            from mdb_mcp.client import start_mcp_session
            from mdb_mcp.db_ops import mcp_find
            from mdb_mcp.graph_store import McpGraphStore

            await start_mcp_session()
            await mcp_find(col.STARTUP_GRAPHS, limit=1)
            set_agent_store(McpGraphStore(), mode="mcp")
            app.state.agent_store = "mcp"
            logger.info("MongoDB MCP agent store enabled")
        except Exception as exc:
            logger.warning("MongoDB MCP startup failed, agents will use DEFAULT_STORE: %s", exc)
            app.state.agent_store = agent_store_mode()
    else:
        logger.info("USE_MONGODB_MCP disabled — agents will use DEFAULT_STORE")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Python %s.%s.%s", *sys.version_info[:3])
    app.state.store = "memory"
    app.state.agent_store = "default"
    DEFAULT_STORE.set(MemoryGraphStore())

    bootstrap_task = asyncio.create_task(_bootstrap_stores(app))

    yield

    bootstrap_task.cancel()
    with suppress(asyncio.CancelledError):
        await bootstrap_task

    if getattr(app.state, "agent_store", None) == "mcp":
        try:
            from mdb_mcp.client import close_mcp_session

            await close_mcp_session()
        except Exception:
            pass

    if getattr(app.state, "store", None) == "atlas":
        try:
            from db.connection import close_db

            await close_db()
        except Exception:
            pass


app = FastAPI(title="CoFounder API", version="0.1.0", lifespan=lifespan)

_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspace_router, prefix="/api")
app.include_router(nodes_router, prefix="/api")
app.include_router(feed_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(voice_router, prefix="/api")


@app.get("/health")
async def health():
    from mdb_mcp.mongodb_mcp import mcp_cluster_label

    return {
        "status": "ok",
        "store": getattr(app.state, "store", "memory"),
        "agent_store": getattr(app.state, "agent_store", "default"),
        "mongodb_cluster": mcp_cluster_label(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
