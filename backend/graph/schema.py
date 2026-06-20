"""mongodb document schemas for the startup graph"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    CORE_IDEA = "core_idea"
    AUDIENCE = "audience"
    MARKET_INTELLIGENCE = "market_intelligence"
    COMPETITORS = "competitors"
    REVENUE = "revenue"
    PRODUCT_VISION = "product_vision"
    TECH_STACK = "tech_stack"
    BUILD = "build"
    LAUNCH = "launch"
    OBSERVE = "observe"
    GROWTH = "growth"
    CUSTOM_RESEARCH = "custom_research"


class NodeStatus(str, Enum):
    VALIDATED = "validated"
    NEEDS_WORK = "needs_work"
    BLOCKING = "blocking"
    LOCKED = "locked"


CANONICAL_NODE_IDS: dict[NodeType, str] = {
    NodeType.CORE_IDEA: "node-core",
    NodeType.AUDIENCE: "node-audience",
    NodeType.MARKET_INTELLIGENCE: "node-market",
    NodeType.COMPETITORS: "node-competitors",
    NodeType.REVENUE: "node-revenue",
    NodeType.PRODUCT_VISION: "node-product",
    NodeType.TECH_STACK: "node-tech",
    NodeType.BUILD: "node-build",
    NodeType.LAUNCH: "node-launch",
    NodeType.OBSERVE: "node-observe",
    NodeType.GROWTH: "node-growth",
}


def canonical_node_id(node_type: NodeType) -> str:
    return CANONICAL_NODE_IDS[node_type]


NODE_AGENT_IDS: dict[NodeType, str] = {
    NodeType.CORE_IDEA: "agent_core_idea",
    NodeType.AUDIENCE: "agent_audience",
    NodeType.MARKET_INTELLIGENCE: "agent_market",
    NodeType.COMPETITORS: "agent_competitors",
    NodeType.REVENUE: "agent_revenue",
    NodeType.PRODUCT_VISION: "agent_product",
    NodeType.TECH_STACK: "agent_tech",
    NodeType.BUILD: "agent_build",
    NodeType.LAUNCH: "agent_launch",
    NodeType.OBSERVE: "agent_observe",
    NodeType.GROWTH: "agent_growth",
    NodeType.CUSTOM_RESEARCH: "agent_research",
}


def node_agent_id(node_type: NodeType) -> str:
    return NODE_AGENT_IDS[node_type]


class SourcePill(BaseModel):
    label: str
    count: int = 0
    url: str | None = None


class UnlockConditions(BaseModel):
    prerequisites: list[str] = Field(default_factory=list)
    threshold: int = 70


class HistoricalSnapshot(BaseModel):
    timestamp: datetime
    confidence: int
    delta: str = ""


class BaseNode(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid4()))
    type: NodeType
    confidence: int = 0
    status: NodeStatus = NodeStatus.BLOCKING
    sources: list[str] = Field(default_factory=list)
    source_pills: list[SourcePill] = Field(default_factory=list)
    agent_notes: str = ""
    chat_history: list[dict[str, Any]] = Field(default_factory=list)
    research_history: list[dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    unlock_conditions: UnlockConditions = Field(default_factory=UnlockConditions)
    historical_snapshots: list[HistoricalSnapshot] = Field(default_factory=list)
    active_agents: list[str] = Field(default_factory=list)
    title: str = ""
    summary: str = ""
    parent_node_id: str | None = None


class CoreIdeaData(BaseModel):
    problem: str = ""
    solution: str = ""
    one_liner: str = ""


class CoreIdeaNode(BaseNode):
    type: NodeType = NodeType.CORE_IDEA
    data: CoreIdeaData = Field(default_factory=CoreIdeaData)


class WorkspaceCreateRequest(BaseModel):
    idea: str = Field(min_length=1, max_length=4000)


class WorkspaceDocument(BaseModel):
    idea_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_name: str = "Untitled Startup"
    session_start: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    approval_status: str = "refining"
    iteration_count: int = 0
    is_monitoring_active: bool = False
    nodes: list[BaseNode] = Field(default_factory=list)
    export_ready: bool = False
    export_url: str | None = None
    github_connected: bool = False
    github_repo: str | None = None
    posthog_connected: bool = False
    posthog_project_id: str | None = None


def status_from_confidence(confidence: int, locked: bool = False) -> NodeStatus:
    if locked:
        return NodeStatus.LOCKED
    if confidence >= 80:
        return NodeStatus.VALIDATED
    if confidence >= 50:
        return NodeStatus.NEEDS_WORK
    return NodeStatus.BLOCKING


def create_core_idea_node(idea: str) -> CoreIdeaNode:
    one_liner = idea.strip()[:120]
    return CoreIdeaNode(
        node_id=canonical_node_id(NodeType.CORE_IDEA),
        title="Core Idea",
        summary=one_liner,
        confidence=35,
        status=NodeStatus.BLOCKING,
        sources=["user_input"],
        data=CoreIdeaData(
            problem=idea.strip(),
            solution="",
            one_liner=one_liner,
        ),
    )
