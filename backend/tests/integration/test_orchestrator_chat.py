from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from api import agents as agents_api


def test_orchestrator_chat_route_returns_contract(monkeypatch, workspace):
    async def fake_chat(workspace_id: str, message: str, history=None, store=None):
        assert workspace_id == workspace.idea_id
        assert "status" in message.lower()
        return {
            "reply": "Your audience node is at 45% confidence.",
            "speaking_text": "Audience is at forty-five percent.",
            "actions_taken": [{"tool": "get_workspace_summary", "summary": "Loaded workspace summary (11 nodes)"}],
            "ui_actions": [],
        }

    monkeypatch.setattr(agents_api, "orchestrator_chat", fake_chat)

    response = asyncio.run(
        agents_api.orchestrator_chat_route(
            agents_api.OrchestratorChatRequest(
                workspace_id=workspace.idea_id,
                message="Give me a status update",
            )
        )
    )

    assert "audience" in response.reply.lower()
    assert response.actions_taken[0].get("tool") == "get_workspace_summary"


def test_orchestrator_chat_rejects_empty_message(workspace):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            agents_api.orchestrator_chat_route(
                agents_api.OrchestratorChatRequest(workspace_id=workspace.idea_id, message="   ")
            )
        )
    assert exc.value.status_code == 400
