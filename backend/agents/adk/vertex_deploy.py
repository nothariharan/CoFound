"""Vertex AI Agent Engine deployment helpers.

Requires GCP billing. Not used in the default runtime path.
Enable only when VERTEX_AGENT_ENGINE_ENABLED=true and billing is available.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from agents.adk.config import get_gcp_project, vertex_agent_engine_enabled

_AGENT_MODULE = Path(__file__).resolve().parent / "planner_agent.py"


def deploy_to_agent_engine(
    *,
    location: str = "us-central1",
    display_name: str = "cofounder-planner",
) -> str:
    """Deploy the ADK Planner to Vertex AI Agent Engine (billing required)."""

    if not vertex_agent_engine_enabled():
        raise RuntimeError(
            "Vertex Agent Engine deployment is disabled. "
            "Set VERTEX_AGENT_ENGINE_ENABLED=true and ensure GCP billing is active."
        )

    project = get_gcp_project()
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Agent Engine deployment")

    cmd = [
        "adk",
        "deploy",
        "agent_engine",
        f"--project={project}",
        f"--location={location}",
        f"--display_name={display_name}",
        str(_AGENT_MODULE),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Agent Engine deploy failed")
    return result.stdout.strip()


def deployment_status() -> dict[str, str]:
    """Return deployment metadata for README and ops dashboards."""

    return {
        "framework": "google-adk",
        "agent": "cofounder_planner",
        "vertex_enabled": str(vertex_agent_engine_enabled()).lower(),
        "gcp_project": get_gcp_project(),
        "billing_required": "true",
    }
