![CoFounder — The Startup Founder Operating System](docs/banner.png)

# CoFounder

**The Startup Founder Operating System** — a persistent AI workspace that takes a startup from raw idea to validated, built, launched, and growing company.

CoFounder represents your startup as a **living knowledge graph**. A central orchestrator coordinates specialist sub-agents, streams live progress, and surfaces the highest-ROI next action — all backed by MongoDB Atlas and Google Gemini.

**Live Demo:** [cofounder-alpha.vercel.app](https://cofounder-alpha.vercel.app)

**Repository:** [github.com/nothariharan/CoFound](https://github.com/nothariharan/CoFound)

---

## What CoFounder Does

- **Knowledge graph canvas** — 11-node startup tech tree with confidence rings, unlock logic, and live agent chips
- **Multi-agent research** — Orchestrator spawns parallel researchers on canonical nodes or dynamic custom research topics
- **Voice-first orchestrator** — Talk or type to start research, get status, hand off priorities, pivot, and export
- **Live activity feed** — Server-Sent Events stream agent progress in real time
- **Surgical pivot** — Diff classifier resets only affected nodes when the idea changes
- **Integrations** — GitHub (build signals) and PostHog (funnel observe)
- **Export package** — Download a scaffold zip when the graph is ready

---

## Platform Requirements

CoFounder is built on the required partner stack and uses each integration at runtime:

| Requirement | Implementation |
|-------------|----------------|
| **MongoDB Atlas** | Workspace graph, task queue, decision journal, dead-end log, build/observe events, vector knowledge base |
| **MongoDB MCP Server** | Official [`mongodb-mcp-server`](https://github.com/mongodb-js/mongodb-mcp-server) — agent persistence via `find`, `aggregate`, `insert-many`, `update-many` at runtime |
| **Google Gemini 2.5 Pro** | Orchestrator synthesis, dialogue agent, diff classifier, export narrative |
| **Google Gemini Flash** | High-volume researcher loops and critique scoring |
| **Google ADK (Agent Development Kit)** | `cofounder_planner` decomposes workspace state into research tasks via `google-adk` |
| **Research tools** | Firecrawl, Reddit, Scrapling (web + community evidence) |
| **Voice (optional)** | Deepgram STT/TTS proxied server-side for the orchestrator orb |

### MongoDB Atlas use cases (7+)

1. Knowledge graph storage (`startup_graphs`)
2. Agent task queue (`task_queue`)
3. Vector / knowledge-base search (`product_knowledge_base`)
4. Decision journal (`decision_journal`)
5. Dead-end log (`dead_ends`)
6. Build event store (`build_events`)
7. Observe event store (`observe_events`)

### Verify the stack is live

```bash
curl http://localhost:8000/health
```

Expected when fully configured:

```json
{"status":"ok","store":"atlas","agent_store":"mcp","mongodb_cluster":"CoFound"}
```

Trigger a research spawn and confirm the agent feed shows `[Planner/ADK]` and `[MongoDB MCP]` lines.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (required for `mongodb-mcp-server` at runtime)
- MongoDB Atlas cluster
- [Google AI Studio API key](https://aistudio.google.com/app/apikey) (`GOOGLE_API_KEY`)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Scrapling powers broad web/community research. For browser-backed stealth fetching on blocked pages:

```bash
scrapling install
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — enter your idea to open the workspace.

### Docker (optional)

```bash
cp .env.example .env
docker compose up
```

---

## Environment

Copy `.env.example` to `.env` at the repo root and fill in:

| Variable | Required | Purpose |
|----------|----------|---------|
| `MONGODB_URI` | Yes | Atlas connection for workspace API routes |
| `MDB_MCP_CONNECTION_STRING` | Yes | Same URI for MongoDB MCP server (agent persistence) |
| `USE_MONGODB_MCP` | Yes | Set `true` to route agents through MCP |
| `GOOGLE_API_KEY` | Yes | Gemini + Google ADK Planner |
| `GEMINI_PRO_MODEL` | No | Default `gemini-2.5-pro` |
| `FIRECRAWL_API_KEY` | No | Web research tool |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | No | Community research tool |
| `DEEPGRAM_API_KEY` | No | Voice STT/TTS for orchestrator |
| `GITHUB_TOKEN` | No | Build node integration |
| `POSTHOG_API_KEY` | No | Observe node integration |

Start the backend from the repo root so `main.py` loads the root `.env`.

---

## Architecture

```
User Input → Orchestrator → Planner (ADK) → Researcher(s) → MongoDB Graph
                ↓                                    ↓
         Voice / Chat UI                      SSE Feed → Frontend
                ↓
         Today's Priority
```

See [docs/architecture.md](docs/architecture.md) and [docs/mongodb_schema.md](docs/mongodb_schema.md) for full detail.

### MongoDB MCP integration

| Piece | Path |
|-------|------|
| MCP client | `backend/mdb_mcp/client.py` |
| Agent store | `backend/mdb_mcp/graph_store.py` |
| Runtime path | `POST /api/agents/spawn` → `get_agent_store()` → MCP tools |

Workspace CRUD (`/api/workspace`) uses Atlas directly; agent orchestration, research, pivot, and export use MCP. Both target the same Atlas database.

### Google ADK integration

| Piece | Path |
|-------|------|
| ADK agent | `backend/agents/adk/planner_agent.py` |
| Runtime path | `POST /api/agents/spawn` → `planner.plan()` → `run_planner_agent()` |

Optional Cloud Run / Vertex deployment notes live in `cloud_run/` (disabled by default; requires GCP billing).

---

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/workspace` | Create workspace from idea |
| `GET` | `/api/workspace/{id}` | Full graph + nodes |
| `POST` | `/api/orchestrator/chat` | Conversational orchestrator (tools + voice replies) |
| `POST` | `/api/agents/spawn` | Bulk research session (Planner + researchers) |
| `POST` | `/api/agents/spawn-research-agents` | Create custom research nodes + parallel agents |
| `GET` | `/api/feed` | SSE live agent feed |
| `POST` | `/api/voice/stt` | Speech-to-text (Deepgram proxy) |
| `POST` | `/api/voice/tts` | Text-to-speech (Deepgram proxy) |

See [docs/architecture.md](docs/architecture.md) and [docs/mongodb_schema.md](docs/mongodb_schema.md) for full API and schema detail.

---

## Project Structure

```
cofounder/
├── backend/
│   ├── agents/          # Orchestrator, researcher, planner, dialogue, export
│   ├── agents/adk/      # Google ADK Planner agent
│   ├── mdb_mcp/         # MongoDB MCP client + agent GraphStore
│   ├── api/             # FastAPI routes
│   └── tools/           # Firecrawl, Reddit, Deepgram, GitHub, PostHog
├── frontend/            # Vite + React + React Flow canvas
├── docs/                # Architecture, schema, banner
├── scripts/             # Atlas seeding and index setup
└── cloud_run/           # Optional ADK Planner service (Cloud Run)
```

---

## License

MIT — see [LICENSE](LICENSE).
