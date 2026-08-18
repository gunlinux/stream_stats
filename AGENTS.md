# AGENTS.md

Instructional context for AI agents and contributors working in this repository.

## Project Overview

A FastAPI web-API template backed by PostgreSQL, using **asyncpg** for runtime queries and **Yoyo** for SQL migrations. Migrations apply automatically on startup. The messages API is protected by a static bearer token (`API_TOKEN`, required, non-empty — fail-closed); the health-check endpoint is intentionally unauthenticated.

The codebase follows a **clean-architecture** layout with the **repository pattern**: `interfaces → application → domain`, with `infrastructure` implementing the ports defined in `application`. Route handlers depend on application services, which depend on repository interfaces — never on asyncpg directly.

**Purpose:** reference/template project demonstrating a clean FastAPI + PostgreSQL + Yoyo-migrations layout, intended to be copied and extended.

## Tech Stack

| Concern        | Tool                                                            |
| -------------- | --------------------------------------------------------------- |
| Dependencies   | `uv` (`pyproject.toml` + `uv.lock`, `.python-version`)          |
| Web framework  | FastAPI (async endpoints, asyncpg DB)                           |
| ASGI server    | uvicorn                                                         |
| Database       | PostgreSQL 15 (local install; tests spin up an ephemeral instance via `pytest-postgresql`) |
| DB access      | **Raw SQL via `asyncpg`** (async connection pool) — no ORM     |
| Migrations     | **Yoyo** (`yoyo-migrations`) — plain `.sql` files (sync, psycopg2) |
| Config         | `pydantic-settings` (reads `.env`)                              |
| Models         | Pydantic v2 entities (`src/domain/entities.py`) + DTOs (`src/application/schemas.py`) |
| Auth           | Static bearer token (`API_TOKEN`) via `HTTPBearer` + constant-time `compare_digest` |
| Testing        | `pytest` + `httpx` `TestClient` (sync) + `pytest-postgresql` (ephemeral DB, no mocks) |
| Lint/format    | `ruff` (lint + format), `isort`, `flake8`, `mypy` (strict)      |

> ⚠️ `sqlalchemy` and `alembic` are **not** dependencies (removed). Runtime DB access is `asyncpg`; migrations are Yoyo on a synchronous `psycopg2` backend. Do not introduce the SQLAlchemy ORM or Alembic unless explicitly requested.

## Project Structure

```
├── src/
│   ├── main.py                       # App entrypoint, lifespan (DB wait + migrations), CORS, routers, error handlers
│   ├── domain/                       # Enterprise entities + domain errors (no external deps)
│   │   ├── entities.py               # Message, HealthCheck, Source enum
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
│       ├── dependencies.py           # Wires ports→adapters; bearer-auth `get_api_token`; `Depends` providers
│       └── routes/
│           ├── health.py             # GET /health (unauthenticated)
│           └── messages.py           # CRUD under /api/v1/messages (bearer-token protected)
├── test/                 # pytest (sync TestClient, ephemeral pytest-postgresql DB)
├── resources/
│   ├── migrations/       # Yoyo SQL migrations (001_…)
│   └── troubleshoot/     # scratch notes (yoyo_errors.txt)
├── README.md             # project readme (referenced by pyproject.toml)
├── pyproject.toml        # deps + tool config (pytest/isort/ruff/mypy); [tool.uv] package=false
├── uv.lock               # locked dependency versions (commit this)
├── .python-version       # pinned Python version (3.13)
├── env.example           # template for .env
├── Makefile
└── yoyo.ini              # Yoyo CLI config — DSN resolved from DATABASE_URL env var (no secrets)
```

## Building & Running

All commands assume the repo root as working directory. There is **no Docker** in this project: the app needs a reachable PostgreSQL 15 at `DATABASE_URL`, and the test suite provisions its own temporary instance.

### Local development

```bash
cp env.example .env                    # then edit as needed — API_TOKEN must be set (non-empty, fail-closed)
uv sync                                # install deps into .venv (dev group included)
# start PostgreSQL 15 locally, e.g. `brew services start postgresql@15`
uv run uvicorn src.main:app --reload   # app at http://localhost:8000
```

The app waits for the database, applies pending migrations, then serves:

- `GET /health` — health check (unauthenticated; status reflects DB connectivity)
- `GET/POST /api/v1/messages` — list (paginated) / create messages (bearer token required)
- `GET/DELETE /api/v1/messages/{id}` — fetch / delete a message (bearer token required)

### Makefile targets

```bash
make test                       # uv run pytest — spins up ephemeral PostgreSQL (needs pg_ctl on PATH)
make lint                       # uv run ruff check . && uv run flake8 src/ test/ && uv run mypy src/
make format                     # uv run isort + uv run ruff format on src/ and test/
make ruff-format                # uv run ruff format src/ test/
make clean                      # remove __pycache__, .pytest_cache, coverage artifacts
make migrate                    # apply migrations via db_manager
make create-migration NAME=<n>  # scaffold the next sequential NNN_<n>.sql migration
```

## Configuration

Environment variables (via `.env`, see `env.example`) are read by `src/infrastructure/config.py` (`pydantic-settings`):

