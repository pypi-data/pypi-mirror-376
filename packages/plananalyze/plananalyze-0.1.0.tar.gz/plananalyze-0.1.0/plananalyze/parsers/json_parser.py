import json
from typing import Any, Dict

import yaml

from ..exceptions import PlanParseError
from .base import BasePlanParser


class JSONPlanParser(BasePlanParser):
    """
    Parser for JSON format EXPLAIN output.
    Handles both JSON and YAML formats (since YAML can be converted to JSON).
    """

    def parse(self, plan_input: str) -> Dict[str, Any]:
        """Parse JSON or YAML format plan."""
        try:
            # Try JSON first
            data = self._parse_json(plan_input)
        except (json.JSONDecodeError, ValueError):
            try:
                # Try YAML as fallback
                data = yaml.safe_load(plan_input)
            except yaml.YAMLError as e:
                raise PlanParseError(f"Invalid JSON/YAML format: {e}")

        # Handle array format (common in PostgreSQL JSON output)
        if isinstance(data, list):
            if not data:
                raise PlanParseError("Empty plan array")
            data = data[0]

        # Ensure we have a Plan key
        if "Plan" not in data:
            raise PlanParseError("No 'Plan' key found in JSON data")

        # Normalize the plan tree
        self._normalize_tree(data["Plan"])

        return data

    def _parse_json(self, json_input: str) -> Dict[str, Any]:
        """Parse JSON with better error handling."""
        try:
            return json.loads(json_input)
        except json.JSONDecodeError as e:
            raise PlanParseError(f"JSON parsing failed: {e}")

    def _normalize_tree(self, node: Dict[str, Any]):
        """Recursively normalize all nodes in the tree."""
        self._normalize_node(node)

        # Process child plans
        if "Plans" in node:
            for child in node["Plans"]:
                self._normalize_tree(child)
