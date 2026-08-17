# AGENTS.md

Instructional context for AI agents and contributors working in this repository.

## Project Overview

A FastAPI web-API template backed by PostgreSQL, using **Yoyo** for SQL migrations. The app applies migrations automatically on startup and exposes a versioned messages API plus health-check endpoints.

The codebase follows a **clean-architecture** layout with the **repository pattern**: `interfaces → application → domain`, with `infrastructure` implementing the ports defined in `application`. Route handlers depend on application services, which depend on repository interfaces — never on asyncpg directly.

**Purpose:** reference/template project demonstrating a clean FastAPI + PostgreSQL + Yoyo-migrations layout, intended to be copied and extended.

## Tech Stack

| Concern        | Tool                                                            |
| -------------- | --------------------------------------------------------------- |
| Dependencies   | `uv` (`pyproject.toml` + `uv.lock`, `.python-version`)          |
| Web framework  | FastAPI (async endpoints, asyncpg DB)                           |
| ASGI server    | uvicorn                                                         |
| Database       | PostgreSQL 15 (Docker Compose)                                  |
| DB access      | **Raw SQL via `asyncpg`** (async connection pool) — no ORM     |
| Migrations     | **Yoyo** (`yoyo-migrations`) — plain `.sql` files (sync, psycopg2) |
| Config         | `pydantic-settings` (reads `.env`)                              |
| Models         | Pydantic v2 entities (`src/domain/entities.py`) + DTOs (`src/application/schemas.py`) |
| Testing        | `pytest` + `httpx` `TestClient` (sync)                          |
| Lint/format    | `black`, `isort`, `flake8`, `mypy` (strict)                     |

> ⚠️ `sqlalchemy` and `alembic` are **not** dependencies (removed). Runtime DB access is `asyncpg`; migrations are Yoyo on a synchronous `psycopg2` backend. Do not introduce the SQLAlchemy ORM or Alembic unless explicitly requested.

## Project Structure

```
├── src/
│   ├── main.py                       # App entrypoint, lifespan (DB wait + migrations), routers, error handlers
│   ├── domain/                       # Enterprise entities + domain errors (no external deps)
│   │   ├── entities.py               # Message, HealthCheck
│   │   └── exceptions.py             # MessageNotFoundError
│   ├── application/                  # Use cases + ports (interfaces)
│   │   ├── ports.py                  # MessageRepository, HealthRepository protocols
│   │   ├── schemas.py                # MessageCreate input DTO
│   │   └── services.py               # MessageService, HealthService (use cases)
│   ├── infrastructure/               # Adapters implementing application ports
│   │   ├── config.py                 # pydantic-settings `Settings`, global `settings`
│   │   ├── database.py               # `DatabaseManager` / global `db_manager` (asyncpg + Yoyo)
│   │   └── repositories.py           # PostgresMessageRepository, PostgresHealthRepository
│   └── interfaces/                   # Delivery layer: FastAPI routers + composition root
│       ├── dependencies.py           # Wires ports→adapters; `Depends` providers
│       └── routes/
│           ├── health.py             # GET /health
│           └── messages.py           # CRUD under /api/v1/messages
├── test/                 # pytest (sync TestClient, real DB)
├── resources/
│   ├── migrations/       # Yoyo SQL migrations (001_…)
│   └── troubleshoot/     # scratch notes (yoyo_errors.txt)
├── docker/Dockerfile
├── docker-compose.yml
├── pyproject.toml        # deps + tool config (pytest/black/isort/mypy); [tool.uv] package=false
├── uv.lock               # locked dependency versions (commit this)
├── .python-version       # pinned Python version (3.13)
├── env.example           # template for .env
├── Makefile
└── yoyo.ini              # Yoyo CLI config (local DB)
```

## Building & Running

All commands assume the repo root as working directory.

### Docker Compose (recommended)

```bash
docker-compose up --build      # PostgreSQL + app; migrations auto-apply
docker-compose down            # stop
docker-compose down -v         # stop and wipe DB volume
docker-compose logs -f         # follow logs
```

### Local development

```bash
uv sync                                  # install deps into .venv (dev group included)
cp env.example .env                      # then edit as needed
docker-compose up postgres -d            # DB only
uv run uvicorn src.main:app --reload     # app at http://localhost:8000
```

### Makefile targets

```bash
make lock                       # uv lock (refresh uv.lock after dependency changes)
make sync                       # uv sync (install deps)
make test                       # uv run pytest
make test-docker                # uv run pytest inside the app container
make test-coverage              # uv run pytest --cov=src
make test-coverage-docker       # uv run pytest --cov=src inside the app container
make lint                       # uv run flake8 src/ test/  &&  uv run mypy src/
make format                     # uv run black + isort on src/ and test/
make migrate                    # apply migrations via db_manager
make migrate-docker             # apply migrations via db_manager inside the app container
make create-migration NAME=<n>  # scaffold the next sequential NNN_<n>.sql migration
make docker-up / docker-down / docker-logs
make start-detached             # docker-compose up --build -d
make prod-build                 # docker build -f docker/Dockerfile -t fastapi-app .
```

