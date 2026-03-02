"""API routes for chat and health endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
import time

from .schemas import ChatRequest, ChatResponse, HealthResponse, RootResponse
from ..core.agent import ReActAgent
from ..core.message import AgentResponse
from ..core.config import settings


router = APIRouter()

# Global agent instance (initialized on first request)
_agent: ReActAgent | None = None


def get_agent() -> ReActAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        # Initialize agent with default tools
        from ..tools.builtin import BashTool, PythonTool
        from ..llm.vllm_client import VLLMClient
        from ..prompts.system import get_system_message

        llm = VLLMClient()
        tools = [BashTool(), PythonTool()]
        system_message = get_system_message(
            include_security_rules=True,
            include_tools=True,
            tools=[
                {"name": "execute_bash", "description": "Execute bash commands"},
                {"name": "execute_python", "description": "Execute Python code"},
            ],
        )

        _agent = ReActAgent(
            llm=llm,
            tools=tools,
            system_prompt=system_message["content"],
            max_iterations=settings.max_iterations,
        )
    return _agent


@router.post("/chat", response_model=ChatResponse)
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
        agent = get_agent()
        result = await agent.run(request.message)

        return ChatResponse(
            id=session_id,
            response=result.response,
            logs=result.logs,
            usage=result.usage,
            iterations=result.iterations,
            processing_time=time.time() - start_time,
            error=result.error,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", timestamp=time.time())


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """Root endpoint with API info."""
    return RootResponse(
        name="Qwen3 Agent API",
        version="0.1.0",
        docs="/docs",
        health="/health",
    )
