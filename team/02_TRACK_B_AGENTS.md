# Track B — Agents, Gemini & GCP

**Owner:** Teammate B  
**Branch:** `feat/track-b-agents`  
**PRs to:** `main` (Lead merges)

---

## Mission

Build the multi-agent intelligence layer. Orchestrator spawns researchers, they self-critique, commit findings to the graph, and stream live progress via SSE. Gemini Pro for synthesis, Flash for high-volume research.

---

## Files You Own

```
backend/
├── agents/
│   ├── orchestrator.py
│   ├── planner.py
│   ├── researcher.py
│   ├── dialogue.py
│   ├── diff_classifier.py
│   ├── growth_agent.py
│   ├── export_agent.py
│   ├── build_observer.py      # Logic only — Lead owns UI wiring
│   └── observe_agent.py       # Logic only — Lead owns UI wiring
├── tools/
│   ├── firecrawl.py
│   ├── exa_search.py
│   ├── reddit_praw.py
│   ├── gummysearch.py
│   ├── github_search.py
│   ├── producthunt.py
│   └── posthog_client.py
├── critique/
│   └── scorer.py
├── sse/
│   └── feed.py
├── export/
│   ├── generator.py
│   └── zipper.py
├── personas/
│   └── prompts.py
├── llm/                         # NEW — create this
│   ├── __init__.py
│   └── gemini.py                # Pro/Flash router
└── api/
    ├── agents.py
    ├── feed.py                  # Replace demo SSE with real events
    └── export.py
```

## Files You Must NOT Edit

- `frontend/` (any file)
- `backend/graph/schema.py` (request changes via issue to Lead)
- `backend/graph/node_manager.py` (use GraphStore protocol)
- `backend/main.py` (paste router snippet in PR)
- `backend/api/workspace.py`, `nodes.py`

---

## Task List

### Phase 1 — LLM Foundation (Days 1–2)

- [ ] **B1.** Create `backend/llm/gemini.py`:
  ```python
  async def generate_pro(prompt: str, system: str = "") -> str: ...
  async def generate_flash(prompt: str, system: str = "") -> str: ...
  ```
- [ ] **B2.** Model routing config from `.env`:
  - Pro: Orchestrator, Planner, Dialogue, Export
  - Flash: Researcher, Build Observer, Observe Agent, Critique scorer
- [ ] **B3.** Orchestrator skeleton:
  - Read workspace from GraphStore
  - Decide if research needed
  - Spawn Planner
- [ ] **B4.** Planner skeleton:
  - Output 6–10 tasks as JSON (use mock KB query until Track A merges)
  - Enqueue tasks via `GraphStore.enqueue_task()`
- [ ] **B5.** PR #1: "Gemini wrapper + Orchestrator/Planner skeleton"

### Phase 2 — Research Loop (Days 3–4)

- [ ] **B6.** Implement `critique/scorer.py`:
  ```python
  async def score(result: dict, task: str) -> CritiqueResult:
      # Returns: score (0-100), verdict, reason, requery, accept
  ```
- [ ] **B7.** Researcher loop in `researcher.py`:
  1. Pop task from queue
  2. Select tools from manifest
  3. Execute tools → raw JSON
  4. Self-critique score
  5. ≥80 → commit to graph via GraphStore
  6. 50–79 → soft reset (requery, max 3 attempts)
  7. <50 → hard reset → log dead end
- [ ] **B8.** Wire at least 2 tools (priority: Reddit + Firecrawl OR Exa)
- [ ] **B9.** Real SSE in `sse/feed.py` + `api/feed.py`:
  - Publish events as researchers run
  - Format: `[Critique: 63/100] Too broad`
- [ ] **B10.** `POST /api/agents/spawn` in `agents.py`
- [ ] **B11.** PR #2: "Researcher loop + live SSE feed"

### Phase 3 — Dialogue & Pivot (Days 5–7)

- [ ] **B12.** Dialogue agent: read full graph → synthesize brief → one targeted question
- [ ] **B13.** Diff classifier in `diff_classifier.py`:
  - Input: pivot message
  - Output: `nodes_affected`, `nodes_unchanged` (per contract)
- [ ] **B14.** `POST /api/agents/pivot` endpoint
- [ ] **B15.** Re-spawn researchers only for affected nodes
- [ ] **B16.** PR #3: "Dialogue + diff classifier pivot"

### Phase 4 — Lifecycle Agents (Days 8–9)

