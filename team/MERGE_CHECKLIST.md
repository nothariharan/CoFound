# Merge Checklist (Lead Only)

Use this checklist before every merge to `main`. Do not skip steps.

---

## Pre-Merge

- [ ] PR title follows format: `[Track X] Description`
- [ ] PR description includes acceptance criteria checkboxes
- [ ] PR description includes manual test steps
- [ ] Correct track owner opened the PR
- [ ] No files outside track scope edited (see [CONFLICT_ZONES.md](./CONFLICT_ZONES.md))

---

## Pull & Run Locally

```bash
git fetch origin
git checkout feat/track-X-...
git rebase origin/main
```

- [ ] Backend starts: `cd backend && uvicorn main:app --reload --port 8000`
- [ ] Frontend starts: `cd frontend && npm run dev`
- [ ] No import errors in backend logs
- [ ] No console errors in browser on intake screen

---

## Track-Specific Acceptance

### Track A PR
- [ ] `POST /api/workspace` → data persists after server restart
- [ ] `GET /api/workspace/{id}` returns valid node schema
- [ ] `PATCH /api/nodes/{id}` works (if included in PR)
- [ ] Decision journal entry created on mutation (if included)
- [ ] Unlock rules applied correctly (if included)
- [ ] Scripts run without error (if included)
- [ ] No changes to `frontend/` or `backend/agents/`

### Track B PR
- [ ] `POST /api/agents/spawn` starts session (if included)
- [ ] SSE feed shows real agent events (not demo placeholders)
- [ ] Critique format correct: `[Critique: N/100]`
- [ ] Uses GraphStore protocol (not direct store.py import)
- [ ] No API keys in diff
- [ ] No changes to `frontend/` or `schema.py`

### Track C PR
- [ ] `npm run build` passes
- [ ] Intake → dashboard flow works
- [ ] UI follows design rules (no gradients, no emojis)
- [ ] Integrations work (if included in PR)

---

## Conflict Zone Check

- [ ] `backend/graph/schema.py` — only Track A changes, or no changes
- [ ] `frontend/src/types/index.ts` — synced if schema changed
- [ ] `backend/main.py` — router imports added correctly
- [ ] `.env.example` — new vars documented, no secrets

---

## Integration Smoke Test

After merging locally (before push):

- [ ] Create workspace via UI or curl
- [ ] Core Idea node visible on canvas
- [ ] Agent Feed connects (SSE green dot)
- [ ] No 500 errors in backend logs during basic flow

---

## Merge

- [ ] Squash merge preferred for milestone PRs
- [ ] Merge commit message matches PR title
- [ ] Delete branch: **No** (keep long-lived feature branches)

---

## Post-Merge

- [ ] Pull `main` locally: `git checkout main && git pull`
- [ ] Notify Teammate A: "Merged [PR title]. Please rebase."
- [ ] Notify Teammate B: "Merged [PR title]. Please rebase."
- [ ] Update your own `feat/track-c-frontend` branch: `git rebase main`
- [ ] Verify deployed/running `main` still works

---

## Merge Log (Fill In)

| Date | PR | Track | Merged by | Notes |
|------|-----|-------|-----------|-------|
| | | | | |
| | | | | |
| | | | | |

---

## Reject PR If

- Acceptance criteria not met
- Edits files outside track scope without approval
- API keys or secrets in diff
- Breaks existing intake → dashboard flow on `main`
- Schema change without `contract-change` issue approval
- No manual test evidence in PR description

**When rejecting:** Comment specific failing criteria. Teammate fixes and re-requests review.