## Configuration

Environment variables (via `.env`, see `env.example`) are read by `src/infrastructure/config.py` (`pydantic-settings`):

- `DATABASE_URL` — default `postgresql://postgres:postgres@localhost:5432/postgres`
- `APP_NAME`, `ENVIRONMENT`, `DEBUG`
- `API_PREFIX` — default `/api/v1`

Access them through the global `settings` instance: `from src.infrastructure.config import settings`.

## Development Conventions

### Database access — always raw SQL through `db_manager`

Raw SQL lives **only** in `src/infrastructure/repositories.py`. Application services and route handlers talk to repository interfaces (`src/application/ports.py`), never to asyncpg.

```python
from src.infrastructure.database import db_manager

async with db_manager.get_connection() as conn:   # asyncpg connection
    rows = await conn.fetch("SELECT * FROM messages")   # list[asyncpg.Record]
```

- Use **`$1`, `$2`, …** placeholders (asyncpg style), never f-string interpolation of values.
- `get_connection()` yields an `asyncpg.Connection`; `fetch()` returns a list of `Record`s, `fetchrow()` a single `Record | None`, `fetchval()` a scalar. `Record` supports `**` unpacking (e.g. `Message(**row)`).
- Migrations are applied by `db_manager.apply_migrations()` (sync Yoyo, run via `asyncio.to_thread`) inside the app `lifespan` in `main.py`, so **new migrations run automatically on startup**.

### Dependency rule

Dependencies point inward. `domain` imports nothing from other layers; `application` may import `domain`; `infrastructure` imports `application` (ports) and `domain`; `interfaces` imports `application` + `domain`. `main.py` and `interfaces/dependencies.py` are the composition root where ports are wired to adapters.

### Adding routes

1. Create `src/interfaces/routes/<name>.py` with an `APIRouter`.
2. Have handlers depend on an application service via `Depends` (providers live in `src/interfaces/dependencies.py`).
3. Import the router in `src/main.py` and `app.include_router(...)`.
4. Raise domain errors from `src/domain/exceptions.py`; map them to HTTP responses via `app.exception_handler(...)` in `main.py` (not in the handlers).

### Adding models

- Add domain entities to `src/domain/entities.py`; add input DTOs to `src/application/schemas.py`.
- Create a matching migration for any new tables/columns.
- If new persistence is needed, add a port in `src/application/ports.py`, implement it in `src/infrastructure/repositories.py`, and wire it in `src/interfaces/dependencies.py`.

### Migrations (Yoyo)

- Migrations live in `resources/migrations/` as plain `.sql` files.
- **Existing convention:** sequential numeric prefixes — `001_…`, `002_…`. Continue this ordering.
- The existing files carry a `-- __transactional__ = False` header comment (runs non-transactionally).
- `make create-migration NAME=<name>` scaffolds the next sequential `NNN_<name>.sql` file (auto-increments from existing migrations).
- Rollback SQL is expected in a `-- Down migration` section (see README example), though current files contain only up-migrations.

### Code style

- `black` line-length **88**, `isort` with `profile = "black"`, `known_first_party = ["src"]`.
- `ruff` (`[tool.ruff]` in `pyproject.toml`) and `flake8` (`.flake8`) are aligned to `line-length = 88`. `[tool.ruff.lint].ignore` lists the intentional known-issue rules (`BLE001`, `TRY002`).
- `flake8` targets `src/` and `test/`; `mypy` targets `src/` with strict settings (untyped defs disallowed).
- Run `make format` before committing; run `make lint` and `make test` to verify.

## Testing

- Tests live in `test/` (pytest config: `testpaths = ["test"]`, `--strict-markers --strict-config --verbose`).
- Uses **sync** `fastapi.testclient.TestClient` (not async), exposed via the `client` fixture in `conftest.py`.
- Tests hit a **real database** — no mocks. A running PostgreSQL with migrations applied is required (`docker-compose up postgres -d`). `test_messages.py` creates/deletes actual rows.
- `test_health.py` requires no DB; `test_messages.py` requires DB + applied migrations.

## Known Issues / Gotchas

These are intentional template simplifications or known gaps — do not silently "fix" them unless asked, but do flag them when relevant:

1. **CORS is wide open.** `main.py` sets `allow_origins=["*"]` with `allow_credentials=True` (invalid/insecure combination for credentialed requests). Harden for production.
2. **Sync/async split:** runtime DB access is `asyncpg` (async), while migrations use Yoyo on a sync `psycopg2` backend. Do not use the asyncpg pool for migrations or the Yoyo backend for runtime queries.

## Environment & Secrets

- Copy `env.example` → `.env` for local overrides; `.env` is git-ignored.
- Docker Compose sets `DATABASE_URL` pointing at the `postgres` service (`postgresql://postgres:postgres@postgres:5432/postgres`) with `ENVIRONMENT=production`.
- Never commit real credentials. The defaults `postgres`/`postgres` are the actual dev credentials from `env.example`/`docker-compose.yml`.
