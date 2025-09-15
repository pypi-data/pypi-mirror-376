"""
plananalyze - PostgreSQL EXPLAIN Plan Analyzer

A Python library that extracts the core logic of pev2 for analyzing
PostgreSQL execution plans and providing actionable performance insights.
"""

from .core import PlanAnalyzer, analyze_plan
from .exceptions import AnalysisError, FormatterError, PlanAnalyzeError, PlanParseError
from .models import NodeMetrics, PlanAnalysis, PlanNode

# Version info
__version__ = "0.1.0"
__author__ = "Guja Lomsadze"
__email__ = "lomsadze.guja@gmail.com"
__license__ = "Apache 2.0"

# Public API - what users can import
__all__ = [
    # Main classes
    "PlanAnalyzer",
    "PlanAnalysis",
    "PlanNode",
    "NodeMetrics",
    # Convenience functions
    "analyze_plan",
    # Exceptions
    "PlanAnalyzeError",
    "PlanParseError",
    "AnalysisError",
    "FormatterError",
    # Metadata
    "__version__",
]

# Default configuration
DEFAULT_CONFIG = {
    "cost_thresholds": {
        "high_cost_percentage": 0.3,
        "large_table_rows": 10000,
        "slow_operation_time": 100,
    },
    "analysis_options": {
        "detect_bottlenecks": True,
        "generate_recommendations": True,
        "calculate_exclusive_times": True,
        "analyze_buffer_usage": True,
    },
    "output_options": {
        "default_format": "summary",
        "show_costs": True,
        "show_timings": True,
        "highlight_issues": True,
    },
}


def get_version() -> str:
    """Get the current version of plananalyze."""
    return __version__


def configure(config_dict: dict):
    """
    Configure global settings for plananalyze.

    Args:
        config_dict: Configuration dictionary to merge with defaults
    """
    # This would update global configuration if needed
    # For now, just validation
    if not isinstance(config_dict, dict):
        raise ValueError("Configuration must be a dictionary")
