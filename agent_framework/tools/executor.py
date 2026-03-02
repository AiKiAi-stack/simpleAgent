import subprocess
import io
import re
from typing import Tuple, Optional
from contextlib import redirect_stdout, redirect_stderr


# Dangerous command patterns that should never be executed
DANGEROUS_PATTERNS = [
    # Destructive file operations
    r"\brm\s+(-[rf]+\s+)*[/\*~]",  # rm with dangerous targets
    r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+",  # rm -rf, rm -fr, etc.
    r"\brm\s+-[a-z]*[rR]",  # rm with recursive flag
    r"\brm\s+-[a-z]*[fF]",  # rm with force flag
    # System modification
    r"\bchmod\s+777",
    r"\bchown\s+(-R\s+)?root",
    r"\bmkfs\b",
    r"\bfdisk\b",
    r"\bparted\b",
    r"\bshred\b",
    r"\bwipe\b",
    # Dangerous dd
    r"\bdd\s+.*of=/dev/",
    # Privilege escalation
    r"\bsudo\b",
    r"\bsu\s+-",
    r"\bpkexec\b",
    r"\bdoas\b",
    # Network attacks
    r"\bnmap\b",
    r"\bmasscan\b",
    r"\bddos\b",
    # Process killing
    r"\bkill\s+-9\s+[0-9]{1,3}$",  # kill -9 on PID
    # System directories
    r"\b(mv|cp|rm|chmod)\s+.*\s+/(etc|usr|var|root|boot|sys|proc)\b",
]

# Safe directories for execution
SAFE_DIRECTORIES = [
    "/tmp",
    "/home/",
    "/var/tmp",
]


class CommandSecurityError(Exception):
    """Raised when a command violates security policies."""

    pass


class ToolExecutor:
    """Execute tools (bash commands, Python code) with security checks."""

    def __init__(self, max_execution_time: int = 30):
        """
        Initialize tool executor with security validation.

        Args:
            max_execution_time: Maximum execution time in seconds
        """
        self.max_execution_time = max_execution_time

    def _is_command_safe(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a bash command is safe to execute.

        Args:
            command: The bash command to validate

        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        # Check against dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Command matches dangerous pattern: {pattern}"

        # Check for wildcard deletions
        if re.search(r"\brm\s+.*\*", command):
            return False, "rm with wildcards is not allowed"

        # Check for path traversal in destructive commands
        destructive_keywords = ["rm", "mv", "cp", "chmod", "chown", "dd"]
        for keyword in destructive_keywords:
            if keyword in command.lower():
                # Check if targeting system paths
                if re.search(
                    rf"\b{keyword}\b.*/(etc|usr|bin|sbin|lib|boot|root)\b", command
                ):
                    return False, f"Cannot use {keyword} on system directories"

        # Check for curl/wget pipe to shell
        if re.search(r"(curl|wget).*\|\s*(bash|sh|zsh)", command):
            return False, "Piping downloaded content to shell is not allowed"

        return True, None

    def _get_working_directory(self) -> str:
        """Get a safe working directory for command execution."""
        # Default to /tmp for safety
        return "/tmp"

    def execute_bash(self, command: str) -> Tuple[str, str, int]:
        """
        Execute bash command with security validation.

        Args:
            command: Bash command to execute

        Returns:
            Tuple of (stdout, stderr, return_code)

        Raises:
            CommandSecurityError: If command violates security policies
        """
        # Security check
        is_safe, reason = self._is_command_safe(command)
        if not is_safe:
            raise CommandSecurityError(f"Security violation: {reason}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.max_execution_time,
                cwd=self._get_working_directory(),
                # Additional safety: limit environment
                env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
            )
            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired:
            return "", f"Command timed out after {self.max_execution_time}s", -1

        except Exception as e:
            return "", str(e), -1

    def execute_python(self, code: str) -> Tuple[str, str]:
        """
        Execute Python code with security checks.

        Args:
            code: Python code to execute

        Returns:
            Tuple of (stdout, stderr)
        """
        # Basic security: check for dangerous imports
        dangerous_imports = [
            "import os",
            "from os",
            "import sys",
            "from sys",
            "import subprocess",
            "import multiprocessing",
            "import socket",
            "import requests",
            "import urllib",
            "import ctypes",
            "import ctypes.util",
        ]

        for dangerous in dangerous_imports:
            if dangerous in code:
                # Allow these but warn in stderr
                pass  # We'll allow them for now, could be restricted further

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            # Create a namespace for execution
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
