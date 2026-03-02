"""MCP Adapter for wrapping MCP servers as Tools."""

from typing import Any, Dict, List, Optional
import asyncio

from ..tools.base import Tool, ToolExecutionError
from .client import MCPClient


class MCPAdapter(Tool):
    """
    Adapter that wraps an MCP server as a Tool.

    This allows MCP servers to be used interchangeably with native tools.
    Each MCP tool exposed by the server becomes callable through this adapter.

    Example:
        client = MCPClient("search-server")
        await client.connect()

        adapter = MCPAdapter(
            server_name="search",
            tool_name="web_search",
            client=client
        )
        result = await adapter.execute(query="python tutorials")
    """

    def __init__(
        self,
        server_name: str,
        tool_name: str,
        client: MCPClient,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize MCP adapter.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool exposed by the server
            client: MCP client instance
            description: Optional tool description (auto-fetched if not provided)
            parameters: Optional parameter schema (auto-fetched if not provided)
        """
        self.server_name = server_name
        self.tool_name = tool_name
        self.client = client
        self._description = description
        self._parameters = parameters

    @property
    def name(self) -> str:
        return f"{self.server_name}_{self.tool_name}"

    @property
    def description(self) -> str:
        if self._description:
            return self._description
        return f"Tool '{self.tool_name}' from MCP server '{self.server_name}'"

    @property
    def parameters(self) -> Dict[str, Any]:
        if self._parameters:
            return self._parameters
        # Default open parameters if not specified
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }

    async def execute(self, **kwargs) -> Any:
        """
        Execute the MCP tool.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ToolExecutionError: If execution fails
            ConnectionError: If not connected to server
        """
        try:
            result = await self.client.call_tool(self.tool_name, kwargs)
            return result
        except Exception as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=f"Failed to execute MCP tool: {str(e)}",
                original_error=e,
            )


class MCPServerAdapter:
    """
    Adapter that wraps an entire MCP server as multiple Tools.

    This automatically discovers all tools exposed by an MCP server
    and creates Tool adapters for each one.

    Example:
        client = MCPClient("search-server")
        await client.connect()

        server_adapter = MCPServerAdapter("search", client)
        tools = server_adapter.get_tools()  # List[Tool]

        for tool in tools:
            print(f"Available: {tool.name}")
    """

    def __init__(self, server_name: str, client: MCPClient):
        """
        Initialize MCP server adapter.

        Args:
            server_name: Name of the MCP server
            client: MCP client instance
        """
        self.server_name = server_name
        self.client = client
        self._tools: Dict[str, MCPAdapter] = {}

    async def discover_tools(self) -> List[MCPAdapter]:
        """
        Discover and wrap all tools from the MCP server.

        Returns:
            List of MCPAdapter instances
        """
        tool_defs = await self.client.list_tools()
        adapters = []

        for tool_def in tool_defs:
            adapter = MCPAdapter(
                server_name=self.server_name,
                tool_name=tool_def["name"],
                client=self.client,
                description=tool_def.get("description"),
                parameters=tool_def.get("inputSchema", {}),
            )
            self._tools[adapter.name] = adapter
            adapters.append(adapter)

        return adapters

    def get_tool(self, name: str) -> Optional[MCPAdapter]:
        """Get a specific tool by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[MCPAdapter]:
        """Get all discovered tools."""
        return list(self._tools.values())

    def list_tool_names(self) -> List[str]:
        """List all tool names."""
        return list(self._tools.keys())
