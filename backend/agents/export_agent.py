"""Scaffold file generator — produces export zip on user approval."""

from __future__ import annotations

from agents.store_protocol import GraphStore, publish_workspace_update
from mdb_mcp.agent_store import get_agent_store
from export.generator import generate_export_files
from export.zipper import create_export_zip


async def generate_export(workspace_id: str, store: GraphStore | None = None) -> dict[str, object]:
    store = store or get_agent_store()
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")
    files = await generate_export_files(workspace)
    export_id, path = create_export_zip(workspace_id, files)
    workspace.export_ready = True
    workspace.export_url = f"/api/export/{export_id}/download"
    if hasattr(store, "save_workspace"):
        await store.save_workspace(workspace)
    await publish_workspace_update(workspace_id, workspace)
    return {"export_id": export_id, "path": str(path), "export_url": workspace.export_url, "files": list(files.keys())}
