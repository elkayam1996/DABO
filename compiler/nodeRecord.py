from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass
class RuntimeNodeRecord:
    """
    Runtime record returned after one node finishes.

    This is not the plan.
    This is what actually happened after executing one AST node.
    """

    node_id: str
    status: str
    output_key: str | None
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "status": self.status,
            "output_key": self.output_key,
            "output": self.output,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeNodeRecord":
        return cls(
            node_id=data["node_id"],
            status=data["status"],
            output_key=data.get("output_key"),
            output=data.get("output", {}),
            errors=data.get("errors", []),
        )
