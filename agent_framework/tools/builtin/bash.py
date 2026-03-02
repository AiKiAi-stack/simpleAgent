"""Bash tool for executing shell commands."""

import subprocess
import re
from typing import Any, Dict, Optional, Tuple

from ..base import SyncTool, ToolExecutionError
from ..executor import CommandSecurityError


class BashTool(SyncTool):
    """
    Tool for executing bash commands with security validation.

    Security features:
    - Blocks dangerous patterns (rm -rf, sudo, etc.)
    - Restricts execution to safe directories
    - Limits execution time
    - Sanitizes environment variables
    """

    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        # Destructive file operations
        r"\brm\s+(-[rf]+\s+)*[/\*~]",
        r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+",
        r"\brm\s+-[a-z]*[rR]",
        r"\brm\s+-[a-z]*[fF]",
        # System modification
        r"\bchmod\s+777",
        r"\bchown\s+(-R\s+)?root",
        r"\bmkfs\b",
        r"\bfdisk\b",
        r"\bparted\b",
        r"\bshred\b",
        r"\bwipe\b",
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
        r"\bkill\s+-9\s+[0-9]{1,3}$",
        # System directories
        r"\b(mv|cp|rm|chmod)\s+.*\s+/(etc|usr|var|root|boot|sys|proc)\b",
    ]

    # Safe directories
    SAFE_DIRECTORIES = ["/tmp", "/home/", "/var/tmp"]

    @property
    def name(self) -> str:
        return "execute_bash"

    @property
    def description(self) -> str:
        return (
            "Execute a bash command on the local system. "
            "Use this for file operations, system commands, or any shell-based tasks. "
            "Security restrictions apply: no destructive operations, no sudo, no system modifications."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                }
            },
            "required": ["command"],
        }

    def __init__(self, max_execution_time: int = 30):
        """
        Initialize bash tool.

        Args:
            max_execution_time: Maximum execution time in seconds
        """
        self.max_execution_time = max_execution_time

    def _is_command_safe(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check if a bash command is safe to execute."""
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Command matches dangerous pattern: {pattern}"

        if re.search(r"\brm\s+.*\*", command):
            return False, "rm with wildcards is not allowed"

        destructive_keywords = ["rm", "mv", "cp", "chmod", "chown", "dd"]
        for keyword in destructive_keywords:
            if keyword in command.lower():
                if re.search(rf"\b{keyword}\b.*/(etc|usr|bin|sbin|lib|boot|root)\b", command):
                    return False, f"Cannot use {keyword} on system directories"

        if re.search(r"(curl|wget).*\|\s*(bash|sh|zsh)", command):
            return False, "Piping downloaded content to shell is not allowed"

        return True, None

    def _get_working_directory(self) -> str:
        """Get a safe working directory for command execution."""
        return "/tmp"

    def _execute_sync(self, command: str) -> Dict[str, Any]:
        """
        Execute bash command with security validation.

        Args:
            command: Bash command to execute

        Returns:
            Dictionary with stdout, stderr, returncode, success
        """
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
                env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {self.max_execution_time}s",
                "returncode": -1,
                "success": False,
            }

        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "success": False,
            }
