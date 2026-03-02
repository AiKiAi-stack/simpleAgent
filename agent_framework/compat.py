"""Backward compatibility imports for legacy code."""

# Re-export from new locations for backward compatibility
from .core.config import Settings, settings
from .core.message import Message, AgentResponse, ToolResult
from .core.agent import ReActAgent

# Old module references (deprecated - use new locations)
# from . import agent  # Use: from .core import agent
# from . import api  # Use: from . import api
# from . import prompts  # Use: from . import prompts
# from . import llm_client  # Use: from .llm import vllm_client

__all__ = [
    "Settings",
    "settings",
    "Message",
    "AgentResponse",
    "ToolResult",
    "ReActAgent",
]
