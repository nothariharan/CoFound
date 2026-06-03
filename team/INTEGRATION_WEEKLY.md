# 10-Day Parallel Integration Schedule

**Deadline:** June 12, 2026  
**Daily sync:** 15 min, same time every day

---

## Week Overview

| Week | Focus | Key merge |
|------|-------|-----------|
| Days 1–2 | Foundation | Track A → Atlas persistence |
| Days 3–4 | Intelligence | Track B → Research loop + SSE |
| Days 5–7 | Experience | Track C → Live canvas + pivot |
| Days 8–10 | Lifecycle | Integrations + export + demo |

---

## Day-by-Day

### Day 0 — Contract Freeze (All 3)
| Person | Tasks |
|--------|-------|
| **All** | Read `team/README.md` + `00_CONTRACT_FREEZE.md` |
| **All** | Agree on API contracts |
| **All** | Create feature branches from `main` |
| **Lead** | Share Atlas + Gemini credentials via password manager |
| **Lead** | Schedule daily sync time |

**Exit criteria:** All 3 branches created. Contracts agreed. No coding yet.

---

### Day 1 — Foundation Start
| Track A | Track B | Lead |
|---------|---------|------|
| Atlas cluster setup | `llm/gemini.py` wrapper | Contract freeze meeting |
| `backend/db/connection.py` | Orchestrator skeleton | Create `feat/track-c-frontend` |
| Motor client + collections | Planner skeleton | Verify scaffold runs locally |

**Sync question:** Is Atlas URI working for everyone?

---

### Day 2 — Persistence PR
| Track A | Track B | Lead |
|---------|---------|------|
| NodeManager CRUD | Planner outputs task manifest | **Merge Track A PR #1** |
| Replace in-memory store | Enqueue via MemoryGraphStore | Sync frontend types |
| **Open PR #1** | Test with mock store | Intake → dashboard on Atlas |

**Merge:** Track A PR #1 (Atlas persistence)  
**Exit criteria:** Workspace survives server restart.

---

### Day 3 — Graph Logic
| Track A | Track B | Lead |
|---------|---------|------|
| Unlock engine wired | Researcher loop start | Canvas refetch on workspace update |
| Decision journal writes | Critique scorer | Poll workspace API after spawn |
| PATCH nodes endpoint | Wire Reddit OR Firecrawl | Test Core Idea confidence display |

**No merge expected.** Both tracks building.

---

### Day 4 — Research + SSE PR
| Track A | Track B | Lead |
|---------|---------|------|
| Journal GET endpoint | Real SSE feed | **Merge Track A PR #2** |
| **Open PR #2** | **Open PR #2** (research loop) | **Merge Track B PR #2** |
| Task queue CRUD start | 2 tools working | Agent Feed shows live SSE |

**Merge:** Track A PR #2, then Track B PR #2  
**Exit criteria:** Agent Feed shows real lines + critique scores.

---

### Day 5 — Canvas Live
| Track A | Track B | Lead |
|---------|---------|------|
| Vector KB index setup | Dialogue agent | Agent chips on nodes |
| Seed script start | Dead end logging | Confidence ring animations |
| | | Stage 2 node unlock animations |

**Exit criteria:** Two agent chips visible on two nodes.

---

### Day 6 — Vector KB + Pivot Prep
| Track A | Track B | Lead |
|---------|---------|------|
| Seed ≥ 20 chunks | Diff classifier | Source pills from API data |
| Vector search working | Pivot endpoint | Stage 3 unlock animations |
| **Open PR #3** | **Open PR #3** | NotificationBar stub |

---

### Day 7 — Pivot Demo
| Track A | Track B | Lead |
|---------|---------|------|
| build_events schema | Growth agent stub | **Merge Track B PR #3** |
| | | Pivot UI + node blur effect |
| | | Decision Journal overlay |
| | | **Merge Track A PR #3** |

**Merge:** Track B PR #3, Track A PR #3  
**Exit criteria:** Pivot blurs Audience + Competitors, Core Idea stays solid.

---

### Day 8 — GitHub Integration
| Track A | Track B | Lead |
|---------|---------|------|
| observe_events schema | Build Observer agent | GitHub OAuth flow |
| **Open PR #4** | GitHub polling logic | Build Node UI + progress bar |
| | **Open PR #4** | LeftRail green dot |

**Exit criteria:** GitHub connected → Build Node shows commit data.

---

### Day 9 — PostHog + Growth
| Track A | Track B | Lead |
|---------|---------|------|
| Index polish | Observe Agent + PostHog | PostHog connect UI |
| | Priority endpoint | Observe Node funnel display |
| | | Growth Node recommendations |
| | | Today's Priority wired |

**Merge:** Track B PR #4, Track A PR #4 if ready  
**Exit criteria:** "Conversion dropped 17% to 8%" visible in UI.

---

### Day 10 — Export + Demo
| Track A | Track B | Lead |
|---------|---------|------|
| Delete store.py | Export zip generation | Export modal + download |
| Final cleanup PR | **Open PR #5** | **Merge all remaining** |
| | | Run demo script end-to-end |
| | | Record 3-minute demo video |
| | | Final README update |

**Exit criteria:** Full demo script runnable. Export zip downloads. `main` clean.

---

## Integration Milestones

```
Day 2  ████░░░░░░  Atlas persistence live
Day 4  ██████░░░░  Research + SSE live
Day 7  ████████░░  Pivot demo works
Day 9  █████████░  Integrations live
Day 10 ██████████  Demo ready
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Track A delayed | Track B uses MemoryGraphStore (already planned) |
| Track B delayed | Lead keeps demo SSE fallback in frontend temporarily |
| Merge conflicts | Lead merges A before B always; see CONFLICT_ZONES.md |
| API key missing | Check `.env.example`; use mock tool responses for demo |
| Atlas quota | M0 free tier sufficient; monitor storage |

---

## Daily Sync Template

Copy-paste into Discord/Slack each day:

```
## CoFounder Daily Sync — Day X

**Track A:**
- Shipped:
- Today:
- Blockers:

**Track B:**
- Shipped:
- Today:
- Blockers:

**Lead:**
- Merged:
- Merging today:
- Blockers:

**Integration status:** [Day X milestone from chart above]
```

---

## End-of-Hackathon Checklist

- [ ] All 3 track acceptance criteria met
- [ ] Demo script runs in ≤ 3 minutes
- [ ] MongoDB 5+ use cases demonstrable
- [ ] GitHub repo README updated
- [ ] Demo video recorded
- [ ] Submission form filled (Google Cloud Rapid Agent Hackathon)
