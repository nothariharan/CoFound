"""adk configuration — gemini api key mode only (no vertex billing)"""
from __future__ import annotations

import os

DEFAULT_PRO_MODEL = "gemini-2.5-pro"
DEFAULT_GCP_PROJECT = "cofound-agent"
APP_NAME = "cofounder"


def get_api_key() -> str:
    return os.getenv("GOOGLE_API_KEY", "").strip()


def get_pro_model() -> str:
    return os.getenv("GEMINI_PRO_MODEL", DEFAULT_PRO_MODEL).strip() or DEFAULT_PRO_MODEL


def get_gcp_project() -> str:
    return os.getenv("GOOGLE_CLOUD_PROJECT", DEFAULT_GCP_PROJECT).strip() or DEFAULT_GCP_PROJECT


def vertex_agent_engine_enabled() -> bool:
    return os.getenv("VERTEX_AGENT_ENGINE_ENABLED", "").strip().lower() == "true"


def ensure_api_key_env() -> None:
    """expose google_api_key to google genai and avoid vertex mode"""

    key = get_api_key()
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is not configured for ADK Planner")
    os.environ["GOOGLE_API_KEY"] = key
    os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
