"""Tool registry for function calling."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable
    requires_confirmation: bool = False


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tools_schema(self) -> list[dict[str, Any]]:
        schemas = []
        for tool in self.tools.values():
            schemas.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": {
                        "type": "object",
                        "properties": tool.parameters.get("properties", {}),
                        "required": tool.parameters.get("required", []),
                    },
                }
            )
        return schemas

    async def execute(self, name: str, args: dict[str, Any]) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        tool = self.tools[name]
        if asyncio.iscoroutinefunction(tool.function):
            return await tool.function(**args)
        return tool.function(**args)


import asyncio

registry = ToolRegistry()
