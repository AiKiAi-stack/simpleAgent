from typing import Dict, Any, List


def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Return OpenAI-compatible tool schemas for Qwen3.

    Returns:
        List of tool schemas that can be passed to vLLM chat completion API.
        Each schema defines a function with name, description, and parameters.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "execute_bash",
                "description": "Execute a bash command on the local system. "
                "Use this for file operations, system commands, "
                "or any shell-based tasks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute",
                        }
                    },
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_python",
                "description": "Execute Python code and return the output. "
                "Use this for calculations, data processing, "
                "or any Python-based tasks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        }
                    },
                    "required": ["code"],
                },
            },
        },
    ]
