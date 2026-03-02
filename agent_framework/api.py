from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .agent import Agent
from .config import settings
import uuid
import time
import json


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


def _serialize_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert logs to JSON-serializable format."""
    serialized = []
    for log in logs:
        clean_log = {}
        for key, value in log.items():
            if key == "response":
                # Handle LLM response dict
                clean_log[key] = {
                    "content": value.get("content"),
                    "tool_calls": (
                        [
                            {
                                "id": tc.id if hasattr(tc, "id") else tc.get("id"),
                                "function": {
                                    "name": tc.function.name
                                    if hasattr(tc, "function")
                                    else tc.get("function", {}).get("name"),
                                    "arguments": tc.function.arguments
                                    if hasattr(tc, "function")
                                    else tc.get("function", {}).get("arguments"),
                                }
                                if hasattr(tc, "function")
                                else tc.get("function"),
                            }
                            for tc in value.get("tool_calls", []) or []
                        ]
                        if value.get("tool_calls")
                        else None
                    ),
                    "finish_reason": value.get("finish_reason"),
                    "usage": value.get("usage", {}),
                }
            elif key == "tool_call":
                # Handle tool call dict
                clean_log[key] = {
                    "id": value.get("id"),
                    "name": value.get("name"),
                    "arguments": value.get("arguments"),
                }
            elif key == "result":
                # Handle tool result dict
                clean_log[key] = {
                    "success": value.get("success"),
                    "stdout": value.get("stdout"),
                    "stderr": value.get("stderr"),
                    "returncode": value.get("returncode"),
                    "error": value.get("error"),
                }
            else:
                clean_log[key] = value
        serialized.append(clean_log)
    return serialized


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

        # Serialize logs to ensure JSON compatibility
        serialized_logs = _serialize_logs(result["logs"])

        return ChatResponse(
            id=session_id,
            response=result["response"] or "",
            logs=serialized_logs,
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
