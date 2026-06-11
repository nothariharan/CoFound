# Conflict Zones — Who Owns What Files

Editing a file owned by another track without approval causes merge conflicts and wasted time. Follow this map strictly.

---

## Single-Owner Files

| File / Directory | Owner | Others may |
|------------------|-------|------------|
| `backend/graph/schema.py` | Track A | Import only. Request changes via `contract-change` issue. |
| `backend/graph/node_manager.py` | Track A | Import only |
| `backend/graph/unlock_engine.py` | Track A | Import only |
| `backend/graph/snapshot.py` | Track A | Import only |
| `backend/db/` | Track A | Do not create or edit |
| `backend/store.py` | Track A | Track B uses GraphStore protocol, not this file |
| `backend/mcp/` | Track A | Do not edit |
| `backend/api/workspace.py` | Track A | Lead reads only |
| `backend/api/nodes.py` | Track A | Do not edit |
| `scripts/init_atlas_indexes.py` | Track A | Do not edit |
| `scripts/seed_knowledge_base.py` | Track A | Do not edit |
| `backend/agents/` | Track B | Lead does not edit agent logic |
| `backend/tools/` | Track B | Do not edit |
| `backend/critique/` | Track B | Do not edit |
| `backend/sse/feed.py` | Track B | Do not edit |
| `backend/export/` | Track B | Do not edit |
| `backend/llm/` | Track B | Do not edit |
| `backend/personas/` | Track B | Do not edit |
| `backend/api/agents.py` | Track B | Do not edit |
| `backend/api/feed.py` | Track B | Lead reads only |
| `backend/api/export.py` | Track B | Do not edit |
| `frontend/src/` | Lead (Track C) | Teammates do not edit any frontend file |
| `frontend/src/types/index.ts` | Lead | Synced from schema after Track A PRs |
| `backend/api/integrations.py` | Lead | Track B does not edit |
| `backend/main.py` | Lead | Teammates paste router snippet in PR description |

---

## Shared Files (Coordinate Before Editing)

| File | Rule |
|------|------|
| `.env.example` | Whoever adds a var updates this. All review in PR. |
| `backend/requirements.txt` | Add deps in your track PR. Lead resolves duplicates on merge. |
| `README.md` | Lead owns. Teammates propose changes via issue. |
| `docs/architecture.md` | Anyone can PR small updates. Lead merges. |
| `docker-compose.yml` | Lead owns. Request via issue. |

---

## How to Request a Change to Another Track's File

1. Open GitHub issue with label `contract-change`
2. Tag the file owner and Lead
3. Describe: what field/endpoint/method you need and why
4. Wait for owner acknowledgment before implementing dependent code
5. Owner implements or Lead schedules the change in next merge

**Example issue title:** `[contract-change] Add active_agents field to PATCH /api/nodes response`

---

## GraphStore Protocol (Shared Interface)

Track B must use this instead of touching Track A files:

```python
# backend/graph/store_protocol.py — Track A creates, Track B imports

from typing import Protocol
from pydantic import BaseModel
from graph.schema import BaseNode, WorkspaceDocument

class ResearchTask(BaseModel):
    task: str
    type: str
    tools: list[str]
    priority: int
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3
    workspace_id: str

class GraphStore(Protocol):
    async def get_workspace(self, idea_id: str) -> WorkspaceDocument | None: ...
    async def update_node(self, idea_id: str, node: BaseNode) -> BaseNode: ...
    async def enqueue_task(self, task: ResearchTask) -> None: ...
    async def pop_pending_task(self, workspace_id: str) -> ResearchTask | None: ...
    async def mark_task_done(self, task_id: str, score: int) -> None: ...
    async def log_dead_end(self, workspace_id: str, task: str, reason: str) -> None: ...
    async def search_knowledge_base(self, query: str, limit: int = 5) -> list[dict]: ...
```

**Track A implements:** `AtlasGraphStore` in `backend/db/atlas_store.py`  
**Track A also provides (interim):** `MemoryGraphStore` in `backend/db/memory_store.py`  
**Track B injects:** receives `GraphStore` instance, never imports MongoDB directly

---

## main.py Merge Pattern

Teammates do NOT edit `main.py`. Instead, paste this block in PR description:

```python
# === PASTE INTO main.py (Lead merges) ===
from api.nodes import router as nodes_router
app.include_router(nodes_router, prefix="/api")
# === END ===
```

Lead adds imports and router registration during merge.

---

## schema.py ↔ types/index.ts Sync

When Track A changes `schema.py`:

1. Track A notes field changes in PR description
2. Lead merges schema PR
3. Lead updates `frontend/src/types/index.ts` to match
4. Lead commits types sync (can be same merge or immediate follow-up)

**Never:** Track A editing TypeScript. Never: Track B editing Python schema.

---

## Conflict Resolution Priority

When the same file appears in two PRs:

1. **schema.py** → Track A wins
2. **types/index.ts** → Lead wins (synced from schema)
3. **main.py** → Lead manually combines
4. **requirements.txt** → Merge both dependency lists
5. **.env.example** → Merge both var lists, deduplicate

---

## Files Safe for Anyone (Low Conflict Risk)

- `docs/`
- `team/` directory (Lead maintains)
- `cloud_run/` (Track B owns but low touch)
- Test scripts in PR descriptions (not committed)

---

## Anti-Patterns (Do Not Do)

- Track B importing `from store import WORKSPACES` directly
- Track A adding agent logic to `workspace.py`
- Track B editing React components "just to test"
- Anyone pushing to `main` without Lead review
- Two people editing `schema.py` in the same sprint
