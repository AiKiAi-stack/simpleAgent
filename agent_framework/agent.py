from typing import List, Dict, Any, Optional
from .llm_client import LLMClient
from .tools.executor import ToolExecutor, CommandSecurityError
from .tools.schemas import get_tool_schemas
from .prompts import get_system_message
from .config import settings
import json
import logging

logger = logging.getLogger(__name__)


class Agent:
    """Agent with tool calling capabilities and strict security policies."""

    def __init__(self, max_iterations: int = 10):
        """
        Initialize agent with security-first approach.

        Args:
            max_iterations: Maximum tool calling iterations before giving up
        """
        self.llm = LLMClient()
        self.executor = ToolExecutor(settings.max_execution_time, strict_mode=True)
        self.tool_schemas = get_tool_schemas()
        self.max_iterations = max_iterations
        self.system_message = get_system_message()

    def run(self, user_message: str) -> Dict[str, Any]:
        """
        Run agent loop until final response or max iterations.

        Args:
            user_message: User input message to process

        Returns:
            Dictionary containing complete execution details:
                - response: Final assistant response
                - iterations: Number of iterations completed
                - usage: Token usage statistics
                - tool_calls_summary: Summary of all tool calls made
                - execution_log: Detailed log of each step
                - error: Error message if any
        """
        # Start with system message for security context
        messages = [self.system_message, {"role": "user", "content": user_message}]
        execution_log = []
        all_tool_calls = []
        iteration = 0

        logger.info(f"Starting agent run with system message: {self.system_message['content'][:200]}...")

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}: Sending request to vLLM")

            # Get LLM response
            response = self.llm.chat_completion(
                messages=messages, tools=self.tool_schemas
            )

            logger.info(f"Iteration {iteration}: Got response, tool_calls={response['tool_calls'] is not None}")

            # Log the response
            execution_log.append({
                "step": iteration,
                "type": "llm_response",
                "content": response["content"],
                "has_tool_calls": response["tool_calls"] is not None,
                "finish_reason": response["finish_reason"],
            })

            # Check for tool calls
            if response["tool_calls"]:
                for tool_call in response["tool_calls"]:
                    tool_call_info = {
                        "step": iteration,
                        "type": "tool_call",
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                        "result": None,
                        "error": None,
                        "security_violation": False,
                    }

                    try:
                        result = self._execute_tool(tool_call)
                        tool_call_info["result"] = result
                        logger.info(f"Tool {tool_call.function.name} executed successfully")
                    except CommandSecurityError as e:
                        # Security violation - don't execute, return error
                        tool_call_info["error"] = str(e)
                        tool_call_info["security_violation"] = True
                        tool_call_info["result"] = {
                            "success": False,
                            "security_violation": True,
                            "error": str(e),
                        }
                        logger.warning(f"Security violation blocked: {e}")

                    all_tool_calls.append(tool_call_info)
                    execution_log.append(tool_call_info)

                    # Add tool result to messages
                    messages.append(
                        {"role": "assistant", "content": response["content"] or ""}
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps(tool_call_info["result"], ensure_ascii=False),
                            "tool_call_id": tool_call.id,
                        }
                    )
            else:
                # No more tool calls, return final response
                logger.info(f"Agent completed after {iteration} iterations")
                return {
                    "response": response["content"],
                    "iterations": iteration,
                    "usage": response["usage"],
                    "tool_calls_summary": all_tool_calls,
                    "execution_log": execution_log,
                    "system_prompt_used": True,  # Confirm system prompt was sent
                }

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return {
            "response": "Max iterations reached",
            "iterations": iteration,
            "usage": {},
            "tool_calls_summary": all_tool_calls,
            "execution_log": execution_log,
            "error": "max_iterations_exceeded",
            "system_prompt_used": True,
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
                command = arguments["command"]
                logger.info(f"Executing bash command: {command}")
                stdout, stderr, returncode = self.executor.execute_bash(command)
                return {
                    "success": returncode == 0,
                    "command": command,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": returncode,
                }

            elif function_name == "execute_python":
                code = arguments["code"]
                logger.info(f"Executing Python code: {code[:100]}...")
                stdout, stderr = self.executor.execute_python(code)
                return {"success": not stderr, "code": code, "stdout": stdout, "stderr": stderr}

            else:
                return {"success": False, "error": f"Unknown function: {function_name}"}

        except CommandSecurityError:
            # Re-raise security errors to be handled by run()
            raise

        except Exception as e:
            return {"success": False, "error": str(e)}
