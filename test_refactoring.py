"""Test script for Qwen3 Agent Framework refactoring."""

import sys
import asyncio


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        # Core
        from agent_framework.core import ReActAgent, Message, AgentResponse, settings
        print("  ✓ Core imports OK")

        # Tools
        from agent_framework.tools import (
            Tool,
            SyncTool,
            ToolExecutionError,
            ToolRegistry,
            BashTool,
            PythonTool,
            get_tool_schemas,
        )
        print("  ✓ Tools imports OK")

        # Skills
        from agent_framework.skills import Skill, SkillRegistry
        print("  ✓ Skills imports OK")

        # MCP
        from agent_framework.mcp import MCPClient, MCPAdapter
        print("  ✓ MCP imports OK")

        # LLM
        from agent_framework.llm import LLM, LLMResponse, VLLMClient
        print("  ✓ LLM imports OK")

        # Prompts
        from agent_framework.prompts import SystemPromptManager, get_system_message
        print("  ✓ Prompts imports OK")

        # API
        from agent_framework.api import ChatRequest, ChatResponse, create_app
        print("  ✓ API imports OK")

        return True

    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_tool_instantiation():
    """Test that tools can be instantiated."""
    print("\nTesting tool instantiation...")

    try:
        bash_tool = BashTool()
        assert bash_tool.name == "execute_bash"
        assert bash_tool.description is not None
        assert "command" in bash_tool.parameters["properties"]
        print("  ✓ BashTool OK")

        python_tool = PythonTool()
        assert python_tool.name == "execute_python"
        assert python_tool.description is not None
        assert "code" in python_tool.parameters["properties"]
        print("  ✓ PythonTool OK")

        return True

    except Exception as e:
        print(f"  ✗ Tool instantiation failed: {e}")
        return False


def test_tool_registry():
    """Test tool registry functionality."""
    print("\nTesting tool registry...")

    try:
        from agent_framework.tools import ToolRegistry, register_tool, get_tool, get_all_tools

        registry = ToolRegistry()

        # Test register
        bash_tool = BashTool()
        registry.register(bash_tool)
        assert "execute_bash" in registry.list_names()
        print("  ✓ Register OK")

        # Test get
        retrieved = registry.get("execute_bash")
        assert retrieved is not None
        assert retrieved.name == "execute_bash"
        print("  ✓ Get OK")

        # Test schemas
        schemas = registry.get_all_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "execute_bash"
        print("  ✓ Schemas OK")

        # Test global registry
        register_tool(PythonTool())
        assert get_tool("execute_python") is not None
        print("  ✓ Global registry OK")

        return True

    except Exception as e:
        print(f"  ✗ Registry test failed: {e}")
        return False


def test_prompt_manager():
    """Test system prompt manager."""
    print("\nTesting prompt manager...")

    try:
        from agent_framework.prompts import SystemPromptManager, get_system_message

        manager = SystemPromptManager()
        manager.register_tool("execute_bash", "Execute bash commands")
        manager.register_tool("execute_python", "Execute Python code")

        prompt = manager.build_system_prompt()
        assert "execute_bash" in prompt
        assert "execute_python" in prompt
        assert "SECURITY RULES" in prompt or "CRITICAL" in prompt
        print("  ✓ Prompt building OK")

        # Test get_system_message
        msg = get_system_message(
            include_tools=True,
            tools=[
                {"name": "test_tool", "description": "A test tool"},
            ],
        )
        assert msg["role"] == "system"
        print("  ✓ System message OK")

        return True

    except Exception as e:
        print(f"  ✗ Prompt test failed: {e}")
        return False


async def test_tool_execution():
    """Test tool execution."""
    print("\nTesting tool execution...")

    try:
        bash_tool = BashTool()

        # Test safe command
        result = await bash_tool.execute(command="echo 'Hello, World!'")
        assert result["success"] is True
        assert "Hello, World!" in result["stdout"]
        print("  ✓ Bash execution OK")

        # Test security violation
        try:
            await bash_tool.execute(command="rm -rf /tmp/test")
            print("  ✗ Security check FAILED (should have raised)")
            return False
        except Exception as e:
            if "Security violation" in str(e):
                print("  ✓ Security check OK")
            else:
                print(f"  ✗ Unexpected error: {e}")
                return False

        # Test Python execution
        python_tool = PythonTool()
        result = await python_tool.execute(code="print(2 + 2)")
        assert result["success"] is True
        assert "4" in result["stdout"]
        print("  ✓ Python execution OK")

        return True

    except Exception as e:
        print(f"  ✗ Tool execution failed: {e}")
        return False


def test_api_app():
    """Test API application creation."""
    print("\nTesting API application...")

    try:
        from agent_framework.api import create_app, ChatRequest, ChatResponse

        app = create_app()
        assert app is not None
        assert app.title == "Qwen3 Agent API"
        print("  ✓ App creation OK")

        # Test schemas
        req = ChatRequest(message="test", max_iterations=5)
        assert req.message == "test"
        assert req.max_iterations == 5
        print("  ✓ Schemas OK")

        return True

    except Exception as e:
        print(f"  ✗ API test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Qwen3 Agent Framework - Refactoring Verification Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Tool Instantiation", test_tool_instantiation()))
    results.append(("Tool Registry", test_tool_registry()))
    results.append(("Prompt Manager", test_prompt_manager()))
    results.append(("Tool Execution", await test_tool_execution()))
    results.append(("API App", test_api_app()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
