"""export trigger + download routes — day 10"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.export_agent import generate_export
from mdb_mcp.agent_store import get_agent_store
from export.zipper import get_export_path

router = APIRouter(tags=["export"])


class ExportRequest(BaseModel):
    workspace_id: str


@router.post("/export")
async def export_workspace(payload: ExportRequest):
    try:
        result = await generate_export(payload.workspace_id, store=get_agent_store())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"export_url": result["export_url"], "files": result["files"]}


@router.get("/export/{export_id}/download")
async def download_export(export_id: str):
    try:
        path = get_export_path(export_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Export not found") from exc
    return FileResponse(path, media_type="application/zip", filename=path.name)
