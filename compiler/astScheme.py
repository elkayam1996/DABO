from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ASTNode:
    """
    One node inside the AST plan.

    This matches the node schema we agreed on.
    Nested fields like task, execution, inputs, and result stay as dict/list
    because the validator will check their exact structure later.
    """

    id: str
    node_type: str
    title: str

    task: dict[str, Any]
    depends_on: list[str]
    execution: dict[str, Any]
    inputs: list[dict[str, Any]]
    suggested_tools: list[str]
    result: dict[str, Any]
    success: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "title": self.title,
            "task": self.task,
            "depends_on": self.depends_on,
            "execution": self.execution,
            "inputs": self.inputs,
            "suggested_tools": self.suggested_tools,
            "result": self.result,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ASTNode":
        return cls(
            id=data["id"],
            node_type=data["node_type"],
            title=data["title"],
            task=data["task"],
            depends_on=data["depends_on"],
            execution=data["execution"],
            inputs=data["inputs"],
            suggested_tools=data["suggested_tools"],
            result=data["result"],
            success=data["success"],
        )


@dataclass
class ASTPlan:
    """
    Full AST plan.

    The plan contains the mission and all AST nodes.
    """

    ast_version: str
    mission: str
    nodes: list[ASTNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ast_version": self.ast_version,
            "mission": self.mission,
            "nodes": [node.to_dict() for node in self.nodes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ASTPlan":
        return cls(
            ast_version=data["ast_version"],
            mission=data["mission"],
            nodes=[
                ASTNode.from_dict(node_data)
                for node_data in data["nodes"]
            ],
        )
