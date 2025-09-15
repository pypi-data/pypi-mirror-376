import re
from typing import Any, Dict, List, Optional, Tuple

from ..exceptions import PlanParseError
from .base import BasePlanParser


class TextPlanParser(BasePlanParser):
    """
    Parser for PostgreSQL text format EXPLAIN output.
    Implements pev2's text parsing logic with robust tree building.
    """

    def parse(self, plan_input: str) -> Dict[str, Any]:
        """Parse text format EXPLAIN output."""
        lines = plan_input.strip().split("\n")

        # for line in lines:
        #     re.sub(r"^\s*->\s*", "", line)

        # Extract plan lines and metadata
        plan_lines, metadata = self._extract_plan_content(lines)

        if not plan_lines:
            raise PlanParseError("No plan content found in text input")

        # Build the plan tree
        root_node = self._build_plan_tree(plan_lines)

        return {
            "Plan": root_node,
            "Planning Time": metadata.get("planning_time"),
            "Execution Time": metadata.get("execution_time"),
        }

    def _extract_plan_content(
        self, lines: List[str]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """Extract plan content and metadata from lines."""
        plan_lines = []
        metadata = {}

        for line in lines:
            stripped = line.strip()
            re.sub(r"^\s*->\s*", "", line)

            # Skip header lines and separators
            if (
                (
                    not stripped
                    or "QUERY PLAN" in line
                    or stripped.startswith(("-", "="))
                )
                # or "(" in stripped
                # and "rows)" in stripped
                and len(stripped) < 30
            ):
                continue

            # Extract metadata
            if stripped.startswith("Planning Time:"):
                try:
                    time_match = re.search(r"([\d.]+)", stripped)
                    if time_match:
                        metadata["planning_time"] = float(time_match.group(1))
                except ValueError:
                    pass
                continue

            if stripped.startswith("Execution Time:"):
                try:
                    time_match = re.search(r"([\d.]+)", stripped)
                    if time_match:
                        metadata["execution_time"] = float(time_match.group(1))
                except ValueError:
                    pass
                continue

            # Keep plan content
            if stripped:
                plan_lines.append(line)

        return plan_lines, metadata

    def _build_plan_tree(self, lines: List[str]) -> Dict[str, Any]:
        """Build hierarchical plan tree from text lines."""
        if not lines:
            raise PlanParseError("No plan lines to parse")

        # Parse lines into nodes with indentation
        parsed_lines = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                node_data = self._parse_node_line(line.strip())
                parsed_lines.append((indent, node_data))

        if not parsed_lines:
            raise PlanParseError("No valid plan nodes found")

        # Build tree structure
        root_indent, root_node = parsed_lines[0]
        self._attach_children(root_node, parsed_lines, 0, root_indent)

        return root_node

    def _parse_node_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a single plan line into node data.
        Implements pev2's line parsing logic.
        """
        # Remove arrow indicators
        re.sub(r"^\s*->\s*", "", line)

        # Extract node components using comprehensive regex
        # Pattern: NodeType [on relation [alias]] (cost=... rows=... width=...) (actual time=... rows=... loops=...)

        # Split by parentheses to separate node info from cost info
        parts = re.split(r"\s*\(([^)]+)\)", line)
        node_part = parts[0].strip()

        # Parse node type and relation info
        relation_match = re.match(r"^(.+?)\s+on\s+(\w+)(?:\s+(\w+))?$", node_part)

        if relation_match:
            node_type = relation_match.group(1).strip()
            relation = relation_match.group(2)
            alias = relation_match.group(3)
        else:
            node_type = node_part
            relation = None
            alias = None

        # Create base node
        node = {
            "Node Type": node_type,
            "Startup Cost": 0.0,
            "Total Cost": 0.0,
            "Plan Rows": 0,
            "Plan Width": 0,
        }

        if relation:
            node["Relation Name"] = relation
        if alias:
            node["Alias"] = alias

        # Parse cost and timing information from parentheses
        for i in range(1, len(parts), 2):
            if i < len(parts):
                self._parse_cost_info(parts[i], node)

        return self._normalize_node(node)

    def _parse_cost_info(self, cost_info: str, node: Dict[str, Any]):
        """Extract cost and timing information from parentheses content."""
        # Cost pattern: cost=0.00..155.00
        cost_match = re.search(r"cost=([\d.]+)\.\.([\d.]+)", cost_info)
        if cost_match:
            node["Startup Cost"] = float(cost_match.group(1))
            node["Total Cost"] = float(cost_match.group(2))

        # Rows pattern: rows=10000
        rows_match = re.search(r"rows=(\d+)", cost_info)
        if rows_match:
            node["Plan Rows"] = int(rows_match.group(1))

        # Width pattern: width=244
        width_match = re.search(r"width=(\d+)", cost_info)
        if width_match:
            node["Plan Width"] = int(width_match.group(1))

        # Actual time pattern: actual time=2.123..45.678
        actual_time_match = re.search(r"actual time=([\d.]+)\.\.([\d.]+)", cost_info)
        if actual_time_match:
            node["Actual Startup Time"] = float(actual_time_match.group(1))
            node["Actual Total Time"] = float(actual_time_match.group(2))

        # Actual rows pattern: actual rows=850
        actual_rows_match = re.search(r"actual rows=(\d+)", cost_info)
        if actual_rows_match:
            node["Actual Rows"] = int(actual_rows_match.group(1))

        # Loops pattern: loops=1
        loops_match = re.search(r"loops=(\d+)", cost_info)
        if loops_match:
            node["Actual Loops"] = int(loops_match.group(1))

    def _attach_children(
        self,
        parent_node: Dict[str, Any],
        parsed_lines: List[Tuple[int, Dict]],
        start_idx: int,
        parent_indent: int,
    ):
        """Recursively attach child nodes to build tree structure."""
        children = []
        i = start_idx + 1

        while i < len(parsed_lines):
            indent, node_data = parsed_lines[i]

            # If this node is a direct child (indented more than parent)
            if indent > parent_indent:
                # Find where this child's subtree ends
                subtree_end = self._find_subtree_end(parsed_lines, i, indent)

                # Recursively attach this child's children
                self._attach_children(node_data, parsed_lines, i, indent)

                children.append(node_data)
                i = subtree_end
            else:
                # This node is not a child, stop processing
                break

        if children:
            parent_node["Plans"] = children

    def _find_subtree_end(
        self, parsed_lines: List[Tuple[int, Dict]], start_idx: int, node_indent: int
    ) -> int:
        """Find where a node's subtree ends."""
        i = start_idx + 1
        while i < len(parsed_lines):
            indent, _ = parsed_lines[i]
            if indent <= node_indent:
                return i
            i += 1
        return len(parsed_lines)
