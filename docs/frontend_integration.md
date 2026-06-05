# Frontend Integration Guide (for Backend + Cloud)

This document explains **exactly how to connect the CoFounder backend (FastAPI + MongoDB Atlas + Gemini / Google Cloud agents) to the current frontend**, what API shapes the UI expects, how the mock/demo mode works, and how to take the whole thing from "runs locally with fake data" to "runs on Cloud Run with real data".

Audience: whoever builds Track A (Data/Graph) and Track B (Agents/GCP), and whoever deploys to Google Cloud.

> TL;DR: The frontend currently runs in **mock mode** (no backend needed). To use the real backend, set `VITE_USE_MOCK=false`, run FastAPI on port 8000, and make your endpoints return the JSON shapes documented below. The frontend talks to the backend **only** through `/api/*`.

---

## 1. Architecture and data flow

```
+-------------------------------------------+
|  Frontend (Vite + React)  :5173           |
|                                           |
|  useWorkspace() / useSSEFeed()            |
|        |                                  |
|        v                                  |
|   USE_MOCK ? ----yes----> mock/demoEngine |  (scripted demo, no network)
|        |                                  |
|        no                                 |
|        v                                  |
|   fetch('/api/...')                       |
+--------|----------------------------------+
         |  Vite dev proxy ( /api -> :8000 )
         v
+-------------------------------------------+
|  Backend (FastAPI)  :8000                 |
|   /api/workspace, /api/feed, ...          |
|        |                  |               |
|        v                  v               |
|   MongoDB Atlas      Gemini / GCP agents  |
+-------------------------------------------+
```

Key idea: **the graph is the interface**. The backend's job is to keep the MongoDB graph up to date and stream agent activity; the frontend renders whatever nodes + feed events it receives.

---

## 2. The mock toggle (most important thing to understand)

The frontend has a single switch that decides whether it calls the real backend or plays a scripted demo.

File: [`frontend/src/config/env.ts`](../frontend/src/config/env.ts)

```ts
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
export const MOCK_IDEA_ID = 'demo-restaurant-copilot'
```

- **Mock is ON by default.** If `VITE_USE_MOCK` is unset, the UI runs entirely from [`frontend/src/mock/`](../frontend/src/mock/) with timers — no backend, no network. This is what powers the "Load demo" button and the hackathon demo flow.
- **To use the real backend**, create a file `frontend/.env.local` containing:

  ```
  VITE_USE_MOCK=false
  ```

  Then restart the dev server (`npm run dev`). Vite only reads env files at startup.

- `MOCK_IDEA_ID` is the fixed workspace id used in demo mode. The real backend generates its own `idea_id` (a UUID) on `POST /api/workspace`; the frontend just stores and reuses whatever id you return.

Where the toggle is read:
- [`frontend/src/hooks/useWorkspace.ts`](../frontend/src/hooks/useWorkspace.ts) — `if (USE_MOCK) { ...mock... } else { fetch('/api/...') }`
- [`frontend/src/hooks/useSSEFeed.ts`](../frontend/src/hooks/useSSEFeed.ts) — same pattern for the SSE feed.

---

## 3. Vite proxy and base URL

File: [`frontend/vite.config.ts`](../frontend/vite.config.ts)

```ts
server: {
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true },
  },
}
```

- In **local dev**, the browser calls `/api/...` (same origin :5173) and Vite forwards to `http://localhost:8000`. So your FastAPI server must listen on **port 8000**.
- The frontend never hardcodes `http://localhost:8000` in app code — it always uses the relative path `/api/...`. That keeps it portable.
- For **production / Cloud Run**, you have two clean options:
  1. **Reverse proxy / same origin (recommended):** serve the built frontend and the API behind one domain, routing `/api/*` to the FastAPI service. No frontend code change needed.
  2. **Separate API origin:** if the API lives on a different domain, set the API base via an env var and prefix requests with it. (Currently requests use the literal string `/api`; if you go this route, introduce e.g. `VITE_API_BASE_URL` and prepend it in the two hooks above.) Update CORS accordingly (see section 8).

