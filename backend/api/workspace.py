"""workspace crud — create graph from idea, fetch state, decision journal"""

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.idea_framer import frame_idea
from agents.store_protocol import DEFAULT_STORE
from graph.schema import (
    BaseNode,
    NodeType,
    UnlockConditions,
    WorkspaceCreateRequest,
    WorkspaceDocument,
    canonical_node_id,
    create_core_idea_node,
    status_from_confidence,
)
from graph.unlock_engine import compute_unlock_states

router = APIRouter(tags=["workspace"])


class WorkspaceResponse(BaseModel):
    idea_id: str
    workspace_name: str
    nodes: list


class JournalResponse(BaseModel):
    entries: list


def _to_response(workspace: WorkspaceDocument) -> WorkspaceResponse:
    workspace.nodes = compute_unlock_states(workspace.nodes)
    return WorkspaceResponse(
        idea_id=workspace.idea_id,
        workspace_name=workspace.workspace_name,
        nodes=[n.model_dump(mode="json") for n in workspace.nodes],
    )


@router.post("/workspace", response_model=WorkspaceResponse)
async def create_workspace(body: WorkspaceCreateRequest):
    # idea framer names the workspace and seeds core node confidence before graph unlock
    idea_id = str(uuid4())
    framed = await frame_idea(body.idea)
    core_node = create_core_idea_node(body.idea)
    core_node.title = framed["core_title"]
    core_node.summary = framed["one_liner"]
    core_node.confidence = framed["confidence"]
    core_node.status = status_from_confidence(core_node.confidence)
    core_node.data.problem = framed["problem"]
    core_node.data.solution = framed["solution"]
    core_node.data.one_liner = framed["one_liner"]
    core_node.agent_notes = f"Problem: {framed['problem']}\nSolution: {framed['solution']}".strip()
    workspace = WorkspaceDocument(
        idea_id=idea_id,
        workspace_name=framed["workspace_name"],
        nodes=[core_node, *_starter_nodes()],
    )
    await DEFAULT_STORE.save_workspace(workspace)
    return _to_response(workspace)


def _starter_nodes() -> list[BaseNode]:
    return [
        _empty_node(NodeType.AUDIENCE, "Audience", "Approve research to identify the first customer segment and urgent pains."),
        _empty_node(NodeType.MARKET_INTELLIGENCE, "Market Intelligence", "Approve research to size demand, timing, and market pull."),
        _empty_node(NodeType.COMPETITORS, "Competitors", "Approve research to map direct, indirect, and do-nothing alternatives."),
        _empty_node(NodeType.REVENUE, "Revenue", "Locked until audience and market evidence are strong enough."),
        _empty_node(NodeType.PRODUCT_VISION, "Product Vision", "Locked until audience and market evidence are strong enough."),
        _empty_node(NodeType.TECH_STACK, "Tech Stack", "Locked until competitor and core idea evidence are strong enough."),
        _empty_node(NodeType.BUILD, "Build", "Locked until revenue and tech stack are ready."),
        _empty_node(NodeType.LAUNCH, "Launch", "Locked until build evidence is ready."),
        _empty_node(NodeType.OBSERVE, "Observe", "Locked until launch evidence is ready."),
        _empty_node(NodeType.GROWTH, "Growth", "Locked until observe signals are ready."),
    ]


def _empty_node(node_type: NodeType, title: str, summary: str) -> BaseNode:
    return BaseNode(
        node_id=canonical_node_id(node_type),
        type=node_type,
        title=title,
        summary=summary,
        confidence=0,
        status=status_from_confidence(0),
        sources=[],
        unlock_conditions=UnlockConditions(),
    )


@router.get("/workspace/{idea_id}", response_model=WorkspaceResponse)
async def get_workspace(idea_id: str):
    workspace = await DEFAULT_STORE.get_workspace(idea_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return _to_response(workspace)


@router.get("/workspace/{idea_id}/journal", response_model=JournalResponse)
async def get_workspace_journal(idea_id: str):
    workspace = await DEFAULT_STORE.get_workspace(idea_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if hasattr(DEFAULT_STORE, "list_journal"):
        entries = await DEFAULT_STORE.list_journal(idea_id)
        return JournalResponse(entries=entries)
    return JournalResponse(entries=[])
