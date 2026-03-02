"""Tool base class and interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json


class Tool(ABC):
    """
    Abstract base class for all tools in the agent framework.

    Tools are callable functions that the agent can use to interact
    with the external world (bash, python, APIs, etc.).

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
        parameters: JSON Schema defining the tool's parameters
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool's unique identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return the tool's human-readable description."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Return the tool's parameter schema as JSON Schema."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool with provided arguments.

        Args:
            **kwargs: Tool-specific arguments matching the parameters schema

        Returns:
            Tool execution result (type depends on the tool)

        Raises:
            ToolExecutionError: If execution fails
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI-compatible tool schema.

        Returns:
            Dictionary suitable for passing to LLM APIs
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        self.tool_name = tool_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' execution failed: {message}")


class SyncTool(Tool):
    """
    Convenience base class for synchronous tools.

    Override _execute_sync() instead of execute().
    """

    async def execute(self, **kwargs) -> Any:
        """Wrap synchronous execute in async."""
        return self._execute_sync(**kwargs)

    @abstractmethod
    def _execute_sync(self, **kwargs) -> Any:
        """
        Execute the tool synchronously.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            Tool execution result
        """
        pass