---

## 4. Endpoints the frontend already calls

These are live in the current UI. Implement them to match these shapes exactly.

### 4.1 `POST /api/workspace` — create a workspace from an idea

Request:
```json
{ "idea": "AI copilot for restaurant owners to manage inventory" }
```

Response:
```json
{
  "idea_id": "uuid-v4",
  "workspace_name": "AI copilot for restaurant owners...",
  "nodes": [ /* GraphNode[] - see section 5 */ ]
}
```

The frontend stores `idea_id`, switches to the dashboard, and renders `nodes` on the canvas. On first creation it is fine to return just the `core_idea` node; more nodes appear as agents unlock them (frontend re-fetches / receives updates).

Current backend stub: [`backend/api/workspace.py`](../backend/api/workspace.py).

### 4.2 `GET /api/workspace/{idea_id}` — fetch full workspace

Response: same shape as above (the complete current set of nodes). The frontend calls this to hydrate/refresh the graph.

### 4.3 `GET /api/feed?workspace_id={id}` — agent activity (SSE)

Server-Sent Events stream of agent activity. Each event's `data` is JSON:

```json
{ "text": "[Researcher R1] Running Reddit scan...", "type": "info", "node_id": "node-audience", "score": 63 }
```

- `node_id` and `score` are optional.
- The frontend ignores events with `type: "ping"` or empty `text` (used as keep-alive).

Current backend stub: [`backend/api/feed.py`](../backend/api/feed.py) (already emits demo lines via `sse-starlette`).

---

## 5. The exact node shape the UI renders

This is the contract that matters most for the canvas. It mirrors [`frontend/src/types/index.ts`](../frontend/src/types/index.ts) (`GraphNode`). Keep MongoDB documents serializable to this shape (camelCase keys as shown).

```jsonc
{
  "node_id": "node-audience",          // string, stable id (see canvas ids in section 6)
  "type": "audience",                  // NodeType enum (see below)
  "confidence": 72,                    // number 0-100
  "status": "needs_work",              // NodeStatus enum (see below)
  "sources": ["reddit", "gummysearch"],// string[]
  "source_pills": [                     // chips shown on the card
    { "label": "Reddit", "count": 847, "url": "https://..." }  // url optional
  ],
  "agent_notes": "847 Reddit posts analyzed...", // string
  "title": "Audience",                 // string shown as card header
  "summary": "Independent owners, 1-3 locations", // string, 1-2 lines
  "last_updated": "2026-06-05T05:30:00.000Z",     // ISO-8601
  "active_agents": ["researcher_1"],   // string[]; drives the pulsing agent chip

  // OPTIONAL - consumed by the right-hand detail panel (e.g. Market Intelligence)
  "overview": "Longer paragraph describing the node...",
  "pain_points": [
    { "label": "Inventory waste and spoilage", "percentage": 34 }
  ]
}
```

### Enums

`NodeType` (one of):
```
core_idea | audience | market_intelligence | competitors |
revenue | product_vision | tech_stack |
build | launch | observe | growth
```

`NodeStatus` (one of):
```
validated | needs_work | blocking | locked
```

- `locked` nodes render greyed out with a lock icon and are not clickable. Either return them with `status: "locked"` or omit them entirely — the frontend handles both (Track A decides; document in PR).
- Status to color mapping (UI side, for reference): `validated`=green, `needs_work`=amber, `blocking`=red, `locked`=grey.

### Optional fields the agents should populate when available
- `overview` and `pain_points` make the right panel rich (the Market Intelligence view shows ranked pain points). Safe to omit; the panel falls back to `summary`.

---

## 6. Canvas node IDs (so backend ids land in the right place)

The canvas uses a fixed tree layout keyed by `node_id`. File: [`frontend/src/utils/canvasLayout.ts`](../frontend/src/utils/canvasLayout.ts).

