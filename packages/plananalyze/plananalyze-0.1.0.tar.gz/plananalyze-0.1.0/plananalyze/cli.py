# plananalyze/cli.py
"""Command-line interface for plananalyze."""

import argparse
import sys
from pathlib import Path

from . import __version__, analyze_plan
from .exceptions import PlanAnalyzeError


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="plananalyze",
        description="PostgreSQL EXPLAIN Plan Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  plananalyze plan.txt
  plananalyze plan.json --format detailed
  cat plan.txt | plananalyze -
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"plananalyze {__version__}"
    )
    parser.add_argument("input", nargs="?", help="Plan file (use - for stdin)")
    parser.add_argument(
        "--format",
        "-f",
        choices=["summary", "detailed", "json"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    try:
        # Read input
        if not args.input:
            parser.print_help()
            return

        if args.input == "-":
            plan_input = sys.stdin.read()
            if not plan_input.strip():
                raise PlanAnalyzeError("No input provided on stdin")
        else:
            input_path = Path(args.input)
            if not input_path.exists():
                raise PlanAnalyzeError(f"Input file not found: {args.input}")
            plan_input = input_path.read_text(encoding="utf-8")

        if args.verbose:
            print(f"Analyzing plan with format: {args.format}", file=sys.stderr)

        # Analyze
        result = analyze_plan(plan_input, format_type=args.format)

        # Output
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            if args.verbose:
                print(f"Analysis saved to {args.output}", file=sys.stderr)
        else:
            print(result)

    except PlanAnalyzeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.verbose:
            import traceback

            traceback.print_exc()
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
