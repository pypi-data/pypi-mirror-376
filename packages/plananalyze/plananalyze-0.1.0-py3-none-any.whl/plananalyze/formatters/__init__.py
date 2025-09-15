"""Output formatters for plananalyze - implements pev2's output formatting."""

from ..exceptions import FormatterError
from .html import HTMLFormatter
from .json import JSONFormatter
from .text import TextFormatter


def get_formatter(format_type: str):
    """Get appropriate formatter based on format type."""
    formatters = {
        "summary": TextFormatter(mode="summary"),
        "detailed": TextFormatter(mode="detailed"),
        "text": TextFormatter(mode="detailed"),
        "json": JSONFormatter(),
        "html": HTMLFormatter(),
    }

    formatter = formatters.get(format_type.lower())
    if not formatter:
        raise FormatterError(f"Unknown format type: {format_type}")

    return formatter
