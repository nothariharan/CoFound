# Track A — MongoDB & Knowledge Graph

**Owner:** Teammate A  
**Branch:** `feat/track-a-mongodb`  
**PRs to:** `main` (Lead merges)

---

## Mission

Make MongoDB Atlas the living memory of the startup. Every node, task, journal entry, and knowledge chunk lives in Atlas — not in-memory dicts.

---

## Files You Own

```
backend/
├── db/                          # NEW — create this
│   ├── __init__.py
│   ├── connection.py            # Motor client, lifespan helpers
│   └── collections.py           # Collection name constants
├── graph/
│   ├── node_manager.py          # Implement fully
│   ├── unlock_engine.py         # Wire to API responses
│   └── snapshot.py              # Write on every mutation
├── mcp/
│   └── mongodb_mcp.py           # MCP interface for agents
├── api/
│   ├── workspace.py             # Replace in-memory store
│   └── nodes.py                 # PATCH /api/nodes/{id}
└── store.py                     # DELETE after Atlas works

scripts/
├── init_atlas_indexes.py        # Implement
└── seed_knowledge_base.py       # Implement
```

## Files You Must NOT Edit

- `frontend/` (any file)
- `backend/agents/` (any file)
- `backend/main.py` (paste lifespan snippet in PR description for Lead)
- `backend/api/feed.py`, `agents.py`, `export.py`

---

## Task List

### Phase 1 — Foundation (Days 1–2)

- [ ] **A1.** Create MongoDB Atlas cluster (M0 free tier OK for hackathon)
- [ ] **A2.** Add `backend/db/connection.py`:
  ```python
  async def connect_db() -> AsyncIOMotorDatabase: ...
  async def close_db() -> None: ...
  ```
- [ ] **A3.** Implement collections in `backend/db/collections.py`:
  - `startup_graphs`, `nodes`, `task_queue`, `dead_ends`
  - `decision_journal`, `product_knowledge_base`
  - `build_events`, `observe_events`, `agent_sessions`
- [ ] **A4.** Implement `NodeManager`:
  - `create_workspace(idea: str) -> WorkspaceDocument`
  - `get_workspace(idea_id: str) -> WorkspaceDocument | None`
  - `update_node(idea_id: str, node: BaseNode) -> BaseNode`
  - `list_nodes(idea_id: str) -> list[BaseNode]`
- [ ] **A5.** Replace `WORKSPACES` dict in `workspace.py` with `NodeManager` calls
- [ ] **A6.** Implement `MemoryGraphStore` wrapper implementing `GraphStore` protocol (for Track B interim use)
- [ ] **A7.** PR #1: "Atlas persistence for workspace CRUD"

### Phase 2 — Graph Logic (Days 3–4)

- [ ] **A8.** Wire `unlock_engine.py` into `get_workspace` — apply locked status
- [ ] **A9.** Implement `PATCH /api/nodes/{node_id}` in `nodes.py`
- [ ] **A10.** On every node mutation: append to `decision_journal` + `historical_snapshots`
- [ ] **A11.** Implement `GET /api/workspace/{id}/journal`
- [ ] **A12.** PR #2: "Unlock engine + decision journal"

### Phase 3 — Vector KB (Days 5–6)

- [ ] **A13.** Run `scripts/init_atlas_indexes.py` — create vector search index on `product_knowledge_base`
- [ ] **A14.** Run `scripts/seed_knowledge_base.py` — embed ≥ 20 chunks:
  - Paul Graham essays (3–5 chunks)
  - YC application framework (3–5 chunks)
  - The Mom Test principles (3–5 chunks)
  - Zero to One monopoly thinking (3–5 chunks)
  - Inspired / Marty Cagan discovery (3–5 chunks)
- [ ] **A15.** Add `search_knowledge_base(query: str, limit: int) -> list[dict]` to NodeManager or separate module
- [ ] **A16.** PR #3: "Vector knowledge base seeded"

### Phase 4 — Event Stores (Days 7–9)

- [ ] **A17.** `build_events` collection schema + insert helper (Track B/Lead call this)
- [ ] **A18.** `observe_events` collection schema + insert helper
- [ ] **A19.** `task_queue` CRUD: enqueue, pop pending, mark done/dead_end
- [ ] **A20.** PR #4: "Event stores + task queue"

### Phase 5 — Polish (Day 10)

- [ ] **A21.** Delete `backend/store.py`
- [ ] **A22.** Index optimization, connection pooling
- [ ] **A23.** Final PR: "Atlas cleanup"

---

## Acceptance Criteria (Per PR)

### PR #1 — Atlas Persistence
- [ ] `POST /api/workspace` persists to Atlas
- [ ] Server restart → `GET /api/workspace/{id}` still returns data
- [ ] Core Idea node has correct schema (all fields from contract)
- [ ] `.env.example` updated if new vars added
- [ ] Manual test script in PR description

### PR #2 — Unlock + Journal
- [ ] Audience/Market/Competitors returned with `status: locked` until Core Idea ≥ 70%
- [ ] `PATCH /api/nodes/{id}` updates confidence in Atlas
- [ ] Decision journal entry created on every PATCH
- [ ] `GET /api/workspace/{id}/journal` returns entries

### PR #3 — Vector KB
- [ ] `init_atlas_indexes.py` runs without error
- [ ] `seed_knowledge_base.py` inserts ≥ 20 documents with embeddings
- [ ] Vector search returns relevant results for "B2B SaaS validation"

### PR #4 — Event Stores
- [ ] Task queue: enqueue + pop works
- [ ] Dead ends logged and never re-queued
- [ ] Build/observe event insert helpers documented

---

## Manual Test Script (Include in PR)

```bash
# Create workspace
curl -X POST http://localhost:8000/api/workspace \
  -H "Content-Type: application/json" \
  -d '{"idea": "AI inventory copilot for restaurants"}'

# Save idea_id from response, then:
curl http://localhost:8000/api/workspace/{idea_id}

# Update node
curl -X PATCH http://localhost:8000/api/nodes/{node_id} \
  -H "Content-Type: application/json" \
  -d '{"idea_id": "{idea_id}", "confidence": 75, "status": "needs_work"}'

# Check journal
curl http://localhost:8000/api/workspace/{idea_id}/journal

# Restart server, verify persistence
curl http://localhost:8000/api/workspace/{idea_id}
```

---

## Dependencies on Other Tracks

| Need from | What | When |
|-----------|------|------|
| Lead | Merge lifespan hook in `main.py` | Day 2 |
| Track B | Uses `GraphStore` protocol | Day 2+ |
| Track C | Consumes workspace + journal APIs | Day 2+ |

---

## Blockers — Escalate to Lead If

- Atlas connection fails (IP whitelist, credentials)
- Schema change needed in `schema.py` (open issue, don't edit directly)
- Track B needs task_queue shape changed (propose in daily sync)

---

## MongoDB Atlas — 7 Use Cases to Hit

Document in PR which use cases you implemented:

1. Knowledge graph storage (`nodes`, `startup_graphs`)
2. Agent task queue (`task_queue`)
3. Vector search (`product_knowledge_base`)
4. Historical snapshots (`decision_journal`)
5. Dead end log (`dead_ends`)
6. Build event store (`build_events`)
7. Observe event store (`observe_events`)

**Hackathon pitch:** Atlas is not a key-value store — it is the startup brain.
