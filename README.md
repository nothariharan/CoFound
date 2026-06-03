# CoFounder

The Startup Founder Operating System — a persistent AI workspace that takes a startup from raw idea to validated, built, launched, and growing company.

**Hackathon:** Google Cloud Rapid Agent Hackathon · MongoDB Track  
**Stack:** Gemini 2.5 Pro · MongoDB Atlas · Google Cloud Agent Builder

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- MongoDB Atlas account (Day 1-2)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
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

Copy `.env.example` to `.env` and fill in credentials as integrations are wired up.

## Project Structure

```
cofounder/
├── backend/          # FastAPI + multi-agent system
├── frontend/         # Vite + React + React Flow canvas
├── scripts/          # Atlas seeding and index setup
├── cloud_run/        # Export zip generation (Day 10)
└── docs/             # Architecture and demo docs
```

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

MIT
