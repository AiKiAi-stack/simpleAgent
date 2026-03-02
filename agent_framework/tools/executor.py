import subprocess
import sys
import io
from typing import Tuple
from contextlib import redirect_stdout, redirect_stderr


class ToolExecutor:
    """Execute tools (bash commands, Python code)."""

    def __init__(self, max_execution_time: int = 30):
        """
        Initialize tool executor.

        Args:
            max_execution_time: Maximum execution time in seconds
        """
        self.max_execution_time = max_execution_time

    def execute_bash(self, command: str) -> Tuple[str, str, int]:
        """
        Execute bash command and return output.

        Args:
            command: Bash command to execute

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.max_execution_time,
                cwd="/tmp",  # Safe working directory
            )
            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired:
            return "", f"Command timed out after {self.max_execution_time}s", -1

        except Exception as e:
            return "", str(e), -1

    def execute_python(self, code: str) -> Tuple[str, str]:
        """
        Execute Python code and return output.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (stdout, stderr)
        """
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            # Create a namespace for execution with restricted builtins
            namespace = {"__builtins__": __builtins__}

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, namespace)

            stdout = stdout_buffer.getvalue()
            stderr = stderr_buffer.getvalue()
            return stdout, stderr

        except Exception as e:
            return "", f"Execution error: {str(e)}"

        finally:
            stdout_buffer.close()
            stderr_buffer.close()
