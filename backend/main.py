import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api.agents import router as agents_router
from api.export import router as export_router
from api.feed import router as feed_router
from api.workspace import router as workspace_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # TODO: connect MongoDB Atlas via motor
    yield


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
app.include_router(feed_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(export_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
