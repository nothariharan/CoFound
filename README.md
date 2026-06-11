# CoFounder

The Startup Founder Operating System — a persistent AI workspace that takes a startup from raw idea to validated, built, launched, and growing company.

**Hackathon:** Google Cloud Rapid Agent Hackathon · MongoDB Track  
**Stack:** Gemini 2.5 Pro · MongoDB Atlas · Google Cloud Agent Builder

## Team Parallel Build

Building with 3 people? Start here: **[team/README.md](team/README.md)**

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (required for `mongodb-mcp-server` at runtime)
- MongoDB Atlas cluster (CoFound track uses cluster `cofound.ivajiy8.mongodb.net`)
- Google AI Studio API key (`GOOGLE_API_KEY`)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Scrapling powers broad web/community research. If you want browser-backed
stealth fetching for blocked pages, run this once after installing
requirements:

```bash
scrapling install
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — enter your idea to see the workspace shell.

### Docker (optional)

```bash
cp .env.example .env
docker compose up
```

## Environment

Copy `.env.example` to `.env` at the repo root and fill in:

| Variable | Required | Purpose |
|----------|----------|---------|
| `MONGODB_URI` | Yes | Atlas connection for workspace API routes |
| `MDB_MCP_CONNECTION_STRING` | Yes | Same URI for MongoDB MCP server (agent persistence) |
| `USE_MONGODB_MCP` | Yes | Set `true` to route agents through MCP |
| `GOOGLE_API_KEY` | Yes | Gemini + Google ADK Planner |
| `GEMINI_PRO_MODEL` | No | Default `gemini-2.5-pro` |

Start backend from `cofounder/` so `main.py` loads the root `.env`.

### Verify the stack is live

```bash
curl http://localhost:8000/health
```

Expected when fully configured:

```json
{"status":"ok","store":"atlas","agent_store":"mcp","mongodb_cluster":"CoFound"}
```

- `store: atlas` — workspace API uses MongoDB Atlas
- `agent_store: mcp` — agents read/write via MongoDB MCP server
- `mongodb_cluster: CoFound` — MCP connected to the CoFound cluster

## MongoDB MCP Integration (Partner Track)

CoFounder routes **agent persistence** through the official **MongoDB MCP server** at runtime:

| Piece | Implementation |
|-------|----------------|
| MCP client | `backend/mdb_mcp/client.py` — stdio session via `mcp` Python SDK |
| MCP server | `mongodb-mcp-server` (spawned via `npx -y mongodb-mcp-server`) |
| Agent store | `backend/mdb_mcp/graph_store.py` — `McpGraphStore` |
| Tools used | `find`, `aggregate`, `insert-many`, `update-many` |
| Runtime path | `POST /api/agents/spawn` → `get_agent_store()` → MCP `find` / `aggregate` |
| SSE labels | `[MongoDB MCP] Reading workspace via find`, `[MongoDB MCP] Knowledge base search via aggregate` |

Workspace CRUD API routes (`/api/workspace`) use Atlas directly; agent orchestration, research, pivot, and export use MCP. Both target the same Atlas database.

**Prerequisites:** Node.js/npx on the machine running the backend so `mongodb-mcp-server` can start.

## Google Cloud Agent Builder Integration

CoFounder uses **Google ADK** (Agent Development Kit) for the Planner agent at runtime:

| Piece | Implementation |
|-------|----------------|
| Framework | `google-adk` (`backend/agents/adk/`) |
| Agent | `cofounder_planner` — decomposes workspace state into research tasks |
| Model | Gemini 2.5 Pro via Google AI API (`GOOGLE_API_KEY`) |
| Runtime path | `POST /api/agents/spawn` → `planner.plan()` → `agents.adk.runner.run_planner_agent()` |
| SSE label | `[Planner/ADK]` in the agent feed |

Vertex AI Agent Engine deployment is documented in `backend/agents/adk/vertex_deploy.py` and `cloud_run/deploy.sh` but **disabled by default** (requires GCP billing). The standalone planner service lives in `cloud_run/main.py` for Cloud Run / Render hosting.

**Do not set** `GOOGLE_GENAI_USE_VERTEXAI=true` unless billing is enabled.

## Project Structure

```
cofounder/
├── backend/
│   ├── agents/adk/   # Google ADK Planner agent
│   └── mdb_mcp/      # MongoDB MCP client + agent GraphStore
├── frontend/         # Vite + React + React Flow canvas
├── team/             # 3-person parallel build guide (roles, branches, criteria)
├── scripts/          # Atlas seeding and index setup
├── cloud_run/        # ADK Planner service (Cloud Run / Render)
└── docs/             # Architecture and demo docs
```

## Verify required hackathon tech (runtime)

Judges expect all three imported and called — not just named in the README:

```bash
# Gemini + ADK
grep -r "google.adk" backend/agents/adk/
grep -r "run_planner_agent" backend/agents/planner.py

# MongoDB MCP
grep -r "call_mcp_tool" backend/mdb_mcp/
curl http://localhost:8000/health   # agent_store should be "mcp"
```

Trigger a research spawn in the UI and confirm the agent feed shows `[Planner/ADK]` and `[MongoDB MCP]` lines.

## Build Plan

| Days | Milestone |
|------|-----------|
| 1-2  | MongoDB Atlas schema + node documents |
| 3-4  | Research loop + SSE live feed |
| 5-6  | Canvas + confidence rings + agent chips |
| 7    | Dialogue agent + diff classifier pivot |
| 8    | Build Node (GitHub) |
| 9    | Observe Node (PostHog) + Growth Node |
| 10   | Export package + demo polish |

## License

MIT — see [LICENSE](LICENSE).
