from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .agent import Agent
from .config import settings
import uuid
import time
import logging

logger = logging.getLogger(__name__)


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
    iterations: int
    tool_calls: List[Dict[str, Any]]  # Detailed tool call information
    usage: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None
    system_prompt_used: bool = True  # Confirmation that system prompt was sent


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
    3. Return final response with complete execution details

    Args:
        request: Chat request with message and max iterations

    Returns:
        Chat response with:
        - response: Final answer
        - tool_calls: Complete list of all tool calls with arguments and results
        - iterations: Number of reasoning steps
        - execution details for verification
    """
    session_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        agent = Agent(max_iterations=request.max_iterations)
        result = agent.run(request.message)

        return ChatResponse(
            id=session_id,
            response=result["response"] or "",
            iterations=result["iterations"],
            tool_calls=result.get("tool_calls_summary", []),
            usage=result.get("usage", {}),
            processing_time=time.time() - start_time,
            error=result.get("error"),
            system_prompt_used=result.get("system_prompt_used", True),
        )

    except Exception as e:
        logger.exception("Error in chat endpoint")
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
