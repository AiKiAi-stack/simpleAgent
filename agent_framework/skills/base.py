"""Skill base class for composable tool collections."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json

from ..tools.base import Tool


class Skill(Tool, ABC):
    """
    A Skill is a composable collection of tools that work together.

    Skills differ from Tools in that they:
    - Combine multiple tools to accomplish complex tasks
    - Can have custom prompts/templates for specific domains
    - May orchestrate multi-step workflows

    Example:
        class ResearchSkill(Skill):
            \"\"\"Search and synthesize information.\"\"\"

            def __init__(self):
                super().__init__(
                    name="research",
                    tools=[SearchTool(), SummarizeTool()],
                    prompt_template="..."
                )
    """

    def __init__(
        self,
        name: str,
        description: str,
        tools: List[Tool],
        prompt_template: Optional[str] = None,
    ):
        """
        Initialize a skill.

        Args:
            name: Unique identifier for the skill
            description: Human-readable description
            tools: List of tools this skill can use
            prompt_template: Optional prompt template for the skill
        """
        self._name = name
        self._description = description
        self._tools = {tool.name: tool for tool in tools}
        self._prompt_template = prompt_template

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The task to accomplish",
                },
                "context": {
                    "type": "string",
                    "description": "Optional context or additional information",
                },
            },
            "required": ["task"],
        }

    @property
    def tools(self) -> Dict[str, Tool]:
        """Get the tools available to this skill."""
        return self._tools.copy()

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the skill with provided arguments.

        Skills orchestrate their internal tools to accomplish tasks.

        Args:
            **kwargs: Skill-specific arguments

        Returns:
            Skill execution result
        """
        pass

    def _parse_plan(self, response: str) -> List[tuple[str, Dict]]:
        """
        Parse a plan string into tool calls.

        Expected format:
            Tool: tool_name
            Args:
                key: value

        Args:
            response: LLM response containing tool calls

        Returns:
            List of (tool_name, args) tuples
        """
        calls = []
        lines = response.strip().split("\n")
        current_tool = None
        current_args = {}

        for line in lines:
            line = line.strip()
            if line.startswith("Tool:"):
                if current_tool:
                    calls.append((current_tool, current_args))
                current_tool = line.replace("Tool:", "").strip()
                current_args = {}
            elif line.startswith("Args:"):
                continue
            elif ":" in line and current_tool:
                key, value = line.split(":", 1)
                current_args[key.strip()] = value.strip()

        if current_tool:
            calls.append((current_tool, current_args))

        return calls

    def _aggregate(self, results: List[Any]) -> Dict[str, Any]:
        """
        Aggregate multiple tool results.

        Args:
            results: List of tool execution results

        Returns:
            Aggregated result
        """
        return {
            "results": results,
            "tool_count": len(results),
        }


class SimpleSkill(Skill):
    """
    A simple skill that wraps a single tool.

    Useful for adding metadata or pre/post-processing to existing tools.
    """

    def __init__(
        self,
        name: str,
        tool: Tool,
        description: Optional[str] = None,
        preprocessor: Optional[callable] = None,
        postprocessor: Optional[callable] = None,
    ):
        super().__init__(
            name=name,
            description=description or f"Skill wrapper for {tool.name}",
            tools=[tool],
        )
        self._tool = tool
        self._preprocessor = preprocessor
        self._postprocessor = postprocessor

    async def execute(self, **kwargs) -> Any:
        """Execute the wrapped tool with optional pre/post-processing."""
        if self._preprocessor:
            kwargs = self._preprocessor(kwargs)

        result = await self._tool.execute(**kwargs)

        if self._postprocessor:
            result = self._postprocessor(result)

        return result
