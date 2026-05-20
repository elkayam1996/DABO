from dataclasses import dataclass
from typing import *

type Vector = list[float]

@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict
    output_schema: dict | None
    embedding: Vector
    callable_ref: Callable

    def to_header(self) -> dict[str, Any]:
        """
        Small public description used by the LLM/tool selector.

        We do NOT expose the whole source code here by default.
        The LLM usually needs the name, description, and arguments.
        """

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }

# class ToolRegistry():
#     def __init__(self)-> None:
#         self.tool_list: list[ToolSpec] = []
#
#     def add_tool(self, spec: ToolSpec) -> None:
#         self.tool_list.append(spec)
#
#     def get_headers(self) -> dict[str, Any]:
#         tools_headers: dict[str, Any] = {}
#         for tool in self.tool_list:
#             tools_headers[tool.name] = tool.to_header()
#         return tools_headers
#
#     def get_tool(self, name: str) -> ToolSpec:
#         for tool in self.tool_list:
#             if tool.name == name:
#                 return tool
#             else:
#                 raise ValueError(f"Tool {name} doesn't exist")

