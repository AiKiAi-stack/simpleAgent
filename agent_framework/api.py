from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .agent import Agent
from .config import settings
import uuid
import time


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message to process")
    max_iterations: int = Field(
        default=10, ge=1, le=20, description="Max tool calling iterations (1-20)"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    id: str
    response: str
    logs: List[Dict[str, Any]]
    usage: Dict[str, Any]
    iterations: int
    processing_time: float
    error: Optional[str] = None


app = FastAPI(
    title="Qwen3 Agent API",
    description="Agent framework with tool calling capabilities using vLLM and Qwen3",
    version="0.1.0",
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a user message with tool calling.

    The agent will:
    1. Analyze the request
    2. Call tools (bash/python) as needed
    3. Return final response with execution logs

    Args:
        request: Chat request with message and max iterations

    Returns:
        Chat response with result and logs
    """
    session_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        agent = Agent(max_iterations=request.max_iterations)
        result = agent.run(request.message)

        return ChatResponse(
            id=session_id,
            response=result["response"],
            logs=result["logs"],
            usage=result.get("usage", {}),
            iterations=result["iterations"],
            processing_time=time.time() - start_time,
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Qwen3 Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
