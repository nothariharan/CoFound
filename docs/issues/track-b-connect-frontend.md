# [Track B] Connect backend to frontend (end-to-end integration)

**Assignee:** Track B (Agents & GCP)  
**Labels:** `track-b`, `integration`, `team-sync`  
**Depends on:** Track B merge to `main` (done — `feat/track-b-agents`)  
**Reference doc:** [`docs/frontend_integration.md`](../frontend_integration.md)

---

## Context

Track B backend (orchestrator, researcher loop, Gemini, SSE feed, pivot, priority, export) is merged into `main`. The frontend (Track C) is also on `main` with a **premium dark UI** and runs in **mock mode by default** — it does not call the real API unless configured.

Your job: wire the live backend so the frontend uses real data instead of the scripted demo in `frontend/src/mock/`.

The Lead fixed a React Flow canvas sizing issue locally (`App.tsx` + `StartupCanvas.tsx` — dashboard uses `h-dvh`, canvas has explicit `width/height: 100%`). Pull latest `main` before starting.

---

## Goal

When a user opens `http://localhost:5173`, enters an idea, and clicks **Start**:

1. `POST /api/workspace` creates a real workspace (not mock).
2. The canvas shows nodes returned by the backend.
3. `GET /api/feed?workspace_id=...` streams real agent SSE events into the UI.
4. `POST /api/agents/spawn` runs after workspace creation so research begins automatically.
5. Node updates (confidence, status, `active_agents`, `source_pills`) appear on the canvas as agents commit research.

---

## Step-by-step: local connection

### 1. Pull latest `main`

```bash
git checkout main
git pull origin main
```

### 2. Backend environment

Copy the root env template and fill in secrets (never commit `.env`):

```bash
cp .env.example .env
```

**Required for agents to run (minimum):**

| Variable | Required | Purpose |
|----------|----------|---------|
| `GOOGLE_API_KEY` | **Yes** (or mock mode in code) | Gemini Pro/Flash for orchestrator, planner, researcher, diff classifier |
| `GEMINI_PRO_MODEL` | No (default `gemini-2.5-pro`) | Heavy synthesis |
| `GEMINI_FLASH_MODEL` | No (default `gemini-2.0-flash`) | Research loops |

**Required once Track A wires Atlas (persistence):**

| Variable | Required | Purpose |
|----------|----------|---------|
| `MONGODB_URI` | Yes for persistence | Atlas connection string |
| `MONGODB_DB` | No (default `cofounder`) | Database name |

**Optional — research tools (agents degrade gracefully without these):**

| Variable | Purpose |
|----------|---------|
| `FIRECRAWL_API_KEY` | Web scraping |
| `EXA_API_KEY` | Semantic search |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Reddit pain-point scan |
| `GUMMYSEARCH_API_KEY` | Audience signals |
| `PRODUCTHUNT_API_KEY` | Competitor discovery |

**Optional — integrations (Track C UI, later):**

| Variable | Purpose |
|----------|---------|
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | Build Node |
| `POSTHOG_API_KEY` / `POSTHOG_PROJECT_ID` | Observe Node |

**Server:**

| Variable | Purpose |
|----------|---------|
| `CORS_ORIGINS` | Must include `http://localhost:5173` (already in `main.py`) |
| `BACKEND_PORT` | Use `8000` locally (Vite proxy expects this) |

Install and run backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Verify: `http://localhost:8000/health` → `{"status":"ok"}`

Run tests:

```bash
pytest tests/ -q
```

### 3. Frontend environment (disable mock)

Create `frontend/.env.local` (gitignored):

```
VITE_USE_MOCK=false
```

Restart the dev server (Vite only reads env at startup):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — use **Start** (not "Load demo"; demo always uses mock).

### 4. How requests flow

```
Browser (:5173)  →  fetch('/api/workspace')  →  Vite proxy  →  FastAPI (:8000)
Browser (:5173)  →  EventSource('/api/feed?workspace_id=...')  →  same proxy  →  SSE
```

No hardcoded `localhost:8000` in frontend code — proxy handles it.

---

## API contract (must match exactly)

Frozen contract: [`team/00_CONTRACT_FREEZE.md`](../../team/00_CONTRACT_FREEZE.md)  
Full frontend guide: [`docs/frontend_integration.md`](../frontend_integration.md)

### Endpoints the frontend calls today (you must make these work)

| Method | Path | When |
|--------|------|------|
| `POST` | `/api/workspace` | User submits idea on intake screen |
| `GET` | `/api/workspace/{idea_id}` | Refresh / rehydrate graph |
| `GET` | `/api/feed?workspace_id={id}` | SSE — agent activity in History tab |

