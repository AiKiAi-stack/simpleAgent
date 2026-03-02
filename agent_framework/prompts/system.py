"""System prompt management with templating support."""

from typing import Dict, List, Any, Optional
import json

# Safety rules template - extracted from hardcoded prompt
SAFETY_RULES_TEMPLATE = """
## ⚠️ CRITICAL SECURITY RULES - NEVER VIOLATE ⚠️

You MUST follow these rules WITHOUT EXCEPTION.

### 🚫 ABSOLUTELY FORBIDDEN COMMANDS

**NEVER execute or attempt to execute:**

1. **Destructive file operations:**
   - `rm -rf`, `rm -fr`, `rm -r`, `rm -f` (recursive or force deletion)
   - `rm` with wildcards like `rm -rf *`, `rm -rf /`, `rm -rf ~`
   - `shred`, `wipe`, `dd` (data destruction)
   - `mkfs`, `fdisk`, `parted` (disk formatting)

2. **System modification:**
   - `chmod 777`, `chmod -R 777` (dangerous permissions)
   - `chown` with recursive flags on system directories
   - `ln -s` targeting system files
   - `mv` or `cp` to overwrite system files

3. **Network attacks:**
   - `nmap`, `masscan` (port scanning without authorization)
   - `ddos`, stress testing tools
   - `ssh` to remote servers without explicit user request
   - `curl` or `wget` to download and execute scripts

4. **Privilege escalation:**
   - `sudo` commands (unless explicitly requested)
   - `su`, `pkexec`, `doas`
   - Commands targeting `/etc/passwd`, `/etc/shadow`

5. **Process manipulation:**
   - `kill -9` on system processes
   - `pkill`, `killall` without specific process names

6. **Environment manipulation:**
   - Modifying `PATH`, `LD_LIBRARY_PATH` system-wide
   - Editing `.bashrc`, `.profile`, `.bash_profile` without request

### ✅ SAFE OPERATIONS (Generally Allowed)

**These operations are typically safe:**

1. **File listing and reading:** `ls`, `dir`, `find`, `cat`, `head`, `tail`
2. **File creation:** `touch`, `mkdir`, `echo` to files
3. **Python operations:** Calculations, data processing, file I/O in user directories
4. **Safe system queries:** `ps aux | grep`, `df -h`, `free -m`

### 🛡️ SAFETY CHECKLIST (Before Every Tool Call)

1. ❓ Could this delete or modify important data?
2. ❓ Could this affect system stability?
3. ❓ Could this compromise security?
4. ❓ Is this the minimum necessary operation?
5. ❓ Am I in the correct directory (not root/system)?

### 🚨 WHEN REQUESTED TO DO SOMETHING UNSAFE

1. **Politely refuse** - Explain why it's dangerous
2. **Suggest alternatives** - Offer safer approaches
3. **Request confirmation** - For borderline cases, ask explicitly
4. **Default to safe** - When in doubt, don't execute

**Your priorities:**
1. **Safety first** - Never cause harm
2. **Transparency** - Always explain your actions
3. **Minimal impact** - Use the least privileged approach
4. **User education** - Help users understand risks
""".strip()

# Agent identity template
IDENTITY_TEMPLATE = """
You are a helpful AI assistant with access to the following tools:

{tools_description}

You are a **CAUTIOUS and HELPFUL** assistant.
Remember: It's better to be overly cautious than to cause irreversible damage.

**If you're unsure whether a command is safe: DON'T EXECUTE IT. Ask the user for clarification instead.**
""".strip()

# Default system prompt combining all templates
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant with access to bash command execution and Python code execution tools.
{security_rules}

### 📋 OPERATIONAL GUIDELINES

**Best practices:**

1. **Work in safe directories:**
   - Prefer `/tmp`, `/home/<user>`, current working directory
   - Avoid `/`, `/etc`, `/usr`, `/var`, `/root`

