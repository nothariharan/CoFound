"""Run ADK agents in-process via Google AI API (no Vertex billing)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.adk.config import APP_NAME, ensure_api_key_env
from agents.adk.planner_agent import planner_agent

if TYPE_CHECKING:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

_runner: Runner | None = None
_session_service: InMemorySessionService | None = None
_USER_ID = "cofounder_user"


def _get_runner() -> tuple["Runner", "InMemorySessionService"]:
    global _runner, _session_service
    if _runner is not None and _session_service is not None:
        return _runner, _session_service

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    ensure_api_key_env()
    session_service = InMemorySessionService()
    runner = Runner(
        agent=planner_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    _session_service = session_service
    _runner = runner
    return _runner, _session_service


async def run_planner_agent(prompt: str) -> str:
    """Execute the ADK Planner agent and return the final text response."""

    from google.genai import types

    ensure_api_key_env()
    runner, session_service = _get_runner()
    session = await session_service.create_session(app_name=APP_NAME, user_id=_USER_ID)
    content = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = ""
    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=session.id,
        new_message=content,
    ):
        if not event.is_final_response():
            continue
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text = part.text

    if not final_text.strip():
        raise RuntimeError("ADK Planner returned an empty response")
    return final_text
