from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from agents.store_protocol import MEMORY_WORKSPACES, MemoryGraphStore
from graph.schema import WorkspaceDocument, create_core_idea_node


@pytest.fixture(autouse=True)
def clear_memory_store():
    MEMORY_WORKSPACES.clear()
    yield
    MEMORY_WORKSPACES.clear()


@pytest.fixture
def workspace():
    ws = WorkspaceDocument(
        workspace_name="KitchenOps",
        nodes=[create_core_idea_node("inventory app for restaurant owners to manage stock and reduce waste")],
    )
    MEMORY_WORKSPACES[ws.idea_id] = ws
    return ws


@pytest.fixture
def memory_store():
    return MemoryGraphStore()
