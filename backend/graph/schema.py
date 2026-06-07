from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from uuid import UUID, uuid4

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

class SourcePill(BaseModel):
    label: str
    count: int
    url: Optional[str] = None

class UnlockConditions(BaseModel):
    prerequisites: List[str] = Field(default_factory=list)
    threshold: Optional[int] = None

class BaseNode(BaseModel):
    node_id: UUID = Field(default_factory=uuid4)
    type: NodeType # Changed to use NodeType Enum
    confidence: int = 0
    status: Literal["validated", "needs_work", "blocking", "locked"] = "locked"
    sources: List[
        Literal["reddit", "exa", "github", "posthog", "user_input"]
    ] = Field(default_factory=list)
    source_pills: List[SourcePill] = Field(default_factory=list)
    agent_notes: Optional[str] = None
    title: str
    summary: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    active_agents: List[str] = Field(default_factory=list)
    unlock_conditions: UnlockConditions = Field(default_factory=UnlockConditions)

class WorkspaceDocument(BaseModel):
    idea_id: UUID = Field(default_factory=uuid4)
    workspace_name: str
    nodes: List[BaseNode] = Field(default_factory=list)

class WorkspaceCreateRequest(BaseModel):
    idea: str
