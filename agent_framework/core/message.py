"""Message data structures for agent communication."""

from dataclasses import dataclass, field
from typing import Literal, Optional, Any, Dict
from datetime import datetime


@dataclass
class Message:
    """
    Message structure for agent communication.

    Attributes:
        role: Message role (system, user, assistant, tool)
        content: Message content
        tool_call_id: Optional tool call ID for tool responses
        tool_calls: Optional list of tool calls for assistant messages
        metadata: Optional metadata (timestamp, etc.)
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=lambda: {"timestamp": datetime.now().isoformat()})

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for API compatibility."""
        result = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result

    @classmethod
    def system(cls, content: str) -> "Message":
        """Create a system message."""
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        """Create a user message."""
        return cls(role="user", content=content)

    @classmethod
    def assistant(
        cls, content: str, tool_calls: Optional[list[Dict[str, Any]]] = None
    ) -> "Message":
        """Create an assistant message."""
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, content: str, tool_call_id: str) -> "Message":
        """Create a tool response message."""
        return cls(role="tool", content=content, tool_call_id=tool_call_id)


@dataclass
class ToolResult:
    """
    Result from tool execution.

    Attributes:
        success: Whether the tool execution was successful
        stdout: Standard output (for bash/python tools)
        stderr: Standard error (for bash/python tools)
        returncode: Return code (for bash tools)
        data: Optional structured data result
        error: Optional error message
        security_violation: Whether a security rule was violated
    """

    success: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    security_violation: bool = False

    def to_message(self, tool_call_id: str) -> Message:
        """Convert tool result to tool response message."""
        content = {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "error": self.error,
        }
        import json
        return Message.tool(
            content=json.dumps(content, ensure_ascii=False),
            tool_call_id=tool_call_id,
        )


@dataclass
class AgentResponse:
    """
    Response from agent execution.

    Attributes:
        response: Final assistant response
        logs: List of execution logs
        usage: Token usage statistics
        iterations: Number of iterations completed
        error: Optional error message
    """

    response: str
    logs: list[Dict[str, Any]]
    usage: Dict[str, Any]
    iterations: int
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response": self.response,
            "logs": self.logs,
            "usage": self.usage,
            "iterations": self.iterations,
            "error": self.error,
        }
