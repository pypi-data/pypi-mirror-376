import xml.etree.ElementTree as ET
from typing import Any, Dict

from ..exceptions import PlanParseError
from .base import BasePlanParser


class XMLPlanParser(BasePlanParser):
    """Parser for XML format EXPLAIN output."""

    def parse(self, plan_input: str) -> Dict[str, Any]:
        """Parse XML format plan."""
        try:
            root = ET.fromstring(plan_input)
        except ET.ParseError as e:
            raise PlanParseError(f"XML parsing failed: {e}")

        # Find the Plan element
        plan_element = root.find(".//Plan")
        if plan_element is None:
            raise PlanParseError("No Plan element found in XML")

        # Convert to dictionary format
        plan_data = self._xml_to_dict(plan_element)

        # Extract metadata
        metadata = {}
        planning_time = root.find(".//Planning-Time")
        if planning_time is not None and planning_time.text:
            try:
                metadata["planning_time"] = float(planning_time.text)
            except ValueError:
                pass

        execution_time = root.find(".//Execution-Time")
        if execution_time is not None and execution_time.text:
            try:
                metadata["execution_time"] = float(execution_time.text)
            except ValueError:
                pass

        result = {"Plan": self._normalize_node(plan_data)}
        result.update(metadata)

        return result

    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary recursively."""
        result = {}

        # Process child elements
        for child in element:
            tag = child.tag.replace("-", " ").title()

            if child.tag == "Plans":
                # Handle child plans
                plans = []
                for plan_child in child:
                    plans.append(self._xml_to_dict(plan_child))
                result["Plans"] = plans
            elif child.text and child.text.strip():
                # Handle text content
                try:
                    # Try to convert to number
                    if "." in child.text:
                        result[tag] = float(child.text)
                    else:
                        result[tag] = int(child.text)
                except ValueError:
                    result[tag] = child.text.strip()
            else:
                # Handle nested elements
                nested = self._xml_to_dict(child)
                if nested:
                    result[tag] = nested

        return result
