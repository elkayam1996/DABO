from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ASTViolation:
    """One problem found in the AST."""

    node_id: str | None
    field: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "field": self.field,
            "message": self.message,
        }


class ASTValidator:
    """Validate raw AST JSON/dict before building ASTPlan / ASTNode objects."""

    def __init__(self, available_local_tools: list[str] | str):
        self.available_local_tools = set(
            self._extract_tool_names(available_local_tools)
        )

        self.valid_ast_version = "0.4"

        self.allowed_node_types = {
            "ACTION",
            "GROUP",
            "VERIFY",
            "APPROVAL",
        }

        self.allowed_execution_modes = {
            "ATOMIC",
            "SEQUENCE",
            "PARALLEL",
            "IF",
            "FORALL",
        }

        self.allowed_input_sources = {
            "NODE_RESULT",
            "MISSION",
            "LOOP_ITEM",
            "CONSTANT",
            "USER",
        }

        self.required_node_fields = [
            "id",
            "node_type",
            "title",
            "task",
            "depends_on",
            "execution",
            "inputs",
            "suggested_tools",
            "result",
            "success",
        ]

        self.required_input_fields = [
            "name",
            "source",
            "from_node",
            "key",
            "value",
        ]

    # =========================
    # PUBLIC API
    # =========================

    def validate(self, raw_ast: str | dict[str, Any]) -> dict[str, Any]:
        """
        Validate raw AST.

        raw_ast can be:
        - JSON string from cloud model
        - already parsed dictionary

        Returns dictionary:
        {
            "ok": bool,
            "ast_dict": dict | None,
            "violations": list[dict],
            "feedback": str
        }
        """

        violations: list[ASTViolation] = []

        ast_dict = self._parse_ast(raw_ast, violations)

        if ast_dict is None:
            return self._make_result(
                ast_dict=None,
                violations=violations,
            )

        self._validate_root(ast_dict, violations)

        raw_nodes = ast_dict.get("nodes")

        if not isinstance(raw_nodes, list):
            return self._make_result(
                ast_dict=ast_dict,
                violations=violations,
            )

        node_by_id = self._make_node_map(raw_nodes, violations)

        self._validate_required_node_fields(raw_nodes, violations)
        self._validate_basic_node_fields(raw_nodes, violations)
        self._validate_task_fields(raw_nodes, violations)
        self._validate_execution_fields(raw_nodes, violations)
        self._validate_execution_references(raw_nodes, node_by_id, violations)
        self._validate_dependencies(raw_nodes, node_by_id, violations)
        self._validate_inputs(raw_nodes, node_by_id, violations)
        self._validate_suggested_tools(raw_nodes, violations)
        self._validate_result_fields(raw_nodes, violations)
        self._validate_duplicate_result_keys(raw_nodes, violations)
        self._validate_success_fields(raw_nodes, violations)
        self._validate_dependency_cycles(raw_nodes, node_by_id, violations)

        return self._make_result(
            ast_dict=ast_dict,
            violations=violations,
        )

    # =========================
    # RESULT HELPERS
    # =========================

    def _make_result(
        self,
        ast_dict: dict[str, Any] | None,
        violations: list[ASTViolation],
    ) -> dict[str, Any]:
        return {
            "ok": len(violations) == 0,
            "ast_dict": ast_dict,
            "violations": [
                violation.to_dict()
                for violation in violations
            ],
            "feedback": self._violations_to_feedback_text(violations),
        }

    def _violations_to_feedback_text(
        self,
        violations: list[ASTViolation],
    ) -> str:
        if len(violations) == 0:
            return "AST is valid."

        lines = ["AST validation failed. Fix these problems:"]

        for i, violation in enumerate(violations, start=1):
            node_id = violation.node_id if violation.node_id is not None else "GLOBAL"

            lines.append(
                f"{i}. node={node_id}, field={violation.field}, error={violation.message}"
            )

        return "\n".join(lines)

    # =========================
    # SMALL HELPERS
    # =========================

    def _add_violation(
        self,
        violations: list[ASTViolation],
        node_id: str | None,
        field: str,
        message: str,
    ) -> None:
        violations.append(
            ASTViolation(
                node_id=node_id,
                field=field,
                message=message,
            )
        )

    def _extract_tool_names(self, available_local_tools: list[str] | str) -> list[str]:
        """
        Supports:
        - list[str]
        - text from ToolRegistry.get_available_tools()

        Expected text examples:
        - read_file: read text content from a file
        read_file: read text content from a file
        """

        if isinstance(available_local_tools, list):
            return available_local_tools

        tool_names = []

        for line in available_local_tools.splitlines():
            line = line.strip()

            if line.startswith("-"):
                line = line[1:].strip()

            if not line:
                continue

            if ":" in line:
                tool_name = line.split(":", 1)[0].strip()
            else:
                tool_name = line.split()[0].strip()

            if tool_name:
                tool_names.append(tool_name)

        return tool_names

    def _get_node_id(self, node: dict[str, Any]) -> str | None:
        node_id = node.get("id")

        if isinstance(node_id, str):
            return node_id

        return None

    # =========================
    # PARSE
    # =========================

    def _parse_ast(
        self,
        raw_ast: str | dict[str, Any],
        violations: list[ASTViolation],
    ) -> dict[str, Any] | None:
        """Parse JSON string into dictionary."""

        if isinstance(raw_ast, dict):
            return raw_ast

        if not isinstance(raw_ast, str):
            self._add_violation(
                violations=violations,
                node_id=None,
                field="root",
                message="AST must be a JSON string or dictionary.",
            )
            return None

        try:
            return json.loads(raw_ast)
        except json.JSONDecodeError as e:
            self._add_violation(
                violations=violations,
                node_id=None,
                field="json",
                message=f"Invalid JSON: {e}",
            )
            return None

    # =========================
    # ROOT VALIDATION
    # =========================

    def _validate_root(
        self,
        ast_dict: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        """Validate root AST fields."""

        self._validate_root_version(ast_dict, violations)
        self._validate_root_mission(ast_dict, violations)
        self._validate_root_nodes(ast_dict, violations)

    def _validate_root_version(
        self,
        ast_dict: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        if ast_dict.get("ast_version") != self.valid_ast_version:
            self._add_violation(
                violations=violations,
                node_id=None,
                field="ast_version",
                message=f'ast_version must be "{self.valid_ast_version}".',
            )

    def _validate_root_mission(
        self,
        ast_dict: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        mission = ast_dict.get("mission")

        if not isinstance(mission, str) or mission.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=None,
                field="mission",
                message="mission must be a non-empty string.",
            )

    def _validate_root_nodes(
        self,
        ast_dict: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        nodes = ast_dict.get("nodes")

        if not isinstance(nodes, list):
            self._add_violation(
                violations=violations,
                node_id=None,
                field="nodes",
                message="nodes must be a list.",
            )
            return

        if len(nodes) == 0:
            self._add_violation(
                violations=violations,
                node_id=None,
                field="nodes",
                message="nodes must not be empty.",
            )

    # =========================
    # NODE MAP
    # =========================

    def _make_node_map(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> dict[str, dict[str, Any]]:
        """Create node_id -> node dictionary."""

        node_by_id = {}

        for raw_node in raw_nodes:
            if not isinstance(raw_node, dict):
                continue

            node_id = raw_node.get("id")

            if not isinstance(node_id, str) or node_id.strip() == "":
                continue

            if node_id in node_by_id:
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field="id",
                    message="Duplicate node id.",
                )
            else:
                node_by_id[node_id] = raw_node

        return node_by_id

    # =========================
    # REQUIRED NODE FIELDS
    # =========================

    def _validate_required_node_fields(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check every node has all required fields."""

        for raw_node in raw_nodes:
            if not isinstance(raw_node, dict):
                self._add_violation(
                    violations=violations,
                    node_id=None,
                    field="node",
                    message="Every node must be a dictionary.",
                )
                continue

            node_id = self._get_node_id(raw_node)

            for field_name in self.required_node_fields:
                if field_name not in raw_node:
                    self._add_violation(
                        violations=violations,
                        node_id=node_id,
                        field=field_name,
                        message=f"Missing required field: {field_name}",
                    )

    # =========================
    # BASIC NODE FIELDS
    # =========================

    def _validate_basic_node_fields(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check id, node_type, title and list fields."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            self._validate_node_id(node, violations)
            self._validate_node_type(node, violations)
            self._validate_node_title(node, violations)
            self._validate_node_list_fields(node, violations)

    def _validate_node_id(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = node.get("id")

        if not isinstance(node_id, str) or node_id.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=None,
                field="id",
                message="Node id must be a non-empty string.",
            )

    def _validate_node_type(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        node_type = node.get("node_type")

        if not isinstance(node_type, str):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="node_type",
                message="node_type must be a string.",
            )
            return

        if node_type not in self.allowed_node_types:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="node_type",
                message=f"Invalid node_type: {node_type}",
            )

    def _validate_node_title(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        title = node.get("title")

        if not isinstance(title, str) or title.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="title",
                message="title must be a non-empty string.",
            )

    def _validate_node_list_fields(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        for field_name in ["depends_on", "inputs", "suggested_tools", "success"]:
            value = node.get(field_name)

            if not isinstance(value, list):
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field=field_name,
                    message=f"{field_name} must be a list.",
                )

    # =========================
    # TASK VALIDATION
    # =========================

    def _validate_task_fields(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check task objective, steps and constraints."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            self._validate_task_shape(node, violations)
            self._validate_task_objective(node, violations)
            self._validate_task_steps(node, violations)
            self._validate_task_constraints(node, violations)

    def _validate_task_shape(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if not isinstance(node.get("task"), dict):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="task",
                message="task must be a dictionary.",
            )

    def _validate_task_objective(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        task = node.get("task")

        if not isinstance(task, dict):
            return

        objective = task.get("objective")

        if not isinstance(objective, str) or objective.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="task.objective",
                message="task.objective must be a non-empty string.",
            )

    def _validate_task_steps(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        node_type = node.get("node_type")
        task = node.get("task")

        if not isinstance(task, dict):
            return

        steps = task.get("steps")

        if not isinstance(steps, list):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="task.steps",
                message="task.steps must be a list.",
            )
            return

        if node_type == "ACTION" and len(steps) == 0:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="task.steps",
                message="ACTION nodes should have non-empty task.steps.",
            )

    def _validate_task_constraints(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        task = node.get("task")

        if not isinstance(task, dict):
            return

        constraints = task.get("constraints")

        if not isinstance(constraints, list):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="task.constraints",
                message="task.constraints must be a list. Use [] if none.",
            )

    # =========================
    # EXECUTION VALIDATION
    # =========================

    def _validate_execution_fields(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check execution mode and mode-specific fields."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            self._validate_execution_shape(node, violations)
            self._validate_execution_mode(node, violations)
            self._validate_execution_compatibility(node, violations)
            self._validate_execution_mode_fields(node, violations)

    def _validate_execution_shape(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if not isinstance(node.get("execution"), dict):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution",
                message="execution must be a dictionary.",
            )

    def _validate_execution_mode(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        execution = node.get("execution")

        if not isinstance(execution, dict):
            return

        mode = execution.get("mode")

        if not isinstance(mode, str):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.mode",
                message="execution.mode must be a string.",
            )
            return

        if mode not in self.allowed_execution_modes:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.mode",
                message=f"Invalid execution mode: {mode}",
            )

    def _validate_execution_compatibility(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check node_type and execution.mode fit together."""

        node_id = self._get_node_id(node)
        node_type = node.get("node_type")
        execution = node.get("execution")

        if not isinstance(execution, dict):
            return

        mode = execution.get("mode")

        if node_type in {"ACTION", "VERIFY", "APPROVAL"} and mode != "ATOMIC":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.mode",
                message=f"{node_type} nodes must use ATOMIC execution.",
            )

        if node_type == "GROUP" and mode == "ATOMIC":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.mode",
                message="GROUP nodes cannot use ATOMIC execution.",
            )

    def _validate_execution_mode_fields(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        execution = node.get("execution")

        if not isinstance(execution, dict):
            return

        mode = execution.get("mode")

        if mode in {"SEQUENCE", "PARALLEL"}:
            self._validate_children_field(node, violations)

        elif mode == "IF":
            self._validate_if_fields(node, violations)

        elif mode == "FORALL":
            self._validate_forall_fields(node, violations)

    def _validate_children_field(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        children = node.get("execution", {}).get("children")

        if not isinstance(children, list):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.children",
                message="children must be a list.",
            )
            return

        if len(children) == 0:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.children",
                message="children must not be empty.",
            )

    def _validate_if_fields(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        execution = node.get("execution", {})

        condition = execution.get("condition")
        then_branch = execution.get("then")
        else_branch = execution.get("else")

        if not isinstance(condition, str) or condition.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.condition",
                message="IF execution must have a non-empty condition.",
            )

        if not isinstance(then_branch, list):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.then",
                message="IF execution must have then as a list.",
            )
        elif len(then_branch) == 0:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.then",
                message="IF execution then list should not be empty.",
            )

        if not isinstance(else_branch, list):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.else",
                message="IF execution must have else as a list. Use [] if none.",
            )

    def _validate_forall_fields(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        execution = node.get("execution", {})

        item = execution.get("item")
        collection = execution.get("collection")
        do_nodes = execution.get("do")

        if not isinstance(item, str) or item.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.item",
                message="FORALL execution must have non-empty item.",
            )

        if not isinstance(collection, str) or collection.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.collection",
                message="FORALL execution must have non-empty collection.",
            )

        if not isinstance(do_nodes, list):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.do",
                message="FORALL execution must have do as a list.",
            )
        elif len(do_nodes) == 0:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="execution.do",
                message="FORALL execution do list must not be empty.",
            )

    # =========================
    # REFERENCES
    # =========================

    def _validate_execution_references(
        self,
        raw_nodes: list[Any],
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        """Check children / then / else / do point to existing nodes."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            execution = node.get("execution")

            if not isinstance(execution, dict):
                continue

            mode = execution.get("mode")

            if mode in {"SEQUENCE", "PARALLEL"}:
                self._validate_reference_list(
                    node=node,
                    field_name="execution.children",
                    refs=execution.get("children", []),
                    node_by_id=node_by_id,
                    violations=violations,
                )

            elif mode == "IF":
                self._validate_reference_list(
                    node=node,
                    field_name="execution.then",
                    refs=execution.get("then", []),
                    node_by_id=node_by_id,
                    violations=violations,
                )
                self._validate_reference_list(
                    node=node,
                    field_name="execution.else",
                    refs=execution.get("else", []),
                    node_by_id=node_by_id,
                    violations=violations,
                )

            elif mode == "FORALL":
                self._validate_reference_list(
                    node=node,
                    field_name="execution.do",
                    refs=execution.get("do", []),
                    node_by_id=node_by_id,
                    violations=violations,
                )

    def _validate_reference_list(
        self,
        node: dict[str, Any],
        field_name: str,
        refs: Any,
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if not isinstance(refs, list):
            return

        for ref_id in refs:
            if not isinstance(ref_id, str):
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field=field_name,
                    message="Referenced node id must be a string.",
                )
                continue

            if ref_id not in node_by_id:
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field=field_name,
                    message=f"Referenced node does not exist: {ref_id}",
                )

            if ref_id == node_id:
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field=field_name,
                    message="Node cannot reference itself.",
                )

    # =========================
    # DEPENDENCIES
    # =========================

    def _validate_dependencies(
        self,
        raw_nodes: list[Any],
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        """Check depends_on references if there are dependencies."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            depends_on = node.get("depends_on")

            if not isinstance(depends_on, list):
                continue

            for dep_id in depends_on:
                self._validate_single_dependency(
                    node=node,
                    dep_id=dep_id,
                    node_by_id=node_by_id,
                    violations=violations,
                )

    def _validate_single_dependency(
        self,
        node: dict[str, Any],
        dep_id: Any,
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if not isinstance(dep_id, str):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="depends_on",
                message="Dependency id must be a string.",
            )
            return

        if dep_id not in node_by_id:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="depends_on",
                message=f"Dependency node does not exist: {dep_id}",
            )

        if dep_id == node_id:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="depends_on",
                message="Node cannot depend on itself.",
            )

    def _validate_dependency_cycles(
        self,
        raw_nodes: list[Any],
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        """Detect cycles in depends_on."""

        visited = set()
        visiting = set()

        def dfs(node_id: str):
            if node_id in visiting:
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field="depends_on",
                    message="Dependency cycle detected.",
                )
                return

            if node_id in visited:
                return

            visiting.add(node_id)

            node = node_by_id.get(node_id)

            if node is not None:
                depends_on = node.get("depends_on", [])

                if isinstance(depends_on, list):
                    for dep_id in depends_on:
                        if isinstance(dep_id, str) and dep_id in node_by_id:
                            dfs(dep_id)

            visiting.remove(node_id)
            visited.add(node_id)

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            node_id = self._get_node_id(node)

            if node_id is not None:
                dfs(node_id)

    # =========================
    # INPUTS
    # =========================

    def _validate_inputs(
        self,
        raw_nodes: list[Any],
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        """Validate input objects."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            inputs = node.get("inputs")

            if not isinstance(inputs, list):
                continue

            for input_obj in inputs:
                self._validate_input_object(node, input_obj, node_by_id, violations)

    def _validate_input_object(
        self,
        node: dict[str, Any],
        input_obj: Any,
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if not isinstance(input_obj, dict):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs",
                message="Every input must be a dictionary.",
            )
            return

        self._validate_input_required_fields(node, input_obj, violations)
        self._validate_input_basic_fields(node, input_obj, violations)
        self._validate_input_source_rules(node, input_obj, node_by_id, violations)

    def _validate_input_required_fields(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        for field_name in self.required_input_fields:
            if field_name not in input_obj:
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field=f"inputs.{field_name}",
                    message=f"Missing input field: {field_name}",
                )

    def _validate_input_basic_fields(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        name = input_obj.get("name")
        source = input_obj.get("source")
        key = input_obj.get("key")

        if not isinstance(name, str) or name.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.name",
                message="Input name must be a non-empty string.",
            )

        if source not in self.allowed_input_sources:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.source",
                message=f"Invalid input source: {source}",
            )

        if not isinstance(key, str) or key.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.key",
                message="Input key must be a non-empty string.",
            )

    def _validate_input_source_rules(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        source = input_obj.get("source")

        if source == "NODE_RESULT":
            self._validate_node_result_input(node, input_obj, node_by_id, violations)

        elif source == "CONSTANT":
            self._validate_constant_input(node, input_obj, violations)

        elif source == "MISSION":
            self._validate_mission_input(node, input_obj, violations)

        elif source == "LOOP_ITEM":
            self._validate_loop_item_input(node, input_obj, node_by_id, violations)

        elif source == "USER":
            self._validate_user_input(node, input_obj, violations)

    def _validate_node_result_input(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        from_node = input_obj.get("from_node")
        key = input_obj.get("key")

        if not isinstance(from_node, str) or from_node.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message="NODE_RESULT input must have from_node.",
            )
            return

        if from_node not in node_by_id:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message=f"Input from_node does not exist: {from_node}",
            )
            return

        source_node = node_by_id[from_node]
        source_result = source_node.get("result")

        if not isinstance(source_result, dict):
            return

        source_key = source_result.get("key")

        if source_key != key:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.key",
                message=(
                    f"NODE_RESULT input key '{key}' does not match "
                    f"result.key of node {from_node}: '{source_key}'"
                ),
            )

    def _validate_constant_input(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if input_obj.get("from_node") is not None:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message="CONSTANT input should have from_node as null.",
            )

        if input_obj.get("value") is None:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.value",
                message="CONSTANT input should have a non-null value.",
            )

    def _validate_mission_input(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if input_obj.get("from_node") is not None:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message="MISSION input should have from_node as null.",
            )

    def _validate_loop_item_input(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        node_by_id: dict[str, dict[str, Any]],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        from_node = input_obj.get("from_node")
        key = input_obj.get("key")

        if not isinstance(from_node, str) or from_node.strip() == "":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message="LOOP_ITEM input should point to a FORALL group node.",
            )
            return

        if from_node not in node_by_id:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message=f"LOOP_ITEM from_node does not exist: {from_node}",
            )
            return

        loop_node = node_by_id[from_node]
        loop_execution = loop_node.get("execution")

        if not isinstance(loop_execution, dict):
            return

        if loop_execution.get("mode") != "FORALL":
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message="LOOP_ITEM from_node must point to a FORALL node.",
            )
            return

        loop_item = loop_execution.get("item")

        if key != loop_item:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.key",
                message=f"LOOP_ITEM key must match FORALL item: {loop_item}",
            )

    def _validate_user_input(
        self,
        node: dict[str, Any],
        input_obj: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if input_obj.get("from_node") is not None:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="inputs.from_node",
                message="USER input should have from_node as null.",
            )

    # =========================
    # TOOLS
    # =========================

    def _validate_suggested_tools(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check suggested tools exist in local tool list."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            suggested_tools = node.get("suggested_tools")

            if not isinstance(suggested_tools, list):
                continue

            for tool_name in suggested_tools:
                self._validate_single_suggested_tool(node, tool_name, violations)

    def _validate_single_suggested_tool(
        self,
        node: dict[str, Any],
        tool_name: Any,
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if not isinstance(tool_name, str):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="suggested_tools",
                message="Tool name must be a string.",
            )
            return

        if tool_name not in self.available_local_tools:
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="suggested_tools",
                message=f"Unknown local tool: {tool_name}",
            )

    # =========================
    # RESULT
    # =========================

    def _validate_result_fields(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check result key, description and must_include."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            self._validate_result_shape(node, violations)
            self._validate_result_key(node, violations)
            self._validate_result_description(node, violations)
            self._validate_result_must_include(node, violations)

    def _validate_result_shape(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)

        if not isinstance(node.get("result"), dict):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="result",
                message="result must be a dictionary.",
            )

    def _validate_result_key(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        result = node.get("result")

        if not isinstance(result, dict):
            return

        result_key = result.get("key")

        if result_key is not None and not isinstance(result_key, str):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="result.key",
                message="result.key must be a string or null.",
            )

    def _validate_result_description(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        result = node.get("result")

        if not isinstance(result, dict):
            return

        description = result.get("description")

        if not isinstance(description, str):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="result.description",
                message="result.description must be a string.",
            )

    def _validate_result_must_include(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        result = node.get("result")

        if not isinstance(result, dict):
            return

        must_include = result.get("must_include")

        if not isinstance(must_include, list):
            self._add_violation(
                violations=violations,
                node_id=node_id,
                field="result.must_include",
                message="result.must_include must be a list.",
            )

    def _validate_duplicate_result_keys(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """result.key should be unique when not null."""

        seen_keys = {}

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            node_id = self._get_node_id(node)
            result = node.get("result")

            if not isinstance(result, dict):
                continue

            result_key = result.get("key")

            if result_key is None:
                continue

            if not isinstance(result_key, str):
                continue

            if result_key in seen_keys:
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field="result.key",
                    message=(
                        f"Duplicate result.key '{result_key}'. "
                        f"Already used by node {seen_keys[result_key]}."
                    ),
                )
            else:
                seen_keys[result_key] = node_id

    # =========================
    # SUCCESS
    # =========================

    def _validate_success_fields(
        self,
        raw_nodes: list[Any],
        violations: list[ASTViolation],
    ) -> None:
        """Check success list."""

        for node in raw_nodes:
            if not isinstance(node, dict):
                continue

            success = node.get("success")

            if not isinstance(success, list):
                continue

            self._validate_success_items(node, violations)
            self._validate_success_not_empty(node, violations)

    def _validate_success_items(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        success = node.get("success", [])

        if not isinstance(success, list):
            return

        for item in success:
            if not isinstance(item, str):
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field="success",
                    message="Every success item must be a string.",
                )

    def _validate_success_not_empty(
        self,
        node: dict[str, Any],
        violations: list[ASTViolation],
    ) -> None:
        node_id = self._get_node_id(node)
        node_type = node.get("node_type")
        success = node.get("success", [])

        if node_type in {"ACTION", "VERIFY", "APPROVAL"}:
            if isinstance(success, list) and len(success) == 0:
                self._add_violation(
                    violations=violations,
                    node_id=node_id,
                    field="success",
                    message=f"{node_type} nodes should have non-empty success list.",
                )