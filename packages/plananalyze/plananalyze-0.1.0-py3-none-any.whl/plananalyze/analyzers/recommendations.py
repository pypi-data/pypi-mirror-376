"""
Recommendation engine - generates optimization suggestions like pev2.
Provides actionable advice for improving query performance.
"""

from typing import Any, Dict, List, Optional

from ..models import PlanAnalysis, PlanNode


class RecommendationEngine:
    """
    Recommendation engine that generates optimization suggestions.
    Implements pev2's recommendation logic.
    """

    def generate(
        self, analysis: PlanAnalysis, query: Optional[str], options: Dict[str, Any]
    ):
        """Generate optimization recommendations."""
        self._generate_index_recommendations(analysis)
        self._generate_join_recommendations(analysis)
        self._generate_configuration_recommendations(analysis)
        self._generate_query_recommendations(analysis, query)

        # Remove duplicate recommendations
        analysis.recommendations = list(set(analysis.recommendations))

    def _generate_index_recommendations(self, analysis: PlanAnalysis):
        """Generate index-related recommendations."""
        seq_scan_tables = set()

        def find_seq_scans(node: PlanNode):
            if (
                "seq scan" in node.node_type.lower()
                and node.relation_name
                and node.metrics.plan_rows > 1000
            ):
                seq_scan_tables.add(node.relation_name)

            for child in node.children:
                find_seq_scans(child)

        find_seq_scans(analysis.root_node)

        for table in seq_scan_tables:
            analysis.recommendations.append(
                f"Consider adding an index on table '{table}' to avoid sequential scans"
            )

    def _generate_join_recommendations(self, analysis: PlanAnalysis):
        """Generate join-related recommendations."""
        if analysis.join_count > 3:
            analysis.recommendations.append(
                "Query has many joins - verify join order and consider query restructuring"
            )

        # Check for nested loop joins with high costs
        def check_joins(node: PlanNode):
            if (
                "nested loop" in node.node_type.lower()
                and node.metrics.total_cost > analysis.total_cost * 0.2
            ):
                analysis.recommendations.append(
                    "High-cost nested loop join detected - consider adding indexes on join columns"
                )

            for child in node.children:
                check_joins(child)

        check_joins(analysis.root_node)

    def _generate_configuration_recommendations(self, analysis: PlanAnalysis):
        """Generate PostgreSQL configuration recommendations."""
        # Memory recommendations
        if analysis.sort_count > 0:
            analysis.recommendations.append(
                "Multiple sort operations detected - consider increasing work_mem"
            )

        # Buffer recommendations
        if analysis.buffer_hit_ratio is not None and analysis.buffer_hit_ratio < 0.95:
            analysis.recommendations.append(
                "Low buffer hit ratio - consider increasing shared_buffers"
            )

        # I/O recommendations
        if analysis.total_buffers_read > 10000:
            analysis.recommendations.append(
                "High disk I/O detected - consider optimizing query selectivity or increasing memory"
            )

    def _generate_query_recommendations(
        self, analysis: PlanAnalysis, query: Optional[str]
    ):
        """Generate query-specific recommendations."""
        # Estimation accuracy recommendations
        if (
            hasattr(analysis, "planner_estimate_accuracy")
            and analysis.planner_estimate_accuracy is not None
            and analysis.planner_estimate_accuracy < 0.8
        ):
            analysis.recommendations.append(
                "Poor planner estimates detected - run ANALYZE on involved tables"
            )

        # General performance recommendations
        if analysis.execution_time and analysis.execution_time > 1000:  # > 1 second
            analysis.recommendations.append(
                "Long execution time - consider query optimization or adding appropriate indexes"
            )