- `DATABASE_URL` — default `postgresql://postgres:postgres@localhost:5432/postgres`
- `APP_NAME`, `ENVIRONMENT`, `DEBUG`
- `API_PREFIX` — default `/api/v1`
- `API_TOKEN` — static bearer token protecting the messages API. **No default: the app fails to start unless it is set to a non-empty value** (fail-closed; blank tokens are rejected at startup by a `model_validator`). Generate with e.g. `openssl rand -hex 32`.
- `CORS_ORIGINS` — comma-separated allowed origins. Credentials are enabled, so `*` is **not** valid — list the real browser origins (default `http://localhost:8000,http://127.0.0.1:8000`).

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

### Auth (bearer token)

- Protected routes are declared at the **router level**: `router = APIRouter(dependencies=[Depends(get_api_token)])` (see `src/interfaces/routes/messages.py`).
- `get_api_token` in `src/interfaces/dependencies.py` validates `Authorization: Bearer <token>` against `settings.api_token` with constant-time `compare_digest` and returns `401` + `WWW-Authenticate` otherwise. It is a guard-only dependency (returns `None`; its value is not consumed).
- `/health` is intentionally left unauthenticated for liveness probes.

### Adding routes

1. Create `src/interfaces/routes/<name>.py` with an `APIRouter`.
2. Have handlers depend on an application service via `Depends` (providers live in `src/interfaces/dependencies.py`).
3. Import the router in `src/main.py` and `app.include_router(...)`.
4. Add `dependencies=[Depends(get_api_token)]` at the router level if the new routes should be protected.
5. Raise domain errors from `src/domain/exceptions.py`; map them to HTTP responses via `app.exception_handler(...)` in `main.py` (not in the handlers).

### Adding models

- Add domain entities to `src/domain/entities.py`; add input DTOs to `src/application/schemas.py`.
- Create a matching migration for any new tables/columns.
- If new persistence is needed, add a port in `src/application/ports.py`, implement it in `src/infrastructure/repositories.py`, and wire it in `src/interfaces/dependencies.py`.

### Migrations (Yoyo)

- Migrations live in `resources/migrations/` as plain `.sql` files.
- **Existing convention:** sequential numeric prefixes — `001_…`, `002_…`, … Continue this ordering.
- The existing files carry a `-- __transactional__ = False` header comment (runs non-transactionally).
- `make create-migration NAME=<name>` scaffolds the next sequential `NNN_<name>.sql` file (auto-increments from existing migrations) with `-- Up migration` / `-- Down migration` sections.
- Rollback SQL is expected in a `-- Down migration` section (see README example), though current files contain only up-migrations.
- The messages table has a **unique index on `(source, message_id)`** so stream-ingestion retries are idempotent — preserve this property when extending the schema.

### Code style

- Formatting is done with **`ruff format`** (not black); `isort` uses `profile = "black"` with `known_first_party = ["src"]`. `ruff` (`[tool.ruff]`) and `flake8` (`.flake8`) are aligned to `line-length = 88`.
- `[tool.ruff.lint].ignore` lists the intentional known-issue rules (`BLE001`, `TRY002`).
- `flake8` targets `src/` and `test/` (with `per-file-ignores = test/conftest.py: E402` for the env-var-before-import pattern); `mypy` targets `src/` with strict settings (untyped defs disallowed).
- Run `make format` before committing; run `make lint` and `make test` to verify.

## Testing

- Tests live in `test/` (pytest config: `testpaths = ["test"]`, `--strict-markers --strict-config --verbose`).
- Uses **sync** `fastapi.testclient.TestClient` (not async), exposed via the `client` fixture in `conftest.py`.
- Every `TestClient` is used as a **context manager** so the app lifespan runs and the asyncpg pool is opened/closed per test — a bare TestClient leaks a 10-connection pool per event loop, which exhausts the ephemeral PostgreSQL's client limit mid-suite.
- `conftest.py` sets `API_TOKEN` in the environment **before** importing the app (settings are read at import time); the `client` fixture authenticates with `settings.api_token`, so tests pass regardless of any token already exported in the environment.
- Tests run against a **real, ephemeral PostgreSQL** provisioned by `pytest-postgresql` — no Docker, no mocks, no running server needed. It auto-locates `pg_ctl` (including Homebrew keg-only installs), so PostgreSQL must be installed locally. The `database_url` fixture creates the test database and applies migrations once; an autouse fixture truncates `messages` before each test so tests are order-independent.
- `test_health.py` requires no DB; `test_messages.py` covers auth (401 without/wrong token) and CRUD.

## Known Issues / Gotchas

These are intentional template simplifications or known gaps — do not silently "fix" them unless asked, but do flag them when relevant:

1. **Sync/async split:** runtime DB access is `asyncpg` (async), while migrations use Yoyo on a sync `psycopg2` backend. Do not use the asyncpg pool for migrations or the Yoyo backend for runtime queries.

## Environment & Secrets

- Copy `env.example` → `.env` for local overrides; `.env` is git-ignored.
- `API_TOKEN` protects the messages API and must be set to a non-empty value (fail-closed) — generate with `openssl rand -hex 32`; never commit real tokens.
- `yoyo.ini` resolves the DSN from the `DATABASE_URL` env var — it holds no secrets.
- Never commit real credentials. The default `postgres`/`postgres` DSN from `env.example` is the dev default.
