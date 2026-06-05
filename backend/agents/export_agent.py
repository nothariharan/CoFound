"""Scaffold file generator — produces export zip on user approval."""

from __future__ import annotations

from agents.store_protocol import DEFAULT_STORE, GraphStore
from export.generator import generate_export_files
from export.zipper import create_export_zip


async def generate_export(workspace_id: str, store: GraphStore = DEFAULT_STORE) -> dict[str, object]:
    workspace = await store.get_workspace(workspace_id)
    if workspace is None:
        raise ValueError(f"Workspace not found: {workspace_id}")
    files = await generate_export_files(workspace)
    export_id, path = create_export_zip(workspace_id, files)
    workspace.export_ready = True
    workspace.export_url = f"/api/export/{export_id}/download"
    return {"export_id": export_id, "path": str(path), "export_url": workspace.export_url, "files": list(files.keys())}
