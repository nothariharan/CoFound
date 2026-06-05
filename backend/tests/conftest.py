from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from agents.store_protocol import MemoryGraphStore
from graph.schema import WorkspaceDocument, create_core_idea_node
from store import WORKSPACES


@pytest.fixture(autouse=True)
def clear_memory_store():
    WORKSPACES.clear()
    yield
    WORKSPACES.clear()


@pytest.fixture
def workspace():
    ws = WorkspaceDocument(
        workspace_name="Restaurant Inventory Copilot",
        nodes=[create_core_idea_node("AI copilot for restaurant owners to manage inventory and reduce waste")],
    )
    WORKSPACES[ws.idea_id] = ws
    return ws


@pytest.fixture
def memory_store():
    return MemoryGraphStore()
