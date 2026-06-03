# CoFounder — 3-Person Parallel Build Guide

This directory is the single source of truth for how the team builds CoFounder in parallel without stepping on each other.

**Repo:** https://github.com/nothariharan/CoFound.git  
**Hackathon deadline:** June 12, 2026

---

## Team Roles

| Person | Track | Branch | Responsibility |
|--------|-------|--------|----------------|
| **Teammate A** | Data & Graph | `feat/track-a-mongodb` | MongoDB Atlas, graph persistence, unlock engine, task queue, vector KB, decision journal |
| **Teammate B** | Agents & GCP | `feat/track-b-agents` | Orchestrator, Planner, Researcher loop, Gemini, tools, SSE feed, export agent |
| **Lead (Hariharan)** | Experience & Integration | `feat/track-c-frontend` | Frontend canvas, integrations UI, GitHub/PostHog, **all merges to `main`** |

---

## Read These First (In Order)

1. **[00_CONTRACT_FREEZE.md](./00_CONTRACT_FREEZE.md)** — Shared API shapes and types. Do not code until all 3 agree.
2. **[BRANCHING.md](./BRANCHING.md)** — How to branch, PR, and merge.
3. **Your track guide:**
   - Teammate A → [01_TRACK_A_MONGODB.md](./01_TRACK_A_MONGODB.md)
   - Teammate B → [02_TRACK_B_AGENTS.md](./02_TRACK_B_AGENTS.md)
   - Lead → [03_TRACK_C_FRONTEND.md](./03_TRACK_C_FRONTEND.md)
4. **[CONFLICT_ZONES.md](./CONFLICT_ZONES.md)** — Files you must not edit.
5. **[INTEGRATION_WEEKLY.md](./INTEGRATION_WEEKLY.md)** — Day-by-day schedule.
6. **[MERGE_CHECKLIST.md](./MERGE_CHECKLIST.md)** — Lead uses this before every merge.

---

## Day 0 Checklist (All 3, ~2 hours)

- [ ] Clone repo: `git clone https://github.com/nothariharan/CoFound.git`
- [ ] Read `00_CONTRACT_FREEZE.md` together
- [ ] Agree on API contracts (no changes without Lead approval)
- [ ] Set up shared credentials (Atlas URI, Gemini key) in team password manager — never commit `.env`
- [ ] Each person creates their feature branch from latest `main`
- [ ] Schedule daily 15-min sync (same time every day)

---

## Daily Sync Format (15 min)

Each person answers:

1. **Yesterday:** What did I ship? PR link?
2. **Today:** What files am I touching?
3. **Blockers:** What am I waiting on from another track?

Lead additionally states: what's on `main`, what's merging today.

---

## Merge Order (Critical)

```
Sprint 1 (Days 1–2):  Track A merges first  → Atlas persistence
Sprint 2 (Days 3–4):  Track B merges second → Real agent feed
Sprint 3 (Days 5–6):  Track C + fixes from A/B
Sprint 4 (Days 7–10): All tracks, Lead integrates daily
```

Only the **Lead merges to `main`**. Teammates open PRs; Lead reviews and merges.

---

## Quick Commands

```bash
# Start of each day — everyone
git checkout main
git pull origin main
git checkout feat/track-X-...
git rebase main

# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

---

## Definition of Done (Whole Project)

See acceptance criteria in each track guide. Project is done when:

1. 3-minute demo script runs end-to-end
2. MongoDB used for 5+ distinct Atlas use cases
3. Two agent chips visible on canvas simultaneously
4. Pivot blurs only affected nodes
5. GitHub + PostHog integrations live
6. Export zip downloads from UI

---

## Questions?

Open a GitHub issue tagged `team-sync` or raise in daily standup. Schema changes always go through Lead first.
