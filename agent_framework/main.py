"""Main entry point for the Qwen3 Agent Framework."""

import uvicorn
from .core.config import settings
from .api.app import create_app

# Create FastAPI app
app = create_app()


def main():
    """Start the FastAPI server."""
    print(f"🚀 Starting Qwen3 Agent API on {settings.api_host}:{settings.api_port}")
    print(f"📖 Docs: http://localhost:{settings.api_port}/docs")
    print(f"🏥 Health: http://localhost:{settings.api_port}/health")
    print(f"🤖 vLLM endpoint: {settings.vllm_base_url}")
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level="info")


if __name__ == "__main__":
    main()
