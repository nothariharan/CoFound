# CoFounder Architecture

## Overview

CoFounder is a persistent AI Founder Operating System. The startup is represented as a living knowledge graph in MongoDB Atlas. A multi-agent system reads graph state, spawns specialist agents, and surfaces a single highest-ROI next action.

## System Flow

```
User Input → Orchestrator → Planner → Researcher(s) → MongoDB Graph
                ↓                              ↓
         Dialogue Agent                   SSE Feed → Frontend
                ↓
         Today's Priority
```

## Agent Roster

| Agent | Responsibility |
|-------|----------------|
| Orchestrator | Read graph, spawn agents, manage budget |
| Planner | Decompose idea into research tasks |
| Researcher (N) | Karpathy self-critique research loop |
| Dialogue Agent | Synthesize brief, ask one targeted question |
| Build Observer | Poll GitHub, update Build Node |
| Observe Agent | Query PostHog funnel, detect drops |
| Growth Agent | Generate ranked recommendations |
| Export Agent | Generate scaffold zip on approval |
| Diff Classifier | Surgical re-research on pivot |

## MongoDB Atlas Use Cases

1. Knowledge graph storage
2. Agent task queue
3. Vector search (product knowledge base)
4. Historical snapshot store
5. Dead end log
6. Build event store
7. Observe event store

## Tech Stack

- **Frontend:** Vite, React, TypeScript, Tailwind, React Flow, Zustand
- **Backend:** FastAPI, Python 3.11+
- **Database:** MongoDB Atlas
- **AI:** Gemini 2.5 Pro (orchestration), Gemini Flash (research)
- **Streaming:** Server-Sent Events
