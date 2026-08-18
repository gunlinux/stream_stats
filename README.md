# FastAPI + PostgreSQL Template

A clean-architecture FastAPI web-API template backed by PostgreSQL, using
**asyncpg** for runtime queries and **Yoyo** for SQL migrations. Migrations
apply automatically on startup.

## Tech Stack

| Concern      | Tool                                                    |
| ------------ | ------------------------------------------------------- |
| Dependencies | `uv` (`pyproject.toml` + `uv.lock`, `.python-version`)  |
| Web framework| FastAPI (async endpoints, asyncpg DB)                   |
| ASGI server  | uvicorn                                                 |
| Database     | PostgreSQL 15                                           |
| DB access    | Raw SQL via `asyncpg` (async connection pool) — no ORM  |
| Migrations   | Yoyo — plain `.sql` files (sync, psycopg2)              |
| Config       | `pydantic-settings` (reads `.env`)                      |
| Testing      | `pytest` + `httpx` `TestClient` (sync) + `pytest-postgresql` (ephemeral DB, no mocks) |

## Layout

```
src/
├── main.py                       # App entrypoint, lifespan, routers, error handlers
├── domain/                       # Entities + domain errors (no external deps)
├── application/                  # Use cases + ports (interfaces)
├── infrastructure/               # Adapters: config, database, repositories
└── interfaces/                   # FastAPI routers + composition root
test/                             # pytest (sync TestClient, ephemeral pytest-postgresql DB)
resources/migrations/             # Yoyo SQL migrations
```

Dependencies point inward: `interfaces → application → domain`, with
`infrastructure` implementing the ports defined in `application`.

## Getting Started

```bash
cp env.example .env               # edit as needed — API_TOKEN must be set (non-empty, fail-closed)
uv sync                           # install deps into .venv
# start PostgreSQL 15 locally, e.g. `brew services start postgresql@15`
uv run uvicorn src.main:app --reload
```

The app waits for the database, applies pending migrations, and serves:

- `GET /health` — health check (status reflects DB connectivity)
- `GET/POST /api/v1/messages` — list (paginated) / create messages (bearer token required)
- `GET/DELETE /api/v1/messages/{id}` — fetch / delete a message (bearer token required)

## Configuration

Environment variables (see `env.example`) are read by
`src/infrastructure/config.py`:

- `DATABASE_URL` — default `postgresql://postgres:postgres@localhost:5432/postgres`
- `APP_NAME`, `ENVIRONMENT`, `DEBUG`
- `API_PREFIX` — default `/api/v1`
- `API_TOKEN` — static bearer token protecting the messages API. Required and
  must be non-empty — the app fails to start otherwise. Generate with
  `openssl rand -hex 32`.
- `CORS_ORIGINS` — comma-separated allowed origins (credentials are enabled,
  so a wildcard is not valid)

## Development

```bash
make test            # uv run pytest (ephemeral PostgreSQL via pytest-postgresql)
make lint            # ruff + flake8 + mypy
make format          # isort + ruff format
make create-migration NAME=<name>   # scaffold the next NNN_<name>.sql migration
```

The test suite provisions its own ephemeral PostgreSQL instance via
`pytest-postgresql`, so PostgreSQL must be installed locally (`pg_ctl` on
PATH — Homebrew keg-only installs are auto-detected).

## Migrations

Migrations live in `resources/migrations/` as plain `.sql` files with
sequential `NNN_` prefixes and a `-- __transactional__ = False` header. They
run automatically on app startup; the `yoyo` CLI reads the DSN from the
`DATABASE_URL` env var (`yoyo.ini` holds no secrets).
