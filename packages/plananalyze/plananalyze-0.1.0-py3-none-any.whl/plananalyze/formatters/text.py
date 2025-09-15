"""Text formatter - produces human-readable analysis reports."""

import json
from typing import Any, Dict

from ..models import PlanAnalysis, PlanNode


class TextFormatter:
    """Text formatter that produces pev2-style text reports."""

    def __init__(self, mode: str = "summary"):
        self.mode = mode

    def format(self, analysis: PlanAnalysis) -> str:
        """Format analysis as text report."""
        if self.mode == "summary":
            return self._format_summary(analysis)
        else:
            return self._format_detailed(analysis)

    def _format_summary(self, analysis: PlanAnalysis) -> str:
        """Format a concise summary report."""
        lines = []
        lines.append("=== PostgreSQL Plan Analysis Summary ===\n")

        # Basic metrics
        lines.append("📊 EXECUTION OVERVIEW:")
        lines.append(f"   Total Cost: {analysis.total_cost:.2f}")
        lines.append(f"   Node Count: {analysis.node_count}")
        if analysis.execution_time:
            lines.append(f"   Execution Time: {analysis.execution_time:.3f} ms")
        if analysis.planning_time:
            lines.append(f"   Planning Time: {analysis.planning_time:.3f} ms")
        lines.append("")

        # Operation counts
        lines.append("🔍 OPERATIONS:")
        lines.append(f"   Sequential Scans: {analysis.seq_scan_count}")
        lines.append(
            f"   Index Scans: {analysis.index_scan_count + analysis.index_only_scan_count}"
        )
        lines.append(f"   Joins: {analysis.join_count}")
        lines.append(f"   Sorts: {analysis.sort_count}")
        lines.append("")

        # Performance insights
        if analysis.bottlenecks:
            lines.append("⚠️  TOP ISSUES:")
            for i, bottleneck in enumerate(analysis.bottlenecks[:3], 1):
                lines.append(
                    f"   {i}. {bottleneck['description']} (Impact: {bottleneck['impact']:.1f})"
                )
            lines.append("")

        # Key recommendations
        if analysis.recommendations:
            lines.append("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(analysis.recommendations[:3], 1):
                lines.append(f"   {i}. {rec}")

        return "\n".join(lines)

    def _format_detailed(self, analysis: PlanAnalysis) -> str:
        """Format a detailed analysis report."""
        lines = []
        lines.append("=== Detailed PostgreSQL Plan Analysis ===\n")

        # Execution metrics
        lines.append("📈 EXECUTION METRICS:")
        lines.append(f"   Total Cost: {analysis.total_cost:.2f}")
        lines.append(f"   Root Operation: {analysis.root_node.node_type}")
        if analysis.execution_time:
            lines.append(f"   Execution Time: {analysis.execution_time:.3f} ms")
        if analysis.planning_time:
            lines.append(f"   Planning Time: {analysis.planning_time:.3f} ms")
        if analysis.total_runtime:
            lines.append(f"   Total Runtime: {analysis.total_runtime:.3f} ms")
        lines.append("")

        # Plan structure
        lines.append("🏗️  PLAN STRUCTURE:")
        lines.append(f"   Total Nodes: {analysis.node_count}")
        lines.append(f"   Plan Depth: {analysis.max_depth}")
        lines.append("")

        # Operation breakdown
        lines.append("🔍 OPERATION BREAKDOWN:")
        lines.append(f"   Sequential Scans: {analysis.seq_scan_count}")
        lines.append(f"   Index Scans: {analysis.index_scan_count}")
        lines.append(f"   Index Only Scans: {analysis.index_only_scan_count}")
        lines.append(f"   Bitmap Scans: {analysis.bitmap_scan_count}")
        lines.append(f"   Join Operations: {analysis.join_count}")
        lines.append(f"   Sort Operations: {analysis.sort_count}")
        lines.append(f"   Hash Operations: {analysis.hash_count}")
        lines.append(f"   Aggregate Operations: {analysis.aggregate_count}")
        lines.append("")

        # Top performers
        if analysis.costliest_nodes:
            lines.append("💰 MOST EXPENSIVE OPERATIONS:")
            for i, node in enumerate(analysis.costliest_nodes, 1):
                pct = (
                    (node.metrics.total_cost / analysis.total_cost * 100)
                    if analysis.total_cost > 0
                    else 0
                )
                relation = f" on {node.relation_name}" if node.relation_name else ""
                lines.append(
                    f"   {i}. {node.node_type}{relation} - Cost: {node.metrics.total_cost:.2f} ({pct:.1f}%)"
                )
            lines.append("")

        if analysis.slowest_nodes:
            lines.append("⏱️  SLOWEST OPERATIONS:")
            for i, node in enumerate(analysis.slowest_nodes, 1):
                relation = f" on {node.relation_name}" if node.relation_name else ""
                time = node.metrics.actual_total_time or 0
                lines.append(
                    f"   {i}. {node.node_type}{relation} - Time: {time:.3f} ms"
                )
            lines.append("")

        # I/O Analysis
        if analysis.has_buffers:
            lines.append("💾 I/O ANALYSIS:")
            lines.append(
                f"   Buffer Hit Ratio: {analysis.buffer_hit_ratio:.1%}"
                if analysis.buffer_hit_ratio
                else "   Buffer Hit Ratio: N/A"
            )
            lines.append(f"   Total Buffers Hit: {analysis.total_buffers_hit:,}")
            lines.append(f"   Total Buffers Read: {analysis.total_buffers_read:,}")
            lines.append("")

        # Performance issues
        if analysis.bottlenecks:
            lines.append("⚠️  PERFORMANCE ISSUES:")
            for i, bottleneck in enumerate(analysis.bottlenecks, 1):
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(
                    bottleneck["severity"], "⚪"
                )
                lines.append(f"   {i}. {severity_icon} {bottleneck['description']}")
                lines.append(
                    f"      Impact: {bottleneck['impact']:.2f} | Type: {bottleneck['type']}"
                )
                if bottleneck.get("recommendation"):
                    lines.append(f"      💡 {bottleneck['recommendation']}")
            lines.append("")

        # Recommendations
        if analysis.recommendations:
            lines.append("🎯 OPTIMIZATION RECOMMENDATIONS:")
            for i, rec in enumerate(analysis.recommendations, 1):
                lines.append(f"   {i}. {rec}")

        return "\n".join(lines)
