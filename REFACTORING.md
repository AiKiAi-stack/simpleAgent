# Qwen3 Agent Framework v0.2.0 - Refactored Architecture

## Overview

This refactoring transforms the Qwen3 Agent Framework into a clean, extensible ReAct-based agent system with proper separation of concerns and standardized interfaces for Tools, MCP servers, and Skills.

## New Directory Structure

```
agent_framework/
├── core/
│   ├── __init__.py          # Core exports
│   ├── agent.py             # ReActAgent (Reason-Act-Observe loop)
│   ├── message.py           # Message, AgentResponse, ToolResult dataclasses
│   └── config.py            # Settings with security configuration
├── tools/
│   ├── __init__.py          # Tool exports
│   ├── base.py              # Tool, SyncTool abstract base classes
│   ├── registry.py          # ToolRegistry for tool management
│   ├── builtin/
│   │   ├── __init__.py
│   │   ├── bash.py          # BashTool implementation
│   │   └── python.py        # PythonTool implementation
│   └── executor.py          # Low-level execution with security checks
├── skills/
│   ├── __init__.py          # Skill exports
│   ├── base.py              # Skill base class (composable tools)
│   └── registry.py          # SkillRegistry
├── mcp/
│   ├── __init__.py          # MCP exports
│   ├── client.py            # MCPClient for MCP server connections
│   └── adapter.py           # MCPAdapter to wrap MCP as Tools
├── llm/
│   ├── __init__.py          # LLM exports
│   ├── base.py              # LLM abstract interface
│   └── vllm_client.py       # VLLMClient implementation
├── prompts/
│   ├── __init__.py          # Prompt exports
│   └── system.py            # SystemPromptManager with templating
├── api/
│   ├── __init__.py          # API exports
│   ├── app.py               # FastAPI application factory
│   ├── routes.py            # API routes (/chat, /health)
│   └── schemas.py           # Pydantic request/response models
├── __init__.py              # Main package exports
├── main.py                  # Entry point
└── compat.py                # Backward compatibility layer
```

## Key Improvements

### 1. Clean ReAct Architecture

The agent loop is now clearly separated into three phases:

```python
class ReActAgent:
    async def run(self, user_message: str) -> AgentResponse:
        while iteration < max_iterations:
            # Reason: Get LLM response
            llm_response = await self._reason(messages)

            if llm_response.has_tool_calls():
                # Act: Execute tool calls
                results = await self._act(llm_response.tool_calls)

                # Observe: Feed results back to LLM
                messages.extend(self._observe(results, tool_calls))
            else:
                return AgentResponse(...)
```

### 2. Extensible Tool System

Tools now follow a standard interface:

```python
from agent_framework import Tool, SyncTool

class MyCustomTool(SyncTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Description of what my tool does"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"],
        }

    def _execute_sync(self, input: str) -> dict:
        # Tool implementation
        return {"result": f"Processed: {input}"}
```

### 3. Tool Registry

Dynamic tool registration and discovery:

```python
from agent_framework import register_tool, get_tool, get_all_tools

# Register a tool
register_tool(MyCustomTool())

# Get a specific tool
tool = get_tool("my_tool")

# Get all registered tools
all_tools = get_all_tools()

# Get OpenAI-compatible schemas
schemas = get_tool_schemas()
```

### 4. MCP Integration Ready

MCP servers can be wrapped as tools:

```python
from agent_framework import MCPClient, MCPAdapter

client = MCPClient("search-server")
await client.connect()

adapter = MCPAdapter(
    server_name="search",
    tool_name="web_search",
    client=client
)

result = await adapter.execute(query="python tutorial")
```

### 5. Skill Composition

Skills combine multiple tools for complex workflows:

```python
from agent_framework import Skill

class ResearchSkill(Skill):
    def __init__(self):
        super().__init__(
            name="research",
            description="Research and synthesize information",
            tools=[SearchTool(), SummarizeTool()],
        )

    async def execute(self, task: str, **kwargs) -> dict:
        # Orchestrate multiple tools
        search_result = await self.tools["search"].execute(query=task)
        summary = await self.tools["summarize"].execute(content=search_result)
        return summary
```

### 6. Security Configuration

Security rules are now configurable:

```python
from agent_framework.core.config import settings

# Access security settings
dangerous_patterns = settings.security.dangerous_patterns
safe_directories = settings.security.safe_directories
```

## Migration Guide

### For Existing Code

Old imports (still work via `compat.py`):
```python
from agent_framework.agent import Agent
from agent_framework.config import settings
```

New imports (recommended):
```python
from agent_framework.core import ReActAgent, settings
from agent_framework.tools import BashTool, PythonTool
```

### API Changes

The API endpoints remain backward compatible:
- `POST /chat` - Process user message
- `GET /health` - Health check
- `GET /` - API info

## Usage Examples

### Basic Usage

```python
import asyncio
from agent_framework import (
    ReActAgent, VLLMClient, BashTool, PythonTool, get_system_message
)

async def main():
    # Initialize components
    llm = VLLMClient()
    tools = [BashTool(), PythonTool()]

    # Build system prompt with tool info
    system_message = get_system_message(
        include_security_rules=True,
        include_tools=True,
        tools=[
            {"name": "execute_bash", "description": "Execute bash commands"},
            {"name": "execute_python", "description": "Execute Python code"},
        ]
    )

    # Create and run agent
    agent = ReActAgent(
        llm=llm,
        tools=tools,
        system_prompt=system_message["content"],
        max_iterations=10
    )

    response = await agent.run("List files in /tmp")
    print(response.response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Running the API Server

```bash
cd .worktrees/qwen3-agent
python -m agent_framework.main
```

Or:
```bash
python -c "from agent_framework.main import main; main()"
```

Then access:
- API docs: http://localhost:8080/docs
- Health check: http://localhost:8080/health
- Chat endpoint: POST http://localhost:8080/chat

## Testing

Run the verification tests:

```bash
cd .worktrees/qwen3-agent
python test_refactoring.py
```

## Version History

### v0.2.0 (Refactored)

- **Breaking**: Reorganized module structure
- Added ReActAgent with clear Reason-Act-Observe separation
- Added Tool base class and registry
- Added Skill composition system
- Added MCP adapter for external tool integration
- Moved security rules to configurable templates
- Improved type hints and documentation

### v0.1.0 (Original)

- Initial implementation with coupled agent/executor logic
- Hardcoded security prompts
- No tool registry or extension system

## Future Enhancements

1. **MCP Server Support**: Full implementation of MCP client protocol
2. **Skill Library**: Pre-built skills for common workflows
3. **Streaming Support**: Stream LLM responses and tool results
4. **Conversation Memory**: Persistent conversation history
5. **Multi-Agent Coordination**: Support for multiple collaborating agents

## License

Same as original project license.
