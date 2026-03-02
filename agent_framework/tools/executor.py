import subprocess
import io
import re
from typing import Tuple, Optional
from contextlib import redirect_stdout, redirect_stderr


# Dangerous command patterns that should never be executed
DANGEROUS_PATTERNS = [
    # ALL rm commands are dangerous (block everything)
    (r'\brm\b', 'rm command is potentially destructive - use "ls" first to list files, then specify exact files to remove'),
    
    # System modification
    (r'\bchmod\s+777\b', 'chmod 777 gives full permissions to everyone'),
    (r'\bchmod\s+-R\b', 'recursive chmod is dangerous'),
    (r'\bchown\b', 'chown can break file permissions'),
    (r'\bmkfs\b', 'mkfs formats disks'),
    (r'\bfdisk\b', 'fdisk modifies partition tables'),
    (r'\bparted\b', 'parted modifies partitions'),
    (r'\bshred\b', 'shred destroys data'),
    (r'\bwipe\b', 'wipe destroys data'),
    
    # Dangerous dd
    (r'\bdd\s+.*of=/dev/', 'dd to device can destroy data'),
    
    # Privilege escalation
    (r'\bsudo\b', 'sudo requires elevated privileges'),
    (r'\bsu\b', 'su switches users'),
    (r'\bpkexec\b', 'pkexec is privilege escalation'),
    (r'\bdoas\b', 'doas is privilege escalation'),
    
    # Network attacks
    (r'\bnmap\b', 'nmap is a port scanner'),
    (r'\bmasscan\b', 'masscan is a port scanner'),
    (r'\bddos\b', 'DDoS tools are not allowed'),
    
    # Process killing
    (r'\bkill\s+-9\b', 'kill -9 forcefully terminates processes'),
    (r'\bpkill\b', 'pkill terminates processes'),
    (r'\bkillall\b', 'killall terminates all instances of a process'),
    
    # System directories
    (r'\b(mv|cp|rm)\s+.*\s+/etc/', 'Modifying /etc is dangerous'),
    (r'\b(mv|cp|rm)\s+.*\s+/usr/', 'Modifying /usr is dangerous'),
    (r'\b(mv|cp|rm)\s+.*\s+/bin/', 'Modifying /bin is dangerous'),
    (r'\b(mv|cp|rm)\s+.*\s+/sbin/', 'Modifying /sbin is dangerous'),
    (r'\b(mv|cp|rm)\s+.*\s+/root/', 'Modifying /root is dangerous'),
]

# Patterns that need extra scrutiny (warn but allow with caution)
WARNING_PATTERNS = [
    (r'\bcurl\b.*\|\s*(bash|sh|zsh)', 'Piping curl to shell can execute arbitrary code'),
    (r'\bwget\b.*\|\s*(bash|sh|zsh)', 'Piping wget to shell can execute arbitrary code'),
    (r'\b>\s*/dev/', 'Redirecting to /dev/null loses output'),
]


class CommandSecurityError(Exception):
    """Raised when a command violates security policies."""
    pass


class CommandWarningError(Exception):
    """Raised when a command triggers a warning (can be overridden)."""
    pass


class ToolExecutor:
    """Execute tools (bash commands, Python code) with strict security checks."""

    def __init__(self, max_execution_time: int = 30, strict_mode: bool = True):
        """
        Initialize tool executor with security validation.

        Args:
            max_execution_time: Maximum execution time in seconds
            strict_mode: If True, block all dangerous commands; if False, allow with warnings
        """
        self.max_execution_time = max_execution_time
        self.strict_mode = strict_mode

    def _is_command_safe(self, command: str) -> Tuple[bool, Optional[str], bool]:
        """
        Check if a bash command is safe to execute.

        Args:
            command: The bash command to validate

        Returns:
            Tuple of (is_safe, reason_if_unsafe, is_warning)
            - is_safe: True if command can execute
            - reason_if_unsafe: Explanation of why it's blocked
            - is_warning: True if it's a warning (not block) in non-strict mode
        """
        # Check dangerous patterns (always block)
        for pattern, reason in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Security violation: {reason} (pattern: {pattern})", False

        # Check warning patterns
        for pattern, reason in WARNING_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                if self.strict_mode:
                    return False, f"Security warning (strict mode): {reason}", False
                else:
                    return True, None, True  # Allow with warning flag

        # Additional checks

        # Block rm with any flags or paths
        if re.search(r'\brm\s+', command):
            return False, "Security violation: rm command is blocked. Use 'ls' to list files first, then request removal of specific files.", False

        # Block wildcard operations with destructive commands
        if re.search(r'\b(mv|cp|chmod)\s+.*\*', command):
            return False, "Security violation: wildcards with file operations are not allowed", False

        # Check for path traversal to system paths
        system_paths = ['/etc', '/usr', '/bin', '/sbin', '/lib', '/lib64', '/boot', '/root', '/proc', '/sys']
        for sys_path in system_paths:
            if sys_path in command:
                # Check if it's a destructive operation
                for destructive in ['rm', 'mv', 'cp', 'chmod', 'chown', 'dd', '>']:
                    if destructive in command:
                        return False, f"Security violation: {destructive} operation on system path {sys_path}", False

        return True, None, False

    def _get_working_directory(self) -> str:
        """Get a safe working directory for command execution."""
        # Default to /tmp for safety
        return '/tmp'

    def execute_bash(self, command: str, bypass_security: bool = False) -> Tuple[str, str, int]:
        """
        Execute bash command with security validation.

        Args:
            command: Bash command to execute
            bypass_security: If True, skip security checks (DANGEROUS - for internal use only)

        Returns:
            Tuple of (stdout, stderr, return_code)

        Raises:
            CommandSecurityError: If command violates security policies
        """
        if not bypass_security:
            # Security check
            is_safe, reason, is_warning = self._is_command_safe(command)
            if not is_safe:
                raise CommandSecurityError(f"{reason}\n\nBlocked command: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.max_execution_time,
                cwd=self._get_working_directory(),
                # Additional safety: limit environment
                env={'PATH': '/usr/local/bin:/usr/bin:/bin'}
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
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            # Create a namespace for execution with limited builtins
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
