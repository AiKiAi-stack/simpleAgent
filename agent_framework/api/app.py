"""FastAPI application factory."""

from fastapi import FastAPI
from .routes import router
from ..core.config import settings


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Qwen3 Agent API",
        description="Agent framework with tool calling capabilities using vLLM and Qwen3",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Include routers
    app.include_router(router, prefix="/api/v1")

    # Also include at root for backward compatibility
    app.include_router(router, tags=["default"])

    @app.on_event("startup")
    async def startup_event():
        """Called on application startup."""
        print(f"Starting Qwen3 Agent API on {settings.api_host}:{settings.api_port}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Called on application shutdown."""
        print("Shutting down Qwen3 Agent API")

    return app
