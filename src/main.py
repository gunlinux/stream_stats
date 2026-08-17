import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config import settings
from src.infrastructure.database import db_manager
from src.interfaces.routes import health, messages


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    print("Starting FastAPI application...")

    # Wait for database to be ready
    print("Waiting for database...")
    await db_manager.wait_for_database()

    # Apply migrations (Yoyo uses a sync backend; run it in a thread)
    print("Applying database migrations...")
    await asyncio.to_thread(db_manager.apply_migrations)

    print("Application startup complete!")
    yield

    # Shutdown
    print("Shutting down FastAPI application...")
    await db_manager.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A FastAPI application with PostgreSQL and Yoyo migrations",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
