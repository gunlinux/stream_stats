.PHONY: help test lint format ruff-format clean migrate create-migration

# Default target
help:
	@echo "FastAPI PostgreSQL Project - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  test            Run tests"
	@echo "  lint            Run linting checks (ruff + flake8 + mypy)"
	@echo "  format          Format code with ruff and isort"
	@echo "  ruff-format     Format with ruff (ruff format)"
	@echo "  clean           Clean up Python cache files"
	@echo ""
	@echo "Database:"
	@echo "  migrate         Apply database migrations"
	@echo "  create-migration Scaffold a migration (make create-migration NAME=...)"
	@echo ""
	@echo "Utility:"
	@echo "  help            Show this help message"

# Development commands
test:
	uv run pytest

lint:
	uv run ruff check .
	uv run flake8 src/ test/
	uv run mypy src/

format:
	uv run isort src/ test/
	uv run ruff format src/ test/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Database commands
migrate:
	uv run python -c "from src.infrastructure.database import db_manager; db_manager.apply_migrations()"

create-migration:
	@if [ -z "$(NAME)" ]; then echo "Usage: make create-migration NAME=<migration_name>"; exit 1; fi
	@next=$$(ls resources/migrations/*.sql 2>/dev/null | sed -nE 's|.*/([0-9]{3})_.*|\1|p' | sort -n | tail -1); \
	next=$$(printf '%03d' $$((10#$${next:-0} + 1))); \
	title=$$(echo "$(NAME)" | tr '_' ' '); \
	file="resources/migrations/$${next}_$(NAME).sql"; \
	printf '%s\n' "-- $$title" "-- Migration: $${next}_$(NAME).sql" "-- __transactional__ = False" "" "-- Up migration" "-- Add your SQL here" "" "-- Down migration" "-- Add rollback SQL here" > "$$file"; \
	echo "Created $$file"


