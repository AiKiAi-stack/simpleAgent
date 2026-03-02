"""LLM base interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMResponse:
    """Response from an LLM completion request."""

    def __init__(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        finish_reason: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.finish_reason = finish_reason
        self.usage = usage or {}

    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0

    def __repr__(self) -> str:
        return f"LLMResponse(content={self.content[:50]!r}..., tool_calls={len(self.tool_calls)})"


class LLM(ABC):
    """
    Abstract base interface for Language Model providers.

    This abstraction allows switching between different LLM backends
    (vLLM, OpenAI, Anthropic, etc.) without changing agent code.

    Example:
        class MyLLM(LLM):
            async def chat_completion(self, messages, tools=None):
                # Implementation here
                pass
    """

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Generate a chat completion.

        Args:
            messages: List of chat messages with role and content
            tools: Optional list of tool schemas for function calling
            tool_choice: Tool choice strategy ("auto", "required", "none")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 2.0)

        Returns:
            LLMResponse with content, tool calls, and metadata
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass
