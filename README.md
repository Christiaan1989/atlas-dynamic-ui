# Atlas V2 — Auto Claims Triage Agent

Proof-of-concept agentic AI system for car insurance claims triage.

## Architecture

- **FastAPI + Postgres** — Mock insurance core system (policies, claims, audit trail)
- **LangGraph agent** (`atlas_v2`) — Collects FNOL, looks up policy, applies decision rules, writes back

## Quick Start

### 1. Start the backend (Postgres + API)

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs

### 2. Seed the database

```bash
cd backend
pip install -r requirements.txt
python seed.py
```

Or from Docker:
```bash
docker compose exec api python seed.py
```

### 3. Run the agent in LangGraph Studio

Open LangGraph Studio and point it at this directory. The `langgraph.json` is configured.

Make sure your `.env` has:
```
OPENAI_API_KEY=sk-...
INSURANCE_API_URL=http://localhost:8000
INSURANCE_API_KEY=demo-api-key-2025
```

## Demo Scenarios

| Scenario | Policy | Description | Expected Outcome |
|---|---|---|---|
| 1 — Accepted | `POL-ACTIVE-001` | "I was rear-ended at a stop light" | **accepted** (collision covered) |
| 2 — Denied (no coverage) | `POL-ACTIVE-002` | "I hit a pole; front damage" | **denied** (liability only, no collision) |
| 3 — Denied (lapsed) | `POL-LAPSED-001` | "My car was stolen overnight" | **denied** (policy lapsed) |
| 4 — Needs info | `POL-ACTIVE-004` | "Something happened to my car" | **needs_info** (vague, agent asks follow-up) |

## API Endpoints

All endpoints require `X-API-Key: demo-api-key-2025` header.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/policies/{policy_number}` | Policy + customer + coverages |
| POST | `/claims` | Create claim (FNOL) |
| GET | `/claims/{claim_id}` | Get claim + events |
| PATCH | `/claims/{claim_id}` | Update claim fields |
| POST | `/claims/{claim_id}/events` | Log audit event |
