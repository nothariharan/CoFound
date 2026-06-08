import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from agents.store_protocol import DEFAULT_STORE, MemoryGraphStore
from api.agents import router as agents_router
from api.export import router as export_router
from api.feed import router as feed_router
from api.integrations import router as integrations_router
from api.nodes import router as nodes_router
from api.workspace import router as workspace_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    mongodb_uri = os.getenv("MONGODB_URI", "").strip()
    if mongodb_uri:
        try:
            from db.atlas_store import AtlasGraphStore
            from db.connection import close_db, connect_db

            db = await connect_db()
            DEFAULT_STORE.set(AtlasGraphStore(db))
            app.state.db = db
            app.state.store = "atlas"
            logger.info("Connected to MongoDB Atlas")
        except Exception as exc:
            logger.warning("MongoDB connection failed, using in-memory store: %s", exc)
            DEFAULT_STORE.set(MemoryGraphStore())
            app.state.store = "memory"
    else:
        DEFAULT_STORE.set(MemoryGraphStore())
        app.state.store = "memory"
        logger.info("MONGODB_URI not set — using in-memory store")

    yield

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


@app.get("/health")
async def health():
    return {"status": "ok", "store": getattr(app.state, "store", "memory")}
