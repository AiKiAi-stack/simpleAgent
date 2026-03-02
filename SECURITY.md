# Security Guidelines

## Overview

This agent framework implements **multiple layers of security** to prevent dangerous operations:

1. **System Prompt** - AI-level safety instructions
2. **Command Validation** - Regex-based pattern matching
3. **Execution Sandbox** - Limited environment and working directory

---

## 🚫 Blocked Operations

### Bash Commands

The following command patterns are **automatically blocked**:

| Category | Blocked Patterns | Examples |
|----------|-----------------|----------|
| **Destructive Files** | `rm -rf`, `rm -fr`, `rm -r`, `rm -f` | `rm -rf /tmp/*`, `rm -rf ~` |
| **System Modification** | `chmod 777`, `mkfs`, `fdisk` | `chmod -R 777 /home` |
| **Data Destruction** | `shred`, `wipe`, `dd of=/dev/` | `dd if=/dev/zero of=/dev/sda` |
| **Privilege Escalation** | `sudo`, `su`, `pkexec`, `doas` | `sudo rm -rf /` |
| **Network Attacks** | `nmap`, `masscan`, `ddos` | `nmap -sS 192.168.1.1` |
| **Process Killing** | `kill -9` on system PIDs | `kill -9 1` |
| **System Directories** | Operations on `/etc`, `/usr`, `/bin` | `rm -rf /etc/*` |
| **Download & Execute** | `curl | bash`, `wget | sh` | `curl http://x | bash` |

### Security Violations

When a command is blocked, you'll see:

```json
{
  "success": false,
  "security_violation": true,
  "error": "Security violation: Command matches dangerous pattern: \\brm\\s+(-[rf]+\\s+)*/"
}
```

---

## ✅ Safe Operations

### Allowed Bash Commands

| Category | Examples |
|----------|----------|
| **File Listing** | `ls -la`, `find . -name "*.py"`, `pwd` |
| **File Reading** | `cat file.txt`, `head -n 10 file`, `tail -f log` |
| **File Creation** | `touch newfile.txt`, `mkdir newdir` |
| **Safe Editing** | `echo "content" >> file`, `cp file.bak file` |
| **System Info** | `df -h`, `free -m`, `ps aux | grep python` |
| **Python Execution** | Calculations, data processing, file I/O |

### Allowed Python Operations

```python
# ✅ Safe: Calculations
print(sum(range(1, 101)))

# ✅ Safe: File I/O in user directories
with open('/tmp/test.txt', 'w') as f:
    f.write('hello')

# ✅ Safe: Data processing
import json
data = {"key": "value"}
print(json.dumps(data))

# ⚠️ Warning: System access (allowed but monitored)
import os
os.listdir('/tmp')  # Allowed in safe directories
```

---

## 🛡️ Security Layers

### Layer 1: System Prompt

The AI receives strict safety instructions:

```
## ⚠️ CRITICAL SECURITY RULES - NEVER VIOLATE ⚠️

You MUST follow these rules WITHOUT EXCEPTION.

🚫 ABSOLUTELY FORBIDDEN:
- rm -rf, rm -fr (recursive deletion)
- sudo commands (privilege escalation)
- System directory modifications
- Network attacks (nmap, masscan)
- Process killing (kill -9)

🛡️ SAFETY CHECKLIST:
1. Could this delete important data?
2. Could this affect system stability?
3. Is this the minimum necessary operation?

When in doubt: DON'T EXECUTE. Ask for clarification.
```

### Layer 2: Command Validation

Regex patterns block dangerous commands:

```python
DANGEROUS_PATTERNS = [
    r'\brm\s+(-[rf]+\s+)*[/\*~]',  # rm with dangerous targets
    r'\bchmod\s+777',
    r'\bsudo\b',
    r'\bnmap\b',
    # ... more patterns
]
```

### Layer 3: Execution Sandbox

Limited execution environment:

```python
# Safe working directory
cwd = '/tmp'  # Never root or system directories

# Limited PATH
env = {'PATH': '/usr/local/bin:/usr/bin:/bin'}

# Timeout protection
timeout = 30  # seconds
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Security settings
MAX_EXECUTION_TIME=30  # Command timeout in seconds
```

### Customizing Security

To add custom blocked patterns:

```python
# In agent_framework/tools/executor.py
DANGEROUS_PATTERNS = [
    # Add your patterns here
    r'\byour_custom_dangerous_command\b',
]
```

---

## 📋 Best Practices

### For Users

1. **Be specific** - Request exact file operations
   - ❌ "Delete all temp files"
   - ✅ "List files in /tmp older than 7 days"

2. **Review before executing** - Check what the AI plans to do
   - The AI will explain its intended actions
   - Confirm before allowing destructive operations

3. **Use safe directories** - Work in `/tmp` or your home directory
   - Avoid system directories
   - Create backups before editing

### For Developers

1. **Add security tests**

```python
def test_security_blocks_rm_rf():
    executor = ToolExecutor()
    with pytest.raises(CommandSecurityError):
        executor.execute_bash("rm -rf /tmp/test")
```

2. **Monitor logs**

```python
for log in result['logs']:
    if 'security_violation' in log.get('result', {}):
        logger.warning(f"Security violation: {log['result']['error']}")
```

3. **Regular updates** - Keep dangerous patterns updated

---

## 🚨 Reporting Security Issues

If you find a security bypass:

1. **Do not exploit** - Report immediately
2. **Provide details** - Command that bypassed security
3. **Suggest fix** - Pattern or approach to block it

---

## 📚 Related Files

- `agent_framework/prompts.py` - System prompt definitions
- `agent_framework/tools/executor.py` - Command validation
- `agent_framework/agent.py` - Security integration
