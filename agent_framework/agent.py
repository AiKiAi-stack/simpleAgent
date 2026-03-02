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
        """
        # Start with system message for security context
        messages = [self.system_message, {"role": "user", "content": user_message}]
        execution_log = []
        all_tool_calls = []
        iteration = 0

        logger.info(f"Starting agent run with system message: {self.system_message['content'][:200]}...")
        logger.info(f"User message: {user_message}")

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteration {iteration}/{self.max_iterations}: Sending request to vLLM")
            logger.info(f"Messages count: {len(messages)}")

            # Get LLM response
            response = self.llm.chat_completion(
                messages=messages, tools=self.tool_schemas
            )

            logger.info(f"Got response from vLLM")
            logger.info(f"  - Content: {response['content'][:100] if response['content'] else 'None'}...")
            logger.info(f"  - Tool calls: {response['tool_calls']}")
            logger.info(f"  - Tool calls type: {type(response['tool_calls'])}")
            logger.info(f"  - Tool calls is not None: {response['tool_calls'] is not None}")
            logger.info(f"  - Tool calls bool: {bool(response['tool_calls']) if response['tool_calls'] is not None else 'N/A'}")
            logger.info(f"  - Finish reason: {response['finish_reason']}")

            # Log the response
            execution_log.append({
                "step": iteration,
                "type": "llm_response",
                "content": response["content"],
                "has_tool_calls": response["tool_calls"] is not None,
                "finish_reason": response["finish_reason"],
            })

            # Check for tool calls - handle both None and empty list
            has_tool_calls = response["tool_calls"] is not None and len(response["tool_calls"]) > 0
            logger.info(f"Has tool calls to process: {has_tool_calls}")

            if has_tool_calls:
                logger.info(f"Processing {len(response['tool_calls'])} tool call(s)...")
                
                for idx, tool_call in enumerate(response["tool_calls"]):
                    logger.info(f"\n  Tool call {idx + 1}/{len(response['tool_calls'])}:")
                    logger.info(f"    - ID: {tool_call.id}")
                    logger.info(f"    - Type: {type(tool_call)}")
                    logger.info(f"    - Function: {tool_call.function}")
                    logger.info(f"    - Function name: {tool_call.function.name}")
                    logger.info(f"    - Function arguments: {tool_call.function.arguments}")
                    
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
                        logger.info(f"    - Executing tool: {tool_call.function.name}")
                        result = self._execute_tool(tool_call)
                        tool_call_info["result"] = result
                        logger.info(f"    - Execution result: success={result.get('success', False)}")
                        
                        if result.get('security_violation'):
                            logger.warning(f"    - Security violation: {result.get('error', 'Unknown')[:100]}")
                        
                    except CommandSecurityError as e:
                        # Security violation - don't execute, return error
                        tool_call_info["error"] = str(e)
                        tool_call_info["security_violation"] = True
                        tool_call_info["result"] = {
                            "success": False,
                            "security_violation": True,
                            "error": str(e),
                        }
                        logger.warning(f"    - Security violation blocked: {e}")
                    except Exception as e:
                        logger.exception(f"    - Execution error: {e}")
                        tool_call_info["error"] = str(e)
                        tool_call_info["result"] = {
                            "success": False,
                            "error": str(e),
                        }

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
                    logger.info(f"    - Added tool result to messages")
                
                logger.info(f"Finished processing all tool calls, continuing to next iteration...")
                # Continue to next iteration to get LLM response with tool results
            else:
                # No more tool calls, return final response
                logger.info(f"\n{'='*60}")
                logger.info(f"Agent completed after {iteration} iterations - no more tool calls")
                logger.info(f"Final response: {response['content'][:200] if response['content'] else 'None'}...")
                return {
                    "response": response["content"],
                    "iterations": iteration,
                    "usage": response["usage"],
                    "tool_calls_summary": all_tool_calls,
                    "execution_log": execution_log,
                    "system_prompt_used": True,
                }

        # Max iterations reached
        logger.warning(f"\n{'='*60}")
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
        """
        function_name = tool_call.function.name
        arguments_str = tool_call.function.arguments
        
        logger.info(f"    - Parsing arguments: {arguments_str[:100]}...")
        
        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            logger.error(f"    - Failed to parse arguments: {e}")
            return {"success": False, "error": f"Invalid JSON arguments: {str(e)}"}

        try:
            if function_name == "execute_bash":
                command = arguments.get("command", "")
                logger.info(f"    - Executing bash command: {command}")
                stdout, stderr, returncode = self.executor.execute_bash(command)
                logger.info(f"    - Command return code: {returncode}")
                logger.info(f"    - Stdout: {stdout[:100] if stdout else 'empty'}...")
                logger.info(f"    - Stderr: {stderr[:100] if stderr else 'empty'}...")
                return {
                    "success": returncode == 0,
                    "command": command,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": returncode,
                }

            elif function_name == "execute_python":
                code = arguments.get("code", "")
                logger.info(f"    - Executing Python code: {code[:100]}...")
                stdout, stderr = self.executor.execute_python(code)
                logger.info(f"    - Python stdout: {stdout[:100] if stdout else 'empty'}...")
                logger.info(f"    - Python stderr: {stderr[:100] if stderr else 'empty'}...")
                return {"success": not stderr, "code": code, "stdout": stdout, "stderr": stderr}

            else:
                logger.error(f"    - Unknown function: {function_name}")
                return {"success": False, "error": f"Unknown function: {function_name}"}

        except CommandSecurityError:
            # Re-raise security errors to be handled by run()
            raise

        except Exception as e:
            logger.exception(f"    - Execution error: {e}")
            return {"success": False, "error": str(e)}
