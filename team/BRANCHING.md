# Branching & PR Workflow

---

## Branch Structure

```
main                              ← Production-ready integration (Lead merges only)
├── feat/track-a-mongodb          ← Teammate A (long-lived)
├── feat/track-b-agents           ← Teammate B (long-lived)
└── feat/track-c-frontend         ← Lead (long-lived)
```

Optional short-lived branches for specific milestones:
```
feat/track-a-unlock-engine        ← branched from feat/track-a-mongodb
feat/track-b-research-loop        ← branched from feat/track-b-agents
```

---

## Rules

### For Everyone

1. **Never push directly to `main`** — always open a PR
2. **Rebase on `main` daily** before starting work:
   ```bash
   git checkout main
   git pull origin main
   git checkout feat/track-X-...
   git rebase main
   ```
3. **One logical milestone per PR** (~300 lines max preferred)
4. **PR title format:** `[Track X] Short description`
   - Example: `[Track A] Atlas persistence for workspace CRUD`
5. **PR description must include:**
   - Which acceptance criteria items are checked
   - Manual test steps or curl commands
   - Files touched list
   - Router snippet for Lead (if backend routes added)
   - Screenshots (if UI changes — Track C only)

### For Teammates A & B

6. Do not edit files in [CONFLICT_ZONES.md](./CONFLICT_ZONES.md)
7. If you need a schema change, open issue `contract-change` first
8. Tag Lead as reviewer on every PR
9. Mark PR as "Ready for review" only when acceptance criteria pass locally

### For Lead

10. Only Lead merges to `main`
11. Use [MERGE_CHECKLIST.md](./MERGE_CHECKLIST.md) before every merge
12. Prefer squash merge for milestone PRs
13. After merge, notify both teammates: "Rebase on main"

---

## PR Lifecycle

```
1. Teammate creates branch from main
2. Implements milestone against acceptance criteria
3. Opens PR → main, tags Lead
4. Lead pulls locally, runs checklist
5. Lead merges (or requests changes)
6. Both teammates rebase on updated main
7. Repeat
```

---

## Merge Order (Non-Negotiable)

| Sprint | Days | Merge first | Why |
|--------|------|-------------|-----|
| 1 | 1–2 | Track A | Atlas blocks real agent persistence |
| 2 | 3–4 | Track A #2, then Track B #1–2 | Task queue + SSE need graph |
| 3 | 5–7 | Track B #3, Track A #3 | Pivot + vector KB |
| 4 | 8–10 | All remaining | Parallel fixes, Lead integrates daily |

**If two PRs are ready:** Always merge Track A before Track B if both touch graph layer.

---

## Handling Merge Conflicts

### Likely conflict files

| File | Resolution |
|------|------------|
| `backend/main.py` | Lead resolves — combine router imports |
| `.env.example` | Merge both additions, deduplicate |
| `backend/graph/schema.py` | Track A version wins — others rebase |
| `frontend/src/types/index.ts` | Lead syncs from schema after Track A merge |

### Conflict resolution process

1. Lead pulls both branches locally
2. Merge Track A into `main` first
3. Ask Track B to rebase `feat/track-b-agents` on updated `main`
4. Track B resolves conflicts in their branch only
5. Lead merges Track B

**Never:** Both teammates resolving the same conflict file simultaneously.

---

## Commit Message Format

```
[Track X] Imperative summary (max 72 chars)

Optional body explaining why, not what.
Reference issue/PR if applicable.
```

Examples:
```
[Track A] Add Motor connection and Atlas workspace CRUD
[Track B] Implement Karpathy self-critique research loop
[Track C] Wire agent chips to active_agents on canvas nodes
```

---

## Emergency Hotfix

If `main` is broken after a merge:

1. Lead creates `hotfix/description` from `main`
2. Fix, PR, merge immediately
3. Notify teammates to rebase

Do not revert unless fix takes > 30 minutes.

---

## GitHub Setup (Recommended)

- Branch protection on `main`: require PR, no direct push
- Lead as required reviewer
- Delete branch after merge: **No** (keep long-lived feature branches)

---

## Quick Reference

```bash
# Start new day
git checkout main && git pull
git checkout feat/track-a-mongodb && git rebase main

# Push work
git add . && git commit -m "[Track A] Description"
git push origin feat/track-a-mongodb

# Open PR (GitHub CLI)
gh pr create --base main --title "[Track A] Description" --body "Acceptance criteria: ..."

# After Lead merges — update your branch
git checkout main && git pull
git checkout feat/track-a-mongodb && git rebase main
git push --force-with-lease origin feat/track-a-mongodb
```
