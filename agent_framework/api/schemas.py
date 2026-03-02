"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message to process")
    max_iterations: int = Field(
        default=10, ge=1, le=20, description="Max tool calling iterations (1-20)"
    )


class ToolFunctionSchema(BaseModel):
    """Tool function schema for API responses."""

    name: str
    arguments: Dict[str, Any]


class ToolCallSchema(BaseModel):
    """Tool call schema for API responses."""

    id: str
    type: str = "function"
    function: ToolFunctionSchema


class ToolResultSchema(BaseModel):
    """Tool result schema for API responses."""

    success: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None
    error: Optional[str] = None
    security_violation: bool = False
    data: Optional[Any] = None


class IterationLogSchema(BaseModel):
    """Log entry for a single iteration."""

    iteration: int
    reason: Optional[Dict[str, Any]] = None
    act: Optional[List[ToolResultSchema]] = None
    observe: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    id: str
    response: str
    logs: List[Dict[str, Any]]
    usage: Dict[str, Any]
    iterations: int
    processing_time: float
    error: Optional[str] = None


class ToolSchema(BaseModel):
    """Schema for tool information."""

    name: str
    description: str
    parameters: Dict[str, Any]


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    timestamp: float


class RootResponse(BaseModel):
    """Response model for root endpoint."""

    name: str
    version: str
    docs: str
    health: str
