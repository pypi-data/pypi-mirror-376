"""
Exception classes for plananalyze.

Custom exceptions that provide specific error handling for different
types of failures in the plan analysis pipeline.
"""


class PlanAnalyzeError(Exception):
    """Base exception for all plananalyze errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class PlanParseError(PlanAnalyzeError):
    """
    Raised when plan parsing fails.

    This occurs when the input EXPLAIN output cannot be parsed,
    usually due to invalid format or corrupted data.
    """

    def __init__(self, message: str, plan_format: str = None, line_number: int = None):
        details = {}
        if plan_format:
            details["format"] = plan_format
        if line_number:
            details["line"] = line_number

        super().__init__(f"Plan parsing failed: {message}", details)
        self.plan_format = plan_format
        self.line_number = line_number


class AnalysisError(PlanAnalyzeError):
    """
    Raised when plan analysis fails.

    This occurs during the analysis phase when the parsed plan
    cannot be analyzed due to missing data or internal errors.
    """

    def __init__(self, message: str, analysis_stage: str = None, node_id: str = None):
        details = {}
        if analysis_stage:
            details["stage"] = analysis_stage
        if node_id:
            details["node_id"] = node_id

        super().__init__(f"Analysis failed: {message}", details)
        self.analysis_stage = analysis_stage
        self.node_id = node_id


class FormatterError(PlanAnalyzeError):
    """
    Raised when output formatting fails.

    This occurs when the analysis results cannot be formatted
    in the requested output format.
    """

    def __init__(self, message: str, format_type: str = None):
        details = {}
        if format_type:
            details["format_type"] = format_type

        super().__init__(f"Formatting failed: {message}", details)
        self.format_type = format_type


class ConfigurationError(PlanAnalyzeError):
    """
    Raised when configuration is invalid.

    This occurs when invalid configuration options are provided
    to the analyzer or formatters.
    """

    def __init__(self, message: str, config_key: str = None, config_value=None):
        details = {}
        if config_key:
            details["key"] = config_key
        if config_value is not None:
            details["value"] = str(config_value)

        super().__init__(f"Configuration error: {message}", details)
        self.config_key = config_key
        self.config_value = config_value


class UnsupportedFormatError(PlanParseError):
    """
    Raised when an unsupported plan format is encountered.

    This is a specific type of parse error for when the format
    is detected but not supported by plananalyze.
    """

    def __init__(self, format_type: str):
        message = f"Unsupported plan format: {format_type}"
        super().__init__(message, plan_format=format_type)
        self.format_type = format_type


class NodeNotFoundError(AnalysisError):
    """
    Raised when a required plan node cannot be found.

    This occurs during analysis when the code expects certain
    nodes to be present in the plan tree.
    """

    def __init__(self, node_type: str = None, node_id: str = None):
        if node_type and node_id:
            message = f"Node not found: {node_type} (ID: {node_id})"
        elif node_type:
            message = f"Node not found: {node_type}"
        elif node_id:
            message = f"Node not found with ID: {node_id}"
        else:
            message = "Required node not found in plan tree"

        super().__init__(message, node_id=node_id)
        self.node_type = node_type


# Utility functions for error handling
def handle_parse_error(func):
    """Decorator to handle parse errors gracefully."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, PlanAnalyzeError):
                raise
            # Convert generic exceptions to PlanParseError
            raise PlanParseError(str(e)) from e

    return wrapper


def handle_analysis_error(stage: str):
    """Decorator factory to handle analysis errors with context."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, PlanAnalyzeError):
                    raise
                # Convert generic exceptions to AnalysisError
                raise AnalysisError(str(e), analysis_stage=stage) from e

        return wrapper

    return decorator
