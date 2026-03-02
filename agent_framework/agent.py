from typing import List, Dict, Any, Optional
from .llm_client import LLMClient
from .tools.executor import ToolExecutor, CommandSecurityError
from .tools.schemas import get_tool_schemas
from .prompts import get_system_message
from .config import settings
import json


class Agent:
    """Agent with tool calling capabilities and strict security policies."""

    def __init__(self, max_iterations: int = 10):
        """
        Initialize agent with security-first approach.

        Args:
            max_iterations: Maximum tool calling iterations before giving up
        """
        self.llm = LLMClient()
        self.executor = ToolExecutor(settings.max_execution_time)
        self.tool_schemas = get_tool_schemas()
        self.max_iterations = max_iterations
        self.system_message = get_system_message()

    def run(self, user_message: str) -> Dict[str, Any]:
        """
        Run agent loop until final response or max iterations.

        Args:
            user_message: User input message to process

        Returns:
            Dictionary containing:
                - response: Final assistant response
                - logs: List of all iteration logs
                - usage: Token usage statistics
                - iterations: Number of iterations completed
                - error: Error message if any (optional)
        """
        # Start with system message for security context
        messages = [self.system_message, {"role": "user", "content": user_message}]
        logs = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            # Get LLM response
            response = self.llm.chat_completion(
                messages=messages, tools=self.tool_schemas
            )

            logs.append({"iteration": iteration, "response": response})

            # Check for tool calls
            if response["tool_calls"]:
                for tool_call in response["tool_calls"]:
                    try:
                        result = self._execute_tool(tool_call)
                    except CommandSecurityError as e:
                        # Security violation - don't execute, return error
                        result = {
                            "success": False,
                            "security_violation": True,
                            "error": str(e),
                        }

                    logs.append(
                        {
                            "iteration": iteration,
                            "tool_call": {
                                "id": tool_call.id,
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                            "result": result,
                        }
                    )

                    # Add tool result to messages
                    messages.append(
                        {"role": "assistant", "content": response["content"]}
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps(result, ensure_ascii=False),
                            "tool_call_id": tool_call.id,
                        }
                    )
            else:
                # No more tool calls, return final response
                return {
                    "response": response["content"],
                    "logs": logs,
                    "usage": response["usage"],
                    "iterations": iteration,
                }

        # Max iterations reached
        return {
            "response": "Max iterations reached",
            "logs": logs,
            "usage": {},
            "iterations": iteration,
            "error": "max_iterations_exceeded",
        }

    def _execute_tool(self, tool_call: Any) -> Dict[str, Any]:
        """
        Execute a single tool call with security validation.

        Args:
            tool_call: Tool call object from LLM response

        Returns:
            Dictionary with execution result
        """
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        try:
            if function_name == "execute_bash":
                stdout, stderr, returncode = self.executor.execute_bash(
                    arguments["command"]
                )
                return {
                    "success": returncode == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": returncode,
                }

            elif function_name == "execute_python":
                stdout, stderr = self.executor.execute_python(arguments["code"])
                return {"success": not stderr, "stdout": stdout, "stderr": stderr}

            else:
                return {"success": False, "error": f"Unknown function: {function_name}"}

        except CommandSecurityError:
            # Re-raise security errors to be handled by run()
            raise

        except Exception as e:
            return {"success": False, "error": str(e)}
