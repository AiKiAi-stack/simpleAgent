"""vLLM implementation of the LLM interface."""

from typing import Any, Dict, List, Optional
from openai import OpenAI

from .base import LLM, LLMResponse
from ..core.config import settings


class VLLMClient(LLM):
    """
    vLLM OpenAI-compatible API client.

    This implementation uses the OpenAI Python SDK to communicate with
    vLLM servers, which expose an OpenAI-compatible API.

    Example:
        llm = VLLMClient()
        response = await llm.chat_completion(
            messages=[{"role": "user", "content": "Hello!"}],
            tools=tool_schemas
        )
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """
        Initialize vLLM client.

        Args:
            base_url: vLLM server URL (default from settings)
            api_key: API key (default from settings)
            model_name: Model name to use (default from settings)
        """
        self.base_url = base_url or settings.vllm_base_url
        self.api_key = api_key or settings.vllm_api_key
        self.model_name = model_name or settings.model_name

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def get_model_name(self) -> str:
        """Return the model name."""
        return self.model_name

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Generate a chat completion via vLLM.

        Args:
            messages: List of chat messages
            tools: Optional list of tool schemas
            tool_choice: Tool choice strategy
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLMResponse with completion data
        """
        # Build request arguments
        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add tool-related arguments if tools provided
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        # Make API call
        response = self.client.chat.completions.create(**kwargs)

        # Extract response data
        choice = response.choices[0]
        message = choice.message

        return LLMResponse(
            content=message.content or "",
            tool_calls=self._extract_tool_calls(message),
            finish_reason=choice.finish_reason,
            usage=self._extract_usage(response.usage),
        )

    def _extract_tool_calls(self, message) -> List[Dict[str, Any]]:
        """Extract tool calls from message."""
        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )
        return tool_calls

    def _extract_usage(self, usage) -> Dict[str, int]:
        """Extract token usage from response."""
        if usage:
            return {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        return {}
