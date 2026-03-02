"""Test script for Qwen3 Agent Framework - Refactored version."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / '.worktrees' / 'qwen3-agent'))

from agent_framework.tools.executor import ToolExecutor, CommandSecurityError
from agent_framework.tools.builtin import BashTool, PythonTool
from agent_framework.tools.registry import ToolRegistry, get_tool_schemas, register_tool


class TestToolExecutor:
    """Test cases for ToolExecutor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.executor = ToolExecutor(max_execution_time=10)

    def test_bash_echo_command(self):
        """Test bash echo command execution."""
        stdout, stderr, code = self.executor.execute_bash("echo hello")
        assert code == 0
        assert "hello" in stdout
        assert not stderr

    def test_bash_invalid_command(self):
        """Test bash with invalid command."""
        stdout, stderr, code = self.executor.execute_bash("nonexistent_command_xyz_123")
        assert code != 0

    def test_bash_ls_command(self):
        """Test bash ls command."""
        stdout, stderr, code = self.executor.execute_bash("ls -la")
        assert code == 0
        assert "total" in stdout or "drwx" in stdout

    def test_python_print(self):
        """Test Python print execution."""
        stdout, stderr = self.executor.execute_python("print('hello')")
        assert "hello" in stdout
        assert not stderr

    def test_python_calculation(self):
        """Test Python calculation."""
        stdout, stderr = self.executor.execute_python("print(2 + 2)")
        assert "4" in stdout

    def test_python_multiple_lines(self):
        """Test Python multi-line code."""
        code = """
x = 10
y = 20
print(x + y)
"""
        stdout, stderr = self.executor.execute_python(code)
        assert "30" in stdout

    def test_python_error_handling(self):
        """Test Python error handling."""
        code = "print(undefined_variable)"
        stdout, stderr = self.executor.execute_python(code)
        assert stderr  # Should have error message

    def test_security_violation_rm_rf(self):
        """Test that rm -rf raises security error."""
        with pytest.raises(CommandSecurityError):
            self.executor.execute_bash("rm -rf /tmp/test")

    def test_security_violation_sudo(self):
        """Test that sudo raises security error."""
        with pytest.raises(CommandSecurityError):
            self.executor.execute_bash("sudo ls")


class TestBashTool:
    """Test cases for BashTool."""

    @pytest.mark.asyncio
    async def test_bash_tool_execute(self):
        """Test BashTool execution."""
        tool = BashTool()
        result = await tool.execute(command="echo 'test'")
        assert result["success"] is True
        assert "test" in result["stdout"]

    @pytest.mark.asyncio
    async def test_bash_tool_schema(self):
        """Test BashTool schema."""
        tool = BashTool()
        schema = tool.to_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "execute_bash"
        assert "command" in schema["function"]["parameters"]["properties"]


class TestPythonTool:
    """Test cases for PythonTool."""

    @pytest.mark.asyncio
    async def test_python_tool_execute(self):
        """Test PythonTool execution."""
        tool = PythonTool()
        result = await tool.execute(code="print('hello')")
        assert result["success"] is True
        assert "hello" in result["stdout"]

    @pytest.mark.asyncio
    async def test_python_tool_schema(self):
        """Test PythonTool schema."""
        tool = PythonTool()
        schema = tool.to_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "execute_python"
        assert "code" in schema["function"]["parameters"]["properties"]


class TestToolRegistry:
    """Test cases for ToolRegistry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()

    def teardown_method(self):
        """Clean up after tests."""
        self.registry.clear()

    def test_register_tool(self):
        """Test tool registration."""
        tool = BashTool()
        self.registry.register(tool)
        assert "execute_bash" in self.registry.list_names()

    def test_get_tool(self):
        """Test getting a tool by name."""
        tool = BashTool()
        self.registry.register(tool)
        retrieved = self.registry.get("execute_bash")
        assert retrieved is not None
        assert retrieved.name == "execute_bash"

    def test_get_tool_not_found(self):
        """Test getting a non-existent tool."""
        retrieved = self.registry.get("nonexistent_tool")
        assert retrieved is None

    def test_get_all_schemas(self):
        """Test getting all tool schemas."""
        self.registry.register(BashTool())
        self.registry.register(PythonTool())
        schemas = self.registry.get_all_schemas()
        assert len(schemas) == 2
        assert schemas[0]["function"]["name"] == "execute_bash"
        assert schemas[1]["function"]["name"] == "execute_python"

    def test_global_registry(self):
        """Test global registry functions."""
        register_tool(BashTool())
        from agent_framework.tools.registry import get_tool
        tool = get_tool("execute_bash")
        assert tool is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
