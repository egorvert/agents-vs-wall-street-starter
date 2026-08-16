# Architecture

## Goal

This monorepo is a minimal, production-shaped starting point for AI, data, and agent hackathons. It optimizes for a working local vertical slice and cheap replacement boundaries—not for speculative scale.

## Runtime flow

```text
Next.js UI
    │ typed HTTP contract
    ▼
FastAPI route
    │ validated Pydantic model
    ▼
Deterministic service
    │ Repository protocol
    ▼
SQLiteRepository ─── later: PostgresRepository
```

Agent orchestration is a separate backend concern:

```text
service or future agent route
    → coordinator
        → specialist agents
        → safe tools / external API wrappers
```

Agents do not access SQLite directly. Tools do not know about React. Routes do not contain domain decisions.

## API contracts

- `GET /health` returns `{ "status": "ok" }`.
- `POST /api/demo` accepts `{ "input": "hello" }` and returns a generated UUID, the original input, status, and UTC timestamp.

The demo path deliberately follows the requested unversioned contract for immediate hackathon use. When a project becomes a lasting product, introduce `/api/v1` before adding more public endpoints and keep compatibility deliberately.

Interactive API documentation is available at `/docs` while FastAPI is running.

## Persistence

SQLite uses Python's standard library and creates `apps/api/data/hackathon.db` on first startup. The database is ignored by Git. Services receive the small `Repository` protocol; a future Postgres or Supabase-backed adapter should implement that protocol and be selected in `repositories/dependencies.py`.

Startup schema creation is appropriate for this local starter. Before production deployment, add reviewed migrations for the selected production database.

## Agent layer

The OpenAI Agents SDK is installed, but agent objects are built lazily. Without `OPENAI_API_KEY`, normal API and frontend development still work and `run_coordinator` raises a clear, controlled error. The current researcher, forecaster, and critic are wiring examples rather than a finished workflow.

## Deliberate omissions

No authentication, Redis, Kafka, GraphQL, vector store, Docker, Kubernetes, or cloud deployment is included. Docker would add more setup than reproducibility for this two-process local stack; add it only when a sponsor SDK or system dependency genuinely needs it.