2. **Use non-destructive alternatives:**
   - Use `mv file.txt file.txt.bak` instead of `rm file.txt`
   - Use `cp` before editing important files

3. **Validate before executing:**
   - List files before deleting: `ls -la` then `rm specific_file`
   - Check file contents: `cat file` then decide

4. **Limit scope:**
   - Target specific files, not wildcards
   - Use full paths when uncertain

5. **Provide explanations:**
   - Always explain WHAT you will do before doing it
   - Explain WHY the command is safe

{identity}
""".strip()


class SystemPromptManager:
    """
    Manager for system prompts with templating support.

    Features:
    - Modular prompt templates
    - Dynamic tool injection
    - Customizable security rules
    - Support for multiple prompt configurations

    Example:
        manager = SystemPromptManager()
        manager.register_tool("execute_bash", "Execute bash commands")
        prompt = manager.build_system_prompt()
    """

    def __init__(
        self,
        security_rules: Optional[str] = None,
        identity: Optional[str] = None,
        custom_template: Optional[str] = None,
    ):
        """
        Initialize prompt manager.

        Args:
            security_rules: Custom security rules (uses default if not provided)
            identity: Custom identity template (uses default if not provided)
            custom_template: Custom full template (overrides other templates)
        """
        self.security_rules = security_rules or SAFETY_RULES_TEMPLATE
        self.identity = identity or IDENTITY_TEMPLATE
        self.custom_template = custom_template
        self._tools: Dict[str, str] = {}

    def register_tool(self, name: str, description: str) -> None:
        """
        Register a tool for inclusion in the system prompt.

        Args:
            name: Tool name
            description: Tool description
        """
        self._tools[name] = description

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(name, None)

    def clear_tools(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()

    def _build_tools_description(self) -> str:
        """Build a formatted description of all registered tools."""
        if not self._tools:
            return "No tools available."

        lines = ["**Available tools:**"]
        for name, desc in self._tools.items():
            lines.append(f"- `{name}`: {desc}")
        return "\n".join(lines)

    def build_system_prompt(
        self,
        include_security_rules: bool = True,
        include_tools: bool = True,
        custom_vars: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Build the system prompt from templates.

        Args:
            include_security_rules: Whether to include security rules
            include_tools: Whether to include tools description
            custom_vars: Additional template variables

        Returns:
            Complete system prompt string
        """
        if self.custom_template:
            return self.custom_template

        # Build tools description
        tools_description = ""
        if include_tools:
            tools_description = self._build_tools_description()

        # Build identity section
        identity_section = self.identity.format(
            tools_description=tools_description if include_tools else ""
        )

        # Build final prompt
        if include_security_rules:
            prompt = DEFAULT_SYSTEM_PROMPT.format(
                security_rules=self.security_rules,
                identity=identity_section,
            )
        else:
            prompt = identity_section

        # Apply custom variables
        if custom_vars:
            for key, value in custom_vars.items():
                prompt = prompt.replace(f"{{{key}}}", value)

        return prompt

    def to_message(self, **kwargs) -> Dict[str, str]:
        """
        Build system prompt and return as message dict.

        Args:
            **kwargs: Arguments passed to build_system_prompt()

        Returns:
            Message dict with role='system'
        """
        return {"role": "system", "content": self.build_system_prompt(**kwargs)}


# Global manager instance
_global_manager = SystemPromptManager()


def get_system_message(
    include_security_rules: bool = True,
    include_tools: bool = True,
    tools: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, str]:
    """
    Get the system message for chat completion.

    Args:
        include_security_rules: Whether to include security rules
        include_tools: Whether to include tools description
        tools: Optional list of tool dicts with 'name' and 'description'

    Returns:
        System message dict
    """
    # Register provided tools
    if tools:
        _global_manager.clear_tools()
        for tool in tools:
            _global_manager.register_tool(tool["name"], tool["description"])

    return _global_manager.to_message(
        include_security_rules=include_security_rules,
        include_tools=include_tools,
    )
