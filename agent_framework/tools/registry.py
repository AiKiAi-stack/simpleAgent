"""Tool registry for managing tool registration and discovery."""

from typing import Dict, List, Optional, Type
from .base import Tool, ToolExecutionError


class ToolRegistry:
    """
    Central registry for all available tools.

    Provides tool registration, lookup, and schema management.

    Example:
        registry = ToolRegistry()
        registry.register(MyTool())
        tool = registry.get("my_tool")
        schemas = registry.get_all_schemas()
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> Optional[Tool]:
        """
        Unregister a tool by name.

        Args:
            name: Tool name to unregister

        Returns:
            The unregistered tool, or None if not found
        """
        return self._tools.pop(name, None)

    def get(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Tool name to look up

        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> Tool:
        """
        Get a tool by name, raising if not found.

        Args:
            name: Tool name to look up

        Returns:
            Tool instance

        Raises:
            KeyError: If tool is not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found. Available tools: {list(self._tools.keys())}")
        return self._tools[name]

    def list_all(self) -> List[Tool]:
        """
        List all registered tools.

        Returns:
            List of all tool instances
        """
        return list(self._tools.values())

    def list_names(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_all_schemas(self) -> List[Dict]:
        """
        Get OpenAI-compatible schemas for all registered tools.

        Returns:
            List of tool schemas
        """
        return [tool.to_schema() for tool in self._tools.values()]

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)


# Global registry instance for convenient access
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


def register_tool(tool: Tool) -> None:
    """Register a tool in the global registry."""
    _global_registry.register(tool)


def get_tool(name: str) -> Optional[Tool]:
    """Get a tool from the global registry."""
    return _global_registry.get(name)


def get_all_tools() -> List[Tool]:
    """Get all tools from the global registry."""
    return _global_registry.list_all()


def get_tool_schemas() -> List[Dict]:
    """Get schemas for all registered tools."""
    return _global_registry.get_all_schemas()
