# Hackathon Starter

A clean, reusable monorepo for AI, data, and agent hackathons. It gives you a polished Next.js dashboard, a typed FastAPI backend, SQLite persistence behind a replaceable repository boundary, and optional OpenAI Agents SDK scaffolding—without cloud infrastructure or authentication.

The starter includes one deliberately small vertical slice: submit text in the browser, call `POST /api/demo`, pass through a service, persist to SQLite, and render the typed response.

## Stack

- Next.js App Router, React, TypeScript, Tailwind CSS
- FastAPI, Pydantic, Python 3.11+
- OpenAI Agents SDK with coordinator/researcher/forecaster/critic placeholders
- SQLite through a small `Repository` protocol
- pytest, Vitest, Testing Library
- Ruff, Oxlint, Oxfmt, React Doctor, Lefthook

## Quick start

Prerequisites: Git, Node.js 22.13+, npm 11+, and Python 3.11+.

### 1. Clone

```bash
git clone https://github.com/RachelBurman/hackathon-starter.git
cd hackathon-starter
```

### 2. Install frontend dependencies

From the repository root:

```bash
npm install
```

This also installs the committed Git hooks.

### 3. Create and activate a Python virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install backend dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e "./apps/api[dev]"
```

### 5. Create local environment configuration

macOS/Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

`OPENAI_API_KEY` is optional. The health and demo routes work without it. Leave `DATABASE_URL` blank to use local SQLite.

### 6. Start FastAPI

In terminal one, with the virtual environment active:

```bash
npm run dev:api
```

### 7. Start Next.js

In terminal two:

```bash
npm run dev:web
```

Or run both processes together:

```bash
npm run dev
```

### 8. Run tests and checks

```bash
npm test
npm run lint
npm run format:check
npm run check
```

One-command setup scripts are also available: `./scripts/bootstrap.sh` on macOS/Linux or `.\scripts\bootstrap.ps1` in PowerShell.

## Local URLs

| Service              | URL                          |
| -------------------- | ---------------------------- |
| Web dashboard        | http://localhost:3000        |
| FastAPI              | http://localhost:8000        |
| Health check         | http://localhost:8000/health |
| Interactive API docs | http://localhost:8000/docs   |

## Repository structure

```text
hackathon-starter/
├── apps/
│   ├── web/                 # Next.js UI and browser API client
│   └── api/
│       ├── app/
│       │   ├── agents/      # Agents SDK orchestration
│       │   ├── config/      # Environment-backed settings
│       │   ├── models/      # Pydantic contracts and AI models
│       │   ├── repositories/# Persistence protocol and adapters
│       │   ├── routes/      # Thin HTTP layer
│       │   ├── services/    # Deterministic application logic
│       │   └── tools/       # Agent tools and external API wrappers
│       └── tests/
├── docs/
├── scripts/
├── .env.example
└── AGENTS.md
```

See [docs/architecture.md](docs/architecture.md) for the dependency boundaries and [docs/hackathon-checklist.md](docs/hackathon-checklist.md) when starting a new project.

## Common commands

| Command          | Purpose                                          |
| ---------------- | ------------------------------------------------ |
| `npm run dev`    | Run API and web app together                     |
| `npm test`       | Run Python and frontend tests                    |
| `npm run lint`   | Run Ruff, Oxlint, and TypeScript checks          |
| `npm run format` | Format Python and frontend/docs files            |
| `npm run check`  | Run all local quality gates and production build |

## Adding tomorrow's APIs and logic

1. Wrap a sponsor API in `apps/api/app/tools/` or a focused integration service.
2. Put deterministic decisions and transformations in `services/`.
3. Wire model orchestration and handoffs in `agents/`.
4. Add Pydantic contracts in `models/` and keep routes thin.
5. Extend the `Repository` protocol only when the application needs a new persistence operation.
6. Build and demo one complete browser-to-database path before adding another feature.

## Database replacement

The default adapter uses `apps/api/data/hackathon.db`, created automatically and never committed. To move to Postgres or Supabase later, implement `PostgresRepository` beside `SQLiteRepository`, select it in `repositories/dependencies.py`, and keep services unchanged. Production databases should use reviewed migrations; Supabase is intentionally not configured here.

## Agent behavior

The agent modules import and build SDK objects lazily. The application starts normally without an API key; calling `run_coordinator` without one raises a controlled `AgentUnavailableError`. Prompts and handoffs are intentionally minimal so you can replace them with the hackathon domain.

## License

MIT
