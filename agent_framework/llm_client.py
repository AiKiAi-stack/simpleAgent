from openai import OpenAI
from typing import List, Dict, Any, Optional
from .config import settings


class LLMClient:
    """vLLM OpenAI-compatible API client."""

    def __init__(self):
        """Initialize vLLM client with settings."""
        self.client = OpenAI(
            base_url=settings.vllm_base_url, api_key=settings.vllm_api_key
        )
        self.model = settings.model_name

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Send chat completion request to vLLM.

        Args:
            messages: List of chat messages with role and content
            tools: Optional list of tool schemas for function calling
            tool_choice: Tool choice strategy ("auto", "required", "none")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dictionary containing:
                - content: Assistant response content
                - tool_calls: List of tool calls (if any)
                - finish_reason: Why generation stopped
                - usage: Token usage statistics
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = self.client.chat.completions.create(**kwargs)

        return {
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls,
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            if response.usage
            else {},
        }
