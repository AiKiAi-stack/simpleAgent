"""LLM module for language model abstraction."""

from .base import LLM
from .vllm_client import VLLMClient

__all__ = ["LLM", "VLLMClient"]
