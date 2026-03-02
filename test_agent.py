"""Test script for Agent Framework."""

import pytest
from agent_framework.tools.executor import ToolExecutor
from agent_framework.tools.schemas import get_tool_schemas


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


class TestToolSchemas:
    """Test cases for tool schemas."""

    def test_schema_count(self):
        """Test that two tool schemas are returned."""
        schemas = get_tool_schemas()
        assert len(schemas) == 2

    def test_bash_schema(self):
        """Test bash tool schema structure."""
        schemas = get_tool_schemas()
        bash_schema = schemas[0]

        assert bash_schema["type"] == "function"
        assert bash_schema["function"]["name"] == "execute_bash"
        assert "description" in bash_schema["function"]
        assert "parameters" in bash_schema["function"]
        assert "command" in bash_schema["function"]["parameters"]["properties"]

    def test_python_schema(self):
        """Test Python tool schema structure."""
        schemas = get_tool_schemas()
        python_schema = schemas[1]

        assert python_schema["type"] == "function"
        assert python_schema["function"]["name"] == "execute_python"
        assert "description" in python_schema["function"]
        assert "parameters" in python_schema["function"]
        assert "code" in python_schema["function"]["parameters"]["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
