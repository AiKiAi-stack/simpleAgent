"""ReAct Agent core implementation with separated Reason/Act/Observe loop."""

from typing import Any, Dict, List, Optional
import json
import time

from ..core.message import Message, AgentResponse, ToolResult
from ..core.config import settings
from ..llm.base import LLM, LLMResponse
from ..tools.base import Tool
from ..tools.registry import ToolRegistry


class ReActAgent:
    """
    ReAct (Reason-Act-Observe) Agent implementation.

    The agent loop:
    1. **Reason**: LLM analyzes the situation and decides what to do
    2. **Act**: Execute tool calls based on LLM decision
    3. **Observe**: Feed tool results back to LLM for next iteration

    Example:
        agent = ReActAgent(
            llm=VLLMClient(),
            tools=[BashTool(), PythonTool()],
            max_iterations=10
        )
        response = await agent.run("List files in /tmp")
    """

    def __init__(
        self,
        llm: LLM,
        tools: List[Tool],
        system_prompt: Optional[str] = None,
        max_iterations: int = 10,
    ):
        """
        Initialize ReAct agent.

        Args:
            llm: LLM instance for generating responses
            tools: List of tools available to the agent
            system_prompt: Optional system prompt (uses default if not provided)
            max_iterations: Maximum tool calling iterations before giving up
        """
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.tool_schemas = [tool.to_schema() for tool in tools]
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    async def run(self, user_message: str) -> AgentResponse:
        """
        Run the ReAct loop until final response or max iterations.

        Args:
            user_message: User input message

        Returns:
            AgentResponse with final result
        """
        # Initialize messages with system prompt
        messages = self._init_messages(user_message)
        logs = []
        iteration = 0
        start_time = time.time()

        while iteration < self.max_iterations:
            iteration += 1

            # **Reason**: Get LLM response
            llm_response = await self._reason(messages)
            logs.append({"iteration": iteration, "reason": llm_response})

            # Check if LLM wants to call tools
            if llm_response.has_tool_calls():
                # **Act**: Execute tool calls
                tool_results = await self._act(llm_response.tool_calls)
                logs.append({"iteration": iteration, "act": tool_results})

                # **Observe**: Feed results back to LLM
                observe_messages = self._observe(tool_results, llm_response.tool_calls)
                messages.extend(observe_messages)
                logs.append({"iteration": iteration, "observe": observe_messages})
            else:
                # No tool calls, return final response
                return AgentResponse(
                    response=llm_response.content,
                    logs=logs,
                    usage=llm_response.usage,
                    iterations=iteration,
                )

        # Max iterations reached
        return AgentResponse(
            response="Max iterations reached",
            logs=logs,
            usage={},
            iterations=iteration,
            error="max_iterations_exceeded",
        )

    def _init_messages(self, user_message: str) -> List[Dict[str, str]]:
        """Initialize message list with system prompt and user message."""
        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        else:
            # Build default system prompt with tool info
            tools_info = "\n".join(
                [f"- {name}: {tool.description}" for name, tool in self.tools.items()]
            )
            messages.append(
                {
                    "role": "system",
                    "content": f"You are a helpful assistant with these tools:\n{tools_info}",
                }
            )

        messages.append({"role": "user", "content": user_message})
        return messages

    async def _reason(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """
        Reason step: Get LLM response.

        Args:
            messages: Current conversation messages

        Returns:
            LLMResponse with potential tool calls
        """
        return await self.llm.chat_completion(
            messages=messages,
            tools=self.tool_schemas,
            tool_choice="auto",
        )

    async def _act(self, tool_calls: List[Dict[str, Any]]) -> List[ToolResult]:
        """
        Act step: Execute tool calls.

        Args:
            tool_calls: List of tool calls from LLM

        Returns:
            List of ToolResult objects
        """
        results = []
        for tool_call in tool_calls:
            result = await self._execute_tool_call(tool_call)
            results.append(result)
        return results

    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> ToolResult:
        """
        Execute a single tool call.

        Args:
            tool_call: Tool call dict with id, function name, and arguments

        Returns:
            ToolResult object
        """
        tool_id = tool_call.get("id")
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        arguments_str = function.get("arguments", "{}")

        try:
            arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                stderr=f"Failed to parse arguments: {e}",
                error="Invalid JSON arguments",
            )

        # Get tool from registry
        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                stderr=f"Unknown tool: {tool_name}",
                error=f"Tool '{tool_name}' not found",
            )

        try:
            # Execute tool
            result = await tool.execute(**arguments)

            # Convert result to ToolResult if needed
            if isinstance(result, ToolResult):
                return result
            elif isinstance(result, dict):
                return ToolResult(
                    success=result.get("success", True),
                    stdout=result.get("stdout"),
                    stderr=result.get("stderr"),
                    returncode=result.get("returncode"),
                    data=result,
                )
            else:
                return ToolResult(
                    success=True,
                    data=result,
                )

        except Exception as e:
            return ToolResult(
                success=False,
                stderr=str(e),
                error=f"Tool execution failed: {e}",
            )

    def _observe(
        self, results: List[ToolResult], tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Observe step: Convert tool results to messages.

        Args:
            results: Tool execution results
            tool_calls: Original tool calls (for matching IDs)

        Returns:
            List of message dicts to add to conversation
        """
        messages = []

        for result, tool_call in zip(results, tool_calls):
            tool_call_id = tool_call.get("id")
            message = result.to_message(tool_call_id)
            messages.append(message.to_dict())

        return messages
