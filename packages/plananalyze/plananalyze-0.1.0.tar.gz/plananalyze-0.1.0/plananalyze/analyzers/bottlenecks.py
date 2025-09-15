"""
Bottleneck detection engine - implements pev2's bottleneck identification.
Finds performance issues and anti-patterns in execution plans.
"""

from typing import Any, Dict, List

from ..models import PlanAnalysis, PlanNode


class BottleneckDetector:
    """
    Bottleneck detection engine that identifies performance issues.
    Implements pev2's bottleneck detection algorithms.
    """

    def detect(self, analysis: PlanAnalysis, options: Dict[str, Any]):
        """Detect various types of bottlenecks and performance issues."""
        self._detect_sequential_scans(analysis)
        self._detect_inefficient_joins(analysis)
        self._detect_expensive_sorts(analysis)
        self._detect_io_bottlenecks(analysis)
        self._detect_estimation_issues(analysis)
        self._detect_memory_issues(analysis)

        # Sort bottlenecks by severity/impact
        analysis.bottlenecks.sort(key=lambda x: x["impact"], reverse=True)

    def _detect_sequential_scans(self, analysis: PlanAnalysis):
        """Detect problematic sequential scans - pev2's key detection."""

        def check_node(node: PlanNode):
            if "seq scan" in node.node_type.lower():
                # Large sequential scans are potential bottlenecks
                if node.metrics.plan_rows > 1000:
                    severity = "high" if node.metrics.plan_rows > 10000 else "medium"

                    analysis.bottlenecks.append(
                        {
                            "type": "Sequential Scan",
                            "severity": severity,
                            "node": node,
                            "description": f'Sequential scan on {node.relation_name or "table"} ({node.metrics.plan_rows:,} rows)',
                            "impact": node.metrics.total_cost,
                            "recommendation": f"Consider adding an index on {node.relation_name}",
                        }
                    )

            for child in node.children:
                check_node(child)

        check_node(analysis.root_node)

    def _detect_inefficient_joins(self, analysis: PlanAnalysis):
        """Detect inefficient join operations."""

        def check_node(node: PlanNode):
            node_type_lower = node.node_type.lower()

            if "join" in node_type_lower:
                # Nested loop joins with high row counts are suspicious
                if "nested loop" in node_type_lower and node.metrics.plan_rows > 1000:
                    analysis.bottlenecks.append(
                        {
                            "type": "Inefficient Join",
                            "severity": "medium",
                            "node": node,
                            "description": f"Nested Loop join processing {node.metrics.plan_rows:,} rows",
                            "impact": node.metrics.total_cost,
                            "recommendation": "Consider hash join or merge join, or add better indexes",
                        }
                    )

                # Hash joins that spill to disk
                if (
                    "hash join" in node_type_lower
                    and hasattr(node, "hash_buckets")
                    and node.hash_buckets
                ):
                    # This would need more detailed analysis of hash join statistics
                    pass

            for child in node.children:
                check_node(child)

        check_node(analysis.root_node)

    def _detect_expensive_sorts(self, analysis: PlanAnalysis):
        """Detect expensive sorting operations."""

        def check_node(node: PlanNode):
            if "sort" in node.node_type.lower():
                # Large sorts are potential bottlenecks
                if node.metrics.plan_rows > 10000:
                    analysis.bottlenecks.append(
                        {
                            "type": "Expensive Sort",
                            "severity": "medium",
                            "node": node,
                            "description": f"Sorting {node.metrics.plan_rows:,} rows",
                            "impact": node.metrics.total_cost,
                            "recommendation": "Consider adding an index on sort columns or increasing work_mem",
                        }
                    )

            for child in node.children:
                check_node(child)

        check_node(analysis.root_node)

    def _detect_io_bottlenecks(self, analysis: PlanAnalysis):
        """Detect I/O related bottlenecks using buffer statistics."""
        if not analysis.has_buffers:
            return

        # Check buffer hit ratio
        if analysis.buffer_hit_ratio is not None and analysis.buffer_hit_ratio < 0.95:
            analysis.bottlenecks.append(
                {
                    "type": "I/O Bottleneck",
                    "severity": "medium",
                    "node": None,
                    "description": f"Low buffer hit ratio: {analysis.buffer_hit_ratio:.1%}",
                    "impact": analysis.total_buffers_read,
                    "recommendation": "Consider increasing shared_buffers or improving query selectivity",
                }
            )

        # Find nodes with excessive disk reads
        def check_io_node(node: PlanNode):
            if (
                node.metrics.shared_read_blocks
                and node.metrics.shared_read_blocks > 1000
            ):
                analysis.bottlenecks.append(
                    {
                        "type": "Excessive Disk I/O",
                        "severity": "high",
                        "node": node,
                        "description": f"{node.node_type} reading {node.metrics.shared_read_blocks:,} blocks from disk",
                        "impact": node.metrics.shared_read_blocks,
                        "recommendation": "Check if data fits in memory or improve query selectivity",
                    }
                )

            for child in node.children:
                check_io_node(child)

        check_io_node(analysis.root_node)

    def _detect_estimation_issues(self, analysis: PlanAnalysis):
        """Detect planner estimation issues."""

        def check_node(node: PlanNode):
            if hasattr(node, "has_estimation_error") and node.has_estimation_error:
                analysis.bottlenecks.append(
                    {
                        "type": "Estimation Error",
                        "severity": "low",
                        "node": node,
                        "description": f"Significant row estimation error in {node.node_type}",
                        "impact": node.metrics.total_cost,
                        "recommendation": "Consider running ANALYZE or adjusting statistics targets",
                    }
                )

            for child in node.children:
                check_node(child)

        check_node(analysis.root_node)

    def _detect_memory_issues(self, analysis: PlanAnalysis):
        """Detect memory-related issues."""

        def check_node(node: PlanNode):
            # Check for sorts that might spill to disk (would need more detailed sort info)
            if (
                "sort" in node.node_type.lower()
                and node.metrics.plan_rows * node.metrics.plan_width > 1000000
            ):  # ~1MB
                analysis.bottlenecks.append(
                    {
                        "type": "Potential Memory Issue",
                        "severity": "low",
                        "node": node,
                        "description": f"Large sort operation may exceed work_mem",
                        "impact": node.metrics.total_cost,
                        "recommendation": "Consider increasing work_mem for this query",
                    }
                )

            for child in node.children:
                check_node(child)

        check_node(analysis.root_node)
