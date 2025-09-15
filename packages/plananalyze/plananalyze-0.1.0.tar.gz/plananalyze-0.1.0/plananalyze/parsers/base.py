"""Base parser interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePlanParser(ABC):
    """Base class for all plan parsers - pev2's parser interface."""

    @abstractmethod
    def parse(self, plan_input: str) -> Dict[str, Any]:
        """
        Parse plan input and return standardized format.

        Returns:
            Dict with 'Plan' key containing the root node and optional metadata
        """
        pass

    def _normalize_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize node data to standard format."""
        # Ensure numeric values are properly typed
        for key in ["Startup Cost", "Total Cost"]:
            if key in node:
                try:
                    node[key] = float(node[key])
                except (ValueError, TypeError):
                    node[key] = 0.0

        for key in ["Plan Rows", "Plan Width", "Actual Rows", "Actual Loops"]:
            if key in node:
                try:
                    node[key] = int(node[key])
                except (ValueError, TypeError):
                    node[key] = 0

        return node
