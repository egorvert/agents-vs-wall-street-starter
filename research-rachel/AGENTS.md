# Coding agent guide

## Prime directive

Preserve working end-to-end functionality before adding sophistication.

This is a reusable hackathon starter. Hackathon speed, clarity, and simplicity take priority over premature abstraction. Keep new dependencies minimal and justify anything that adds setup or operational burden.

## Repository map

- `apps/web`: Next.js App Router frontend. UI components belong in `components/`; browser API clients and frontend-only utilities belong in `lib/`.
- `apps/api/app/routes`: thin FastAPI HTTP handlers and transport concerns.
- `apps/api/app/models`: Pydantic request, response, and structured AI models.
- `apps/api/app/services`: deterministic application and business logic.
- `apps/api/app/agents`: OpenAI Agents SDK orchestration, prompts, and handoffs.
- `apps/api/app/tools`: safe wrappers exposed to agents and adapters for external/sponsor APIs.
- `apps/api/app/repositories`: persistence protocols and database-specific adapters.
- `apps/api/tests` and colocated `*.test.tsx` files: backend and frontend tests.
- `docs`: architecture decisions and reusable hackathon workflow guidance.

## Architectural rules

1. The frontend depends only on documented HTTP contracts. It never imports backend modules or assumes database details.
2. Routes validate transport data, call services, and return typed responses. Put deterministic business logic in services, not routes or agents.
3. Agent modules orchestrate models, tools, and handoffs. They must not contain SQL, direct persistence logic, or frontend concerns.
4. External APIs belong behind focused functions in `tools/` or clients in `services/`. Keep credentials in environment variables and make failure behavior explicit.
5. Access persistence only through the `Repository` protocol. Add `PostgresRepository` beside the SQLite adapter and select it centrally; do not leak adapter details into services.
6. Keep API request and response models explicit. Prefer structured outputs for AI behavior that downstream code consumes.
7. Every meaningful change should retain or extend one working route-to-database and browser-to-route path.

## Conventions

- Python: type hints, Pydantic at boundaries, Ruff formatting/linting, pytest tests.
- TypeScript: strict mode, accessible semantic HTML, one reusable React component per file, OXC formatting/linting, Vitest tests.
- Prefer small modules and plain functions/classes. Introduce an abstraction only when it protects a real replacement boundary or removes demonstrated repetition.
- Do not add authentication, queues, caches, containers, cloud resources, or additional databases unless the project actually requires them.
- Update `.env.example`, README commands, contracts, and tests when setup or behavior changes.

## Before handing off

Run `npm run check` from the repository root. Never commit secrets, local databases, generated build output, `node_modules`, or virtual environments.
