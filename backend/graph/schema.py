"""MongoDB document schemas for the startup graph."""

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


class NodeStatus(str, Enum):
    VALIDATED = "validated"
    NEEDS_WORK = "needs_work"
    BLOCKING = "blocking"
    LOCKED = "locked"


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


class CoreIdeaData(BaseModel):
    problem: str = ""
    solution: str = ""
    one_liner: str = ""


class CoreIdeaNode(BaseNode):
    type: NodeType = NodeType.CORE_IDEA
    data: CoreIdeaData = Field(default_factory=CoreIdeaData)


class WorkspaceCreateRequest(BaseModel):
    idea: str


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


class EventType(str, Enum):
    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"
    AGENT_ASSIGNED = "agent_assigned"
    AGENT_UNASSIGNED = "agent_unassigned"
    RESEARCH_COMPLETED = "research_completed"
    CHAT_MESSAGE = "chat_message"
    STATUS_CHANGED = "status_changed"
    CONFIDENCE_CHANGED = "confidence_changed"
    SOURCE_ADDED = "source_added"
    SOURCE_REMOVED = "source_removed"
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    TASK_ENQUEUED = "task_enqueued"
    TASK_PROCESSED = "task_processed"
    TASK_FAILED = "task_failed"
    TASK_DEAD_ENDED = "task_dead_ended"


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    idea_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    details: dict[str, Any] = Field(default_factory=dict)
    agent_id: str | None = None


class BuildEvent(BaseEvent):
    # Specific fields for build events, if any, can be added here.
    # For now, it reuses BaseEvent fields.
    pass


class ObserveEvent(BaseEvent):
    # Specific fields for observe events, if any, can be added here.
    # For now, it reuses BaseEvent fields.
    pass


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_END = "dead_end"


class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    idea_id: str
    task_type: str
    status: TaskStatus = TaskStatus.PENDING
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    retries: int = 0
    max_retries: int = 3
    error_message: str | None = None


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
