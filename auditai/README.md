# AuditAI Test Platform

Enterprise automated software testing platform with full testing pyramid coverage, embedded neural networks per engine, and AI-generated code fix proposals.

## Quick Start

```bash
cp .env.example .env
docker-compose up
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Default admin: `admin@auditai.local` / `changeme123`

## Architecture

```
auditai/
├── backend/          # FastAPI + Celery workers
│   ├── app/          # Core application (models, APIs, services)
│   └── engines/      # 10 test engines (each with neural model)
└── frontend/         # React 19 + Vite dashboard
```

## Testing Pyramid (10 Levels)

| Level | Engine | Neural Model |
|---|---|---|
| 1 | SAST + Taint | CodeBERT vulnerability classifier |
| 2 | Unit / Mutation | GNN mutation priority predictor |
| 3 | Property-Based + Fuzzing | VAE input generator + DQN coverage agent |
| 4 | Integration | Isolation Forest anomaly detector |
| 5 | Contract (OpenAPI/AsyncAPI) | Sentence-BERT semantic drift |
| 6 | Differential | Siamese equivalence network |
| 7 | End-to-End | (Playwright driver) |
| 8 | Performance / Load | LSTM degradation predictor |
| 9 | Security / Pentest | OWASP neural scorer |
| 10 | Chaos / Resilience | Causal inference fault ranking |

## Neural Fix Proposals

Every finding can generate an AI fix proposal via:
- Ollama (local llama3.2) for privacy-first deployments
- Claude API (claude-sonnet-4-6) for higher quality

## Release Gate

Each execution produces a GREEN / YELLOW / RED decision based on:
- Finding severity vs. policy thresholds
- Mutation score minimum
- Required engine coverage
- Pyramid level gaps

## Banking Domain Rules

Built-in rules for: balance preservation, idempotency, monetary rounding, transaction atomicity, PCI DSS compliance, concurrency safety.
