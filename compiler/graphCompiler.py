from __future__ import annotations

from typing import Any

from .astScheme import ASTNode, ASTPlan


class GraphCompiler:
    """
    Compile valid AST dict into execution graph data.

    This class assumes the AST was already validated by ASTValidator.
    It does not validate the schema again.
    """

    def compile(self, ast_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Main compile function.

        Input:
        - valid AST dict

        Output:
        - graph dictionary used later by the executor
        """

        ast_plan = ASTPlan.from_dict(ast_dict)

        node_by_id = self._build_node_by_id(ast_plan)
        depends_on = self._build_depends_on(ast_plan)
        reverse_dependencies = self._build_reverse_dependencies(depends_on)
        children_by_node = self._build_children_by_node(ast_plan)
        parent_by_node = self._build_parent_by_node(children_by_node)
        root_nodes = self._find_root_nodes(ast_plan, parent_by_node)

        return {
            "ast_plan": ast_plan,
            "node_by_id": node_by_id,
            "depends_on": depends_on,
            "reverse_dependencies": reverse_dependencies,
            "children_by_node": children_by_node,
            "parent_by_node": parent_by_node,
            "root_nodes": root_nodes,
        }

    def _build_node_by_id(self, ast_plan: ASTPlan) -> dict[str, ASTNode]:
        """Create node_id -> ASTNode."""

        node_by_id = {}

        for node in ast_plan.nodes:
            node_by_id[node.id] = node

        return node_by_id

    def _build_depends_on(self, ast_plan: ASTPlan) -> dict[str, list[str]]:
        """Create node_id -> list of dependency node ids."""

        depends_on = {}

        for node in ast_plan.nodes:
            depends_on[node.id] = node.depends_on

        return depends_on

    def _build_reverse_dependencies(
        self,
        depends_on: dict[str, list[str]],
    ) -> dict[str, list[str]]:
        """
        Create dependency -> nodes waiting for it.

        Example:
        depends_on = {
            "2": ["1"]
        }

        reverse_dependencies = {
            "1": ["2"]
        }
        """

        reverse_dependencies = {}

        for node_id in depends_on:
            reverse_dependencies[node_id] = []

        for node_id, dependencies in depends_on.items():
            for dependency_id in dependencies:
                if dependency_id not in reverse_dependencies:
                    reverse_dependencies[dependency_id] = []

                reverse_dependencies[dependency_id].append(node_id)

        return reverse_dependencies

    def _build_children_by_node(self, ast_plan: ASTPlan) -> dict[str, list[str]]:
        """
        Create group_node_id -> child node ids.

        For ACTION / VERIFY / APPROVAL nodes, children list is empty.
        """

        children_by_node = {}

        for node in ast_plan.nodes:
            children_by_node[node.id] = self._get_node_children(node)

        return children_by_node

    def _get_node_children(self, node: ASTNode) -> list[str]:
        """Extract children from node.execution based on execution mode."""

        execution = node.execution
        mode = execution.get("mode")

        if mode in {"SEQUENCE", "PARALLEL"}:
            return execution.get("children", [])

        if mode == "IF":
            then_children = execution.get("then", [])
            else_children = execution.get("else", [])
            return then_children + else_children

        if mode == "FORALL":
            return execution.get("do", [])

        return []

    def _build_parent_by_node(
        self,
        children_by_node: dict[str, list[str]],
    ) -> dict[str, str]:
        """
        Create child_node_id -> parent_group_node_id.

        Used to know which nodes are top-level roots and which nodes are inside groups.
        """

        parent_by_node = {}

        for parent_id, children in children_by_node.items():
            for child_id in children:
                parent_by_node[child_id] = parent_id

        return parent_by_node

    def _find_root_nodes(
        self,
        ast_plan: ASTPlan,
        parent_by_node: dict[str, str],
    ) -> list[str]:
        """
        Find nodes that are not children of any GROUP node.

        These are the top-level nodes the executor starts from.
        """

        root_nodes = []

        for node in ast_plan.nodes:
            if node.id not in parent_by_node:
                root_nodes.append(node.id)

        return root_nodes