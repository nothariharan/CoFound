# Track C — Frontend, Integrations & Merge (Lead)

**Owner:** Lead (Hariharan)  
**Branch:** `feat/track-c-frontend`  
**Also responsible for:** All merges to `main`

---

## Mission

Make the graph the interface. Wire the frontend to real backend APIs, build integration flows, orchestrate merges, and deliver a demo-ready product in 3 minutes.

---

## Files You Own

```
frontend/src/                    # Everything
backend/api/integrations.py      # GitHub + PostHog connect endpoints
backend/main.py                  # Router registration (you merge all routes)
```

## Coordinate With (Don't Deep-Edit)

- `backend/agents/build_observer.py` — Track B implements logic; you wire UI
- `backend/agents/observe_agent.py` — Track B implements logic; you wire UI
- `backend/graph/schema.py` — Track A owns; you sync `frontend/src/types/index.ts`

---

## Task List

### Phase 0 — Setup (Day 0)

- [ ] **C0.** Run contract freeze meeting with both teammates
- [ ] **C0b.** Create `feat/track-c-frontend` branch
- [ ] **C0c.** Set up GitHub branch protection on `main` (optional but recommended)

### Phase 1 — Integration Foundation (Days 1–2)

- [ ] **C1.** Merge Track A PR #1 (Atlas persistence)
- [ ] **C2.** Sync `frontend/src/types/index.ts` with any schema changes
- [ ] **C3.** Verify intake → dashboard works against Atlas-backed API
- [ ] **C4.** Add workspace polling or refetch after agent spawn

### Phase 2 — Live Canvas (Days 3–5)

- [ ] **C5.** Merge Track B PR #2 (Research loop + SSE)
- [ ] **C6.** Agent Feed: consume real SSE events (remove demo-only handling)
- [ ] **C7.** Agent chips on nodes: show `active_agents` from node data
- [ ] **C8.** Two chips on two different nodes simultaneously (demo moment)
- [ ] **C9.** Confidence ring animation when confidence updates
- [ ] **C10.** Stage 2 unlock: Audience, Market, Competitors animate in when API returns them
- [ ] **C11.** Stage 3 unlock: Revenue, Product Vision, Tech Stack appear
- [ ] **C12.** Source pills populate from `source_pills` on nodes

### Phase 3 — Pivot Demo (Days 6–7)

- [ ] **C13.** Merge Track B PR #3 (Diff classifier)
- [ ] **C14.** Pivot input in Node Chat or dedicated UI
- [ ] **C15.** On pivot response: blur affected nodes (CSS filter), keep unchanged nodes solid
- [ ] **C16.** Terminal shows "Diff identified. Re-researching..."
- [ ] **C17.** Decision Journal overlay (`components/journal/DecisionJournal.tsx`):
  - Fetch from `GET /api/workspace/{id}/journal`
  - Timeline with event, reason, evidence, confidence delta
  - Click entry to highlight affected node

### Phase 4 — Integrations (Days 8–9)

- [ ] **C18.** Implement `POST /api/integrations/github` in `integrations.py`
- [ ] **C19.** GitHub connect UI in LeftRail — green dot when connected
- [ ] **C20.** Build Node appears and shows progress (features completed, missing, PRD alignment)
- [ ] **C21.** Implement `POST /api/integrations/posthog`
- [ ] **C22.** PostHog connect UI in LeftRail
- [ ] **C23.** Observe Node shows funnel metrics + delta
- [ ] **C24.** NotificationBar: "Signup conversion dropped from 17% to 8%"
- [ ] **C25.** Growth Node displays ranked recommendations
- [ ] **C26.** Today's Priority bar wired to `GET /api/priority`

### Phase 5 — Export & Verification (Day 10)

- [ ] **C27.** Merge Track B PR #5 (Export zip)
- [ ] **C28.** Export modal (`components/export/ExportModal.tsx`):
  - Trigger export
  - Show file list
  - Download zip
- [ ] **C29.** Export button enabled when graph reaches Build stage
- [ ] **C30.** Run the live workflow end-to-end
- [ ] **C31.** Record 3-minute demo video
- [ ] **C32.** Final merge + README update

---

## Acceptance Criteria

### After Track A Merge
- [ ] Intake → dashboard persists across server restart
- [ ] Core Idea node displays with confidence ring
- [ ] Types in frontend match backend schema

### After Track B Merge (Research)
- [ ] Agent Feed shows real SSE (not static demo lines)
- [ ] Critique scores visible in terminal
- [ ] Agent chips pulse on active nodes
- [ ] Two chips visible on two nodes during parallel research

### Pivot Demo
- [ ] Type "pivot to B2B" → Audience + Competitors blur
- [ ] Core Idea stays fully visible (no blur)
- [ ] Feed shows re-research message

### Integrations
- [ ] GitHub: connect repo → green dot → Build Node unlocks
- [ ] Build Node shows commit summary + missing features
- [ ] PostHog: connect → Observe Node shows conversion data
- [ ] Conversion drop triggers Growth recommendation
- [ ] Today's Priority updates to top recommendation

### Final
- [ ] `npm run build` passes with zero errors
- [ ] 3-minute demo script runnable without manual backend steps
- [ ] Export zip downloads from UI

---

## Merge Workflow (Your Responsibility)

See [MERGE_CHECKLIST.md](./MERGE_CHECKLIST.md) for full checklist.

**Quick process:**
1. Teammate opens PR to `main`
2. You pull branch locally: `git fetch && git checkout feat/track-X`
3. Run acceptance criteria for that track
4. Merge if green; request changes if not
5. Notify both teammates to rebase on updated `main`

**Expected merge sequence:**
```
Day 2:  Merge Track A PR #1
Day 4:  Merge Track A PR #2 + Track B PR #1
Day 5:  Merge Track B PR #2
Day 7:  Merge Track B PR #3 + Track A PR #3
Day 9:  Merge Track B PR #4 + Track A PR #4
Day 10: Merge all remaining + final integration
```

---

## Router Registration Snippets

When teammates PR, they paste this in description. You add to `main.py`:

**Track A:**
```python
from api.nodes import router as nodes_router
app.include_router(nodes_router, prefix="/api")
```

**Track B:**
```python
from api.agents import router as agents_router
from api.export import router as export_router
app.include_router(agents_router, prefix="/api")
app.include_router(export_router, prefix="/api")
```

**Track C (you):**
```python
from api.integrations import router as integrations_router
app.include_router(integrations_router, prefix="/api")
```

---

## UI Design Rules (Do Not Break)

- Clean, minimal — no gradients, no emojis
- Lucide React icons only
- **Dark mode (default):** warm neutral palette — `#1F1E1D` bg, `#EDEDEB` text, `#C96442` accent, `#3A3936` borders
- Inter font, semantic CSS tokens via Tailwind/shadcn
- Single workspace — no page routing
- GSAP animations with `prefers-reduced-motion` support

---

## Demo Moments Checklist

These are the 10 seconds that win the hackathon. Verify each works:

| # | Moment | How to verify |
|---|--------|---------------|
| 1 | Blank slate intake | Only textarea visible on load |
| 2 | Core Idea alone on canvas | Single node, centered |
| 3 | Agent Feed streaming | Terminal lines appear live |
| 4 | Two agent chips | R1 on Audience, R2 on Competitors |
| 5 | Critique scores | `[Critique: 63/100]` in feed |
| 6 | Stage 2 unlock animation | 3 nodes appear from Core Idea |
| 7 | Pivot blur | Audience + Competitors blur, Core Idea solid |
| 8 | Decision Journal | Click journal → timeline with evidence |
| 9 | Build Node progress | GitHub connected → confidence climbing |
| 10 | Conversion drop | PostHog → "17% to 8%" → Growth recommendation |

---

## Dependencies on Other Tracks

| Need from | What | When |
|-----------|------|------|
| Track A | Atlas-backed workspace API | Day 2 |
| Track A | Journal API | Day 7 |
| Track B | Real SSE feed | Day 4 |
| Track B | Pivot endpoint | Day 7 |
| Track B | Priority endpoint | Day 9 |
| Track B | Export endpoint | Day 10 |
