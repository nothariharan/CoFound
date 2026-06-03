# Contract Freeze — Shared Interfaces

**Status:** FROZEN after Day 0 meeting  
**Rule:** No breaking changes without Lead approval + all 3 notified.

All tracks build against these contracts. Implementation can change internally; shapes cannot.

---

## REST API Endpoints

### Track A implements — B and C consume

#### `POST /api/workspace`

Create a new startup workspace.

**Request:**
```json
{ "idea": "AI copilot for restaurant owners to manage inventory" }
```

**Response:**
```json
{
  "idea_id": "uuid-v4",
  "workspace_name": "AI copilot for restaurant owners...",
  "nodes": [ /* BaseNode[] — always includes core_idea */ ]
}
```

#### `GET /api/workspace/{idea_id}`

Return full workspace with all unlocked nodes.

**Response:** Same shape as POST response.

#### `PATCH /api/nodes/{node_id}`

Update a node. Used by Track B (researcher commits) and Track C (manual edits).

**Request:**
```json
{
  "idea_id": "uuid-v4",
  "confidence": 81,
  "status": "validated",
  "agent_notes": "847 Reddit posts found",
  "source_pills": [{ "label": "Reddit", "count": 847 }],
  "sources": ["reddit"],
  "active_agents": []
}
```

**Response:** Updated node object.

#### `GET /api/workspace/{idea_id}/journal`

Decision journal entries for a workspace.

**Response:**
```json
{
  "entries": [
    {
      "timestamp": "ISO-8601",
      "node_type": "audience",
      "event": "confidence_updated",
      "reason": "Research committed after critique score 81",
      "evidence": ["847 Reddit posts"],
      "confidence_before": 0,
      "confidence_after": 81
    }
  ]
}
```

---

### Track B implements — C consumes

#### `POST /api/agents/spawn`

Start agent research for a workspace.

**Request:**
```json
{ "workspace_id": "uuid-v4", "trigger": "session_start | pivot | manual" }
```

**Response:**
```json
{ "session_id": "uuid-v4", "tasks_queued": 8, "agents_active": 2 }
```

#### `GET /api/feed?workspace_id={id}` (SSE)

Server-Sent Events stream of agent activity.

**Event shape:**
```json
{
  "text": "[Researcher R1] Running Reddit scan for pain points...",
  "type": "info | critique | error | done | ping",
  "node_id": "optional-uuid",
  "score": 63
}
```

**Critique format in `text`:** `[Critique: 63/100] Too broad — refining query`

#### `POST /api/agents/pivot`

Trigger diff classifier on user pivot message.

**Request:**
```json
{
  "workspace_id": "uuid-v4",
  "message": "Actually, pivot to ghost kitchens — different audience"
}
```

**Response:**
```json
{
  "nodes_affected": ["audience", "competitors", "revenue"],
  "nodes_unchanged": ["core_idea", "tech_stack", "market_intelligence"],
  "requery_needed": true,
  "spawn_researcher": true
}
```

#### `POST /api/export`

Generate export zip.

**Request:**
```json
{ "workspace_id": "uuid-v4" }
```

**Response:**
```json
{ "export_url": "/api/export/{export_id}/download", "files": ["README.md", "tech_stack.md", "..."] }
```

#### `GET /api/priority?workspace_id={id}`

Today's Priority recommendation.

**Response:**
```json
{
  "action": "Talk to 3 restaurant owners",
  "reason": "Audience confidence is 72% — highest ROI action today",
  "estimated_time": "~2 hrs",
  "impact": "High — unlocks pricing clarity"
}
```

---

### Track C implements — UI consumes

#### `POST /api/integrations/github`

Connect GitHub repo for Build Node.

**Request:**
```json
{ "workspace_id": "uuid-v4", "repo": "owner/repo", "access_token": "ghp_..." }
```

**Response:**
```json
{ "connected": true, "build_node_unlocked": true }
```

#### `POST /api/integrations/posthog`

Connect PostHog project for Observe Node.

**Request:**
```json
{ "workspace_id": "uuid-v4", "project_id": "...", "api_key": "phc_..." }
```

**Response:**
```json
{ "connected": true, "observe_node_unlocked": true }
```

---

## Shared Type Files

| File | Owner | Rule |
|------|-------|------|
| `backend/graph/schema.py` | Track A | B and C import only. Changes via PR to Lead. |
| `frontend/src/types/index.ts` | Track C (Lead) | Must mirror `schema.py`. Sync after every schema PR. |
| `backend/store.py` | Track A | Deleted when Atlas lands. Interim only. |
| `backend/main.py` | Lead | Teammates paste router registration snippet in PR description. |

---

## BaseNode Schema (Canonical)

Both Python and TypeScript must match this shape:

```json
{
  "node_id": "uuid-v4",
  "type": "core_idea | audience | market_intelligence | competitors | revenue | product_vision | tech_stack | build | launch | observe | growth",
  "confidence": 74,
  "status": "validated | needs_work | blocking | locked",
  "sources": ["reddit", "exa", "github", "posthog", "user_input"],
  "source_pills": [{ "label": "Reddit", "count": 847, "url": "..." }],
  "agent_notes": "...",
  "title": "Core Idea",
  "summary": "One-line summary",
  "last_updated": "ISO-8601",
  "active_agents": ["researcher_1", "researcher_2"],
  "unlock_conditions": { "prerequisites": [], "threshold": 70 }
}
```

---

## GraphStore Protocol (Track B uses before Atlas merge)

Track B must not import `store.py` directly. Use this protocol:

```python
from typing import Protocol
from graph.schema import BaseNode, WorkspaceDocument

class ResearchTask(BaseModel):
    task: str
    type: str
    tools: list[str]
    priority: int
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3

class GraphStore(Protocol):
    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None: ...
    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode: ...
    async def enqueue_task(self, idea_id: str, task: ResearchTask) -> None: ...
    async def log_dead_end(self, idea_id: str, task: str, reason: str) -> None: ...
```

**Implementations:**
- `MemoryGraphStore` — interim (current `store.py` wrapper) — Track A provides
- `AtlasGraphStore` — production — Track A implements in `backend/db/`

Track B receives `GraphStore` via dependency injection in agent modules.

---

## Unlock Rules (Both Backend and Frontend)

| Node | Prerequisites | Threshold |
|------|---------------|-----------|
| Core Idea | None | — |
| Audience, Market Intelligence, Competitors | Core Idea | 70% |
| Revenue, Product Vision | Audience + Market Intelligence | 70% |
| Tech Stack | Competitors + Core Idea | 70% |
| Build | Revenue + Tech Stack | 70% |
| Launch | Build | auto on deploy |
| Observe | Launch | on PostHog connect |
| Growth | Observe | continuous |

Locked nodes: return with `"status": "locked"` OR omit from response (Track A decides; document in PR).

---

## Environment Variables (Shared)

All tracks may read these. Only add new vars via PR with `.env.example` update.

```
MONGODB_URI=
MONGODB_DB=cofounder
GOOGLE_API_KEY=
GEMINI_PRO_MODEL=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.0-flash
FIRECRAWL_API_KEY=
EXA_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
POSTHOG_API_KEY=
POSTHOG_PROJECT_ID=
CORS_ORIGINS=http://localhost:5173
```

---

## Breaking Change Process

1. Teammate opens GitHub issue tagged `contract-change`
2. Lead reviews impact on all 3 tracks
3. All 3 acknowledge in issue comment
4. Lead merges schema PR first, then dependent tracks rebase