Expected ids and positions:

| node_id | type | row |
|---|---|---|
| `node-core` | core_idea | root |
| `node-audience` | audience | tier 2 |
| `node-market` | market_intelligence | tier 2 |
| `node-competitors` | competitors | tier 2 |
| `node-revenue` | revenue | tier 3 |
| `node-product` | product_vision | tier 3 |
| `node-tech` | tech_stack | tier 3 |
| `node-build` | build | tier 4 |
| `node-launch` | launch | tier 5 |
| `node-observe` | observe | tier 5 |
| `node-growth` | growth | tier 5 |

Two options for the backend:
1. **Easiest:** use these exact `node_id` strings in the graph documents, so nodes drop straight into the tree.
2. **Flexible:** use your own UUIDs. Then update `canvasLayout.ts` to map by `type` instead of `node_id` (small change), or have the API also return a `type` (it already does) and switch the layout lookup to `type`. If you want this, ping the Lead — it's a ~10-line frontend change.

Edges are derived from this layout (core -> tier2 -> tier3 -> build -> tier5). You do not need to send edges.

---

## 7. SSE feed format details

Matches [`backend/api/feed.py`](../backend/api/feed.py) and [`frontend/src/hooks/useSSEFeed.ts`](../frontend/src/hooks/useSSEFeed.ts).

- Transport: `text/event-stream` via `sse-starlette`'s `EventSourceResponse`.
- Each message event: `{"event": "message", "data": "<json string>"}` where the JSON is `{ text, type, node_id?, score? }`.
- `type` values the UI styles specially:
  - `info` — normal line (default color)
  - `critique` — amber; use the convention `"[Critique: 63/100] reason..."` so judges see the self-critique scores
  - `error` — red
  - `done` — green (stage complete)
  - `ping` — keep-alive; **ignored** by the client (send empty `text`)
- Keep-alive: emit a `ping` every ~15s so proxies don't drop the connection.
- The feed shows up in the right panel's "History" tab and the Agent Feed.

---

## 8. CORS and auth

Current allow-list: [`backend/main.py`](../backend/main.py)

```python
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]
```

- For local dev this is already correct.
- For deployment, **add your deployed frontend origin** (e.g. `https://cofounder.example.com`) to `allow_origins`, or drive it from the `CORS_ORIGINS` env var documented in [`team/00_CONTRACT_FREEZE.md`](../team/00_CONTRACT_FREEZE.md).
- SSE + credentials: if you later add cookies/auth, keep `allow_credentials=True` and list explicit origins (you cannot use `*` with credentials).
- The frontend currently sends no auth headers. If you add auth, coordinate with the Lead so the hooks attach the token.

---

## 9. Endpoints that are still mock-only (implement for full parity)

These features work in the demo via [`frontend/src/mock/demoEngine.ts`](../frontend/src/mock/demoEngine.ts) but are **not yet wired to the network**. The frozen contracts live in [`team/00_CONTRACT_FREEZE.md`](../team/00_CONTRACT_FREEZE.md). To make them real, implement the endpoint and replace the mock call site.

| Feature | Frozen endpoint | Where it's faked now | How to switch to real |
|---|---|---|---|
| Spawn agents | `POST /api/agents/spawn` | implicit in `startDemoSequence()` | call after `POST /api/workspace` returns |
| Pivot / diff classifier | `POST /api/agents/pivot` | `triggerPivotDemo()` in `demoEngine.ts` | replace with `fetch('/api/agents/pivot', ...)`, then blur `nodes_affected` |
| Today's Priority | `GET /api/priority?workspace_id=` | hardcoded in `startDemoSequence()` | fetch and call `setTodayPriority(...)` |
| Decision Journal | `GET /api/workspace/{id}/journal` | `MOCK_JOURNAL` in `mock/workspace.ts` | fetch in `DecisionJournal.tsx` |
| Export | `POST /api/export` | `MOCK_EXPORT_FILES` in `ExportModal.tsx` | fetch file list + download url |
| GitHub integration | `POST /api/integrations/github` | `integrations` array in store | post creds, flip `connected`, unlock Build node |
| PostHog integration | `POST /api/integrations/posthog` | `integrations` array in store | post creds, flip `connected`, unlock Observe node |

