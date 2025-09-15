"""
Plan parsers for different EXPLAIN output formats.
Implements pev2's parsing logic for multiple formats.
"""

import json
import xml.etree.ElementTree as ET

import yaml

from ..exceptions import PlanParseError
from .base import BasePlanParser
from .json_parser import JSONPlanParser
from .text_parser import TextPlanParser
from .xml_parser import XMLPlanParser


def get_parser(plan_input: str) -> BasePlanParser:
    """
    Auto-detect plan format and return appropriate parser.
    Uses pev2's format detection logic.
    """
    plan_input = plan_input.strip()

    # JSON detection (most reliable)
    if _is_json(plan_input):
        return JSONPlanParser()

    # XML detection
    elif plan_input.startswith("<?xml") or plan_input.startswith("<explain"):
        return XMLPlanParser()

    # YAML detection (be careful not to conflict with text)
    elif _is_yaml_safe(plan_input):
        return JSONPlanParser()  # YAML parser can use JSON parser internally

    # Default to text format (most common for copy-paste)
    else:
        return TextPlanParser()


def _is_json(text: str) -> bool:
    """Check if input is valid JSON."""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def _is_yaml_safe(text: str) -> bool:
    """Safely check if input is YAML format."""
    try:
        # Only consider YAML if it has clear indicators
        if not any(indicator in text for indicator in ["- Plan:", "Plan:", "---"]):
            return False

        # Exclude PostgreSQL text output patterns
        if any(
            pg_indicator in text
            for pg_indicator in [
                "QUERY PLAN",
                "cost=",
                "Seq Scan",
                "Index Scan",
                "Hash Join",
                "Planning Time:",
                "Execution Time:",
                "rows=",
            ]
        ):
            return False

        yaml.safe_load(text)
        return True
    except (yaml.YAMLError, yaml.scanner.ScannerError):
        return False
