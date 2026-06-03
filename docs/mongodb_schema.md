# MongoDB Schema Reference

## Collections

| Collection | Purpose |
|------------|---------|
| `startup_graphs` | Master workspace document per startup |
| `nodes` | Individual node documents with full history |
| `task_queue` | Research task manifest for agents |
| `dead_ends` | Failed research queries (never retried) |
| `decision_journal` | Graph mutations with reason + evidence |
| `product_knowledge_base` | PM frameworks (Atlas Vector Search) |
| `agent_sessions` | Agent lifecycle and budget tracking |
| `build_events` | GitHub commit events and inferences |
| `observe_events` | PostHog funnel snapshots |

## Base Node Schema

```json
{
  "node_id": "uuid-v4",
  "type": "core_idea | audience | market_intelligence | ...",
  "confidence": 74,
  "status": "validated | needs_work | blocking | locked",
  "sources": ["reddit", "exa", "github"],
  "source_pills": [{ "label": "Reddit", "count": 847 }],
  "agent_notes": "...",
  "chat_history": [],
  "research_history": [],
  "last_updated": "ISO timestamp",
  "unlock_conditions": { "prerequisites": [], "threshold": 70 },
  "historical_snapshots": [],
  "active_agents": []
}
```

## Unlock Rules

| Node | Prerequisites | Threshold |
|------|---------------|-----------|
| Core Idea | None | — |
| Audience, Market, Competitors | Core Idea | 70% |
| Revenue, Product Vision | Audience + Market | 70% |
| Tech Stack | Competitors + Core Idea | 70% |
| Build | Revenue + Tech Stack | 70% |
| Launch | Build | auto on deploy |
| Observe | Launch | on PostHog connect |
| Growth | Observe | continuous |
