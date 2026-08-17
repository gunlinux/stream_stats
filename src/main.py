import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.exceptions import MessageNotFoundError
from src.infrastructure.config import settings
from src.infrastructure.database import db_manager
from src.interfaces.routes import health, messages

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting FastAPI application...")

    # Wait for database to be ready
    logger.info("Waiting for database...")
    await db_manager.wait_for_database()

    # Apply migrations (Yoyo uses a sync backend; run it in a thread)
    logger.info("Applying database migrations...")
    await asyncio.to_thread(db_manager.apply_migrations)

    logger.info("Application startup complete!")
    yield

    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await db_manager.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application with PostgreSQL and Yoyo migrations",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware — origins are configurable (CORS_ORIGINS env var,
# comma-separated). Credentials are enabled, so a wildcard is not allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Map domain errors to HTTP responses (handlers raise domain errors, not HTTP)
@app.exception_handler(MessageNotFoundError)
async def message_not_found_handler(
    request: Request, exc: MessageNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(messages.router, prefix=settings.api_prefix, tags=["messages"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