- [ ] **B17.** Build Observer: poll GitHub REST API every 5 min, infer features from commits
- [ ] **B18.** Observe Agent: query PostHog funnel, detect >5pp conversion drop
- [ ] **B19.** Growth Agent: synthesize Observe + Market + Competitors → ranked recommendations
- [ ] **B20.** `GET /api/priority?workspace_id={id}` endpoint
- [ ] **B21.** PR #4: "Build/Observe/Growth agents"

### Phase 5 — Export (Day 10)

- [ ] **B22.** Export agent: generate README, tech_stack.md, ui_spec.md, .cursorrules, HANDOFF.md
- [ ] **B23.** `export/zipper.py`: assemble zip, serve download
- [ ] **B24.** `POST /api/export` + download endpoint
- [ ] **B25.** PR #5: "Export zip generation"

---

## Acceptance Criteria (Per PR)

### PR #1 — Gemini + Skeleton
- [ ] `generate_pro()` and `generate_flash()` return valid responses with `GOOGLE_API_KEY`
- [ ] Orchestrator reads workspace and calls Planner
- [ ] Planner outputs valid task manifest JSON
- [ ] Tasks enqueued via GraphStore (works with MemoryGraphStore until Atlas merges)
- [ ] No API keys committed

### PR #2 — Research Loop + SSE
- [ ] `POST /api/agents/spawn` starts research session
- [ ] SSE feed shows live agent lines (not demo placeholders)
- [ ] Critique scores appear: `[Critique: 63/100]`
- [ ] ≥2 research tasks complete and update node confidence in graph
- [ ] Dead ends logged via `GraphStore.log_dead_end()`
- [ ] Soft reset retries up to 3 times

### PR #3 — Pivot
- [ ] `POST /api/agents/pivot` returns correct affected/unchanged nodes
- [ ] Only affected nodes re-researched
- [ ] Dialogue agent returns exactly one question after Stage 2

### PR #4 — Lifecycle Agents
- [ ] Build Observer updates Build Node on GitHub commits
- [ ] Observe Agent detects funnel drop and triggers Growth
- [ ] `GET /api/priority` returns actionable recommendation

### PR #5 — Export
- [ ] `POST /api/export` returns downloadable zip
- [ ] Zip contains ≥ 5 files: README.md, tech_stack.md, ui_spec.md, .cursorrules, HANDOFF.md
- [ ] Files contain real data from graph (not placeholders)

---

## Karpathy Self-Critique Loop (Reference)

```
1. Pop next pending task from task_queue
2. Select tools from manifest based on task type
3. Execute tools → get raw JSON results
4. Run self-critique scorer:
   Score ≥ 80  → accept → write to graph → mark task done
   Score 50-79 → soft reset → refine query → re-run (increment attempts)
   Score < 50  → hard reset → log dead end → move on
5. Budget check → continue or surface to user
6. Stream status update to SSE feed
```

---

## Tool Priority (Tier 1 for Demo)

| Tool | File | Demo use |
|------|------|----------|
| Firecrawl | `tools/firecrawl.py` | Competitor landing pages |
| Exa | `tools/exa_search.py` | Market signals |
| Reddit | `tools/reddit_praw.py` | Pain point mining |
| GitHub | `tools/github_search.py` | Build Node + moat risk |
| PostHog | `tools/posthog_client.py` | Observe Node funnel |

Minimum for demo: **2 tools working** (Reddit + one of Firecrawl/Exa).

---

## SSE Publishing Pattern

```python
# In researcher.py after each step:
await feed.publish(workspace_id, {
    "text": f"[Researcher R1] Running Reddit scan...",
    "type": "info",
    "node_id": node.node_id,
})

await feed.publish(workspace_id, {
    "text": f"[Critique: {score}/100] {reason}",
    "type": "critique",
    "node_id": node.node_id,
    "score": score,
})
```

---

## Dependencies on Other Tracks

| Need from | What | When |
|-----------|------|------|
| Track A | `GraphStore` / AtlasGraphStore | Day 2 (use MemoryGraphStore until then) |
| Track A | `task_queue` CRUD | Day 4 |
| Track A | Vector KB search for Planner | Day 5 |
| Lead | Merge agent routes in `main.py` | Each PR |
| Lead | Frontend consumes SSE | Day 4+ |

---

## Local Fallback Strategy (Until Track A Merges)

Use `MemoryGraphStore` implementing the protocol from `00_CONTRACT_FREEZE.md`. Do not block on Atlas — build agents against the protocol interface. When Track A merges, swap injection to `AtlasGraphStore` with zero agent code changes.

---

## Blockers — Escalate to Lead If

- Need new field in `BaseNode` schema
- GraphStore method missing from Track A
- Gemini API quota/rate limits
- Tool API key not available (check `.env.example`)