When you implement one, the swap is small and localized — each is a single `if (USE_MOCK)` branch plus a `fetch`. Do these through PRs to the Lead so the demo path stays intact.

---

## 10. Go-live checklist (local backend)

1. Backend: from `cofounder/backend`, install deps and run:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate            # Windows
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```
   Confirm `http://localhost:8000/health` returns `{ "status": "ok" }`.
2. Frontend: create `frontend/.env.local` with `VITE_USE_MOCK=false`.
3. Restart the frontend: `npm run dev`.
4. Open `http://localhost:5173`, type an idea, hit Start. Verify:
   - A workspace is created (network tab shows `POST /api/workspace` 200).
   - The Core Idea node renders on the canvas.
   - The Agent Feed / History tab streams SSE lines from `/api/feed`.
5. Verify persistence: restart the backend, reload the page — `GET /api/workspace/{id}` should rehydrate the graph (once Atlas is wired).

---

## 11. Deployment checklist (Google Cloud Run)

1. **Frontend build:** `cd frontend && npm run build` -> static assets in `frontend/dist/`.
2. **Serve the frontend:** either
   - put `dist/` behind the same domain as the API and route `/api/*` to the FastAPI service (recommended — no code change), or
   - host `dist/` on a static host/CDN and point it at the API origin via `VITE_API_BASE_URL` (requires the small hook change in section 3).
3. **Backend on Cloud Run:** containerize FastAPI (uvicorn/gunicorn), expose port `8080` (Cloud Run default) — note this differs from local `8000`, so make the port env-driven (`PORT`).
4. **Env / secrets** (never commit `.env`): `MONGODB_URI`, `MONGODB_DB`, `GOOGLE_API_KEY`, `GEMINI_*`, integration keys, and `CORS_ORIGINS=<your frontend origin>`. Use Secret Manager.
5. **CORS:** add the deployed frontend origin to `allow_origins` (section 8).
6. **SSE on Cloud Run:** ensure response streaming is not buffered; keep the ~15s `ping` keep-alive; set a generous request timeout for the feed connection.
7. **Smoke test in prod:** intake -> canvas, SSE feed streaming, refresh rehydrates from Atlas.

---

## 12. Quick reference: files the backend dev should know

| File | Why it matters |
|---|---|
| [`frontend/src/config/env.ts`](../frontend/src/config/env.ts) | The mock vs real toggle |
| [`frontend/vite.config.ts`](../frontend/vite.config.ts) | `/api` proxy target (port 8000) |
| [`frontend/src/hooks/useWorkspace.ts`](../frontend/src/hooks/useWorkspace.ts) | Calls `POST/GET /api/workspace` |
| [`frontend/src/hooks/useSSEFeed.ts`](../frontend/src/hooks/useSSEFeed.ts) | Consumes `/api/feed` SSE |
| [`frontend/src/types/index.ts`](../frontend/src/types/index.ts) | Canonical `GraphNode` shape + enums |
| [`frontend/src/utils/canvasLayout.ts`](../frontend/src/utils/canvasLayout.ts) | Node ids -> tree positions |
| [`frontend/src/mock/workspace.ts`](../frontend/src/mock/workspace.ts) | Reference data shapes (copy these JSON shapes) |
| [`frontend/src/mock/demoEngine.ts`](../frontend/src/mock/demoEngine.ts) | Where mock-only features live |
| [`team/00_CONTRACT_FREEZE.md`](../team/00_CONTRACT_FREEZE.md) | The frozen API contract (source of truth) |

If anything here conflicts with `00_CONTRACT_FREEZE.md`, the contract wins — and raise it with the Lead so this doc gets updated.