### Endpoints you implemented — wire the frontend to call them

After workspace creation, the frontend should trigger (currently only in mock):

| Method | Path | Action needed |
|--------|------|---------------|
| `POST` | `/api/agents/spawn` | Call from frontend after `POST /api/workspace` succeeds — body: `{ "workspace_id": "<idea_id>", "trigger": "session_start" }` |
| `POST` | `/api/agents/pivot` | Already wired in Node Chat when user types "pivot" — verify real response blurs `nodes_affected` |
| `GET` | `/api/priority?workspace_id=` | Wire ActionBar "Today's Priority" (currently mock in `demoEngine.ts`) |
| `POST` | `/api/export` | Wire Export modal (Track C) |

**Suggested spawn hook** — add to `frontend/src/hooks/useWorkspace.ts` after successful workspace create (when `USE_MOCK` is false):

```ts
await fetch('/api/agents/spawn', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ workspace_id: data.idea_id, trigger: 'session_start' }),
})
```

Coordinate with Lead if you prefer backend to auto-spawn inside `POST /api/workspace` instead.

### `GraphNode` JSON shape (canvas renders this)

Every node in `nodes[]` must match:

```json
{
  "node_id": "node-audience",
  "type": "audience",
  "confidence": 72,
  "status": "needs_work",
  "sources": ["reddit"],
  "source_pills": [{ "label": "Reddit", "count": 847 }],
  "agent_notes": "...",
  "title": "Audience",
  "summary": "One-line summary",
  "last_updated": "2026-06-05T12:00:00.000Z",
  "active_agents": ["researcher_1"]
}
```

**`type` values:** `core_idea`, `audience`, `market_intelligence`, `competitors`, `revenue`, `product_vision`, `tech_stack`, `build`, `launch`, `observe`, `growth`

**`status` values:** `validated`, `needs_work`, `blocking`, `locked`

**Canvas layout ids** (recommended for tree positioning — see `frontend/src/utils/canvasLayout.ts`):

`node-core`, `node-audience`, `node-market`, `node-competitors`, `node-revenue`, `node-product`, `node-tech`, `node-build`, `node-launch`, `node-observe`, `node-growth`

Optional rich fields for right panel: `overview`, `pain_points: [{ "label": "...", "percentage": 34 }]`

### SSE feed format

Each SSE `data` payload:

```json
{ "text": "[Researcher R1] Running Reddit scan...", "type": "info", "node_id": "node-audience", "score": 63 }
```

- `type`: `info` | `critique` | `error` | `done` | `ping`
- Critique lines: `"[Critique: 63/100] reason..."`
- Send `ping` every ~15s with empty `text` (client ignores)
- Frontend ignores `type: "ping"` and empty text

When a node is being researched, set `active_agents` on that node and emit SSE with matching `node_id` so agent chips pulse on the canvas.

---

## Acceptance criteria

- [ ] `frontend/.env.local` has `VITE_USE_MOCK=false`; intake **Start** hits real API (check Network tab).
- [ ] `POST /api/workspace` → Core Idea node on canvas.
- [ ] `POST /api/agents/spawn` (or auto-spawn) → SSE feed shows live lines in History tab (not mock script).
- [ ] At least two nodes show `active_agents` simultaneously during parallel research.
- [ ] Critique scores appear in feed: `[Critique: N/100]`.
- [ ] `PATCH /api/nodes/{id}` or workspace refresh updates confidence rings on canvas.
- [ ] `pytest tests/ -q` passes.
- [ ] No API keys or `.env` files in git diff.

---

## Files to read first

| File | Why |
|------|-----|
| `docs/frontend_integration.md` | Full integration guide |
| `team/00_CONTRACT_FREEZE.md` | Frozen API shapes |
| `frontend/src/hooks/useWorkspace.ts` | Where to disable mock / add spawn |
| `frontend/src/hooks/useSSEFeed.ts` | SSE consumer |
| `frontend/src/types/index.ts` | TypeScript types = your JSON contract |
| `backend/main.py` | Routers already registered |
| `backend/api/agents.py` | spawn / pivot / priority |
| `backend/api/feed.py` + `backend/sse/feed.py` | SSE implementation |

---

## Out of scope for this issue (other tracks)

- **Track A:** MongoDB Atlas persistence (`MONGODB_URI`) — until merged, in-memory store is fine for dev.
- **Track C:** GitHub/PostHog integration UI, export modal wiring — separate issues.

---

## Questions?

Comment on this issue or tag Lead in daily sync. Do not change `team/00_CONTRACT_FREEZE.md` shapes without Lead approval.
