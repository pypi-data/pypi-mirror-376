"""
Performance analysis engine - pev2's performance calculation logic.
Calculates metrics like exclusive time, cost distribution, etc.
"""

from typing import Any, Dict, List, Optional

from ..models import PlanAnalysis, PlanNode


class PerformanceAnalyzer:
    """
    Performance analysis engine that implements pev2's performance calculations.
    Handles cost analysis, time distribution, and efficiency metrics.
    """

    def analyze(self, analysis: PlanAnalysis, options: Dict[str, Any]):
        """Perform comprehensive performance analysis."""
        self._calculate_exclusive_times(analysis.root_node)
        self._calculate_cost_distribution(analysis)
        self._calculate_efficiency_metrics(analysis)
        self._analyze_estimation_accuracy(analysis)

    def _calculate_exclusive_times(self, node: PlanNode):
        """
        Calculate exclusive time for each node (time spent in node itself).
        This is a key pev2 feature for identifying actual bottlenecks.
        """
        if not node.metrics.actual_total_time:
            # Recursively process children even without actual times
            for child in node.children:
                self._calculate_exclusive_times(child)
            return

        # Start with total time
        exclusive_time = node.metrics.actual_total_time

        # Subtract children's time to get exclusive time
        for child in node.children:
            self._calculate_exclusive_times(child)
            if child.metrics.actual_total_time:
                exclusive_time -= child.metrics.actual_total_time

        # Ensure non-negative (due to rounding errors)
        node.metrics.exclusive_time = max(0, exclusive_time)
        node.metrics.inclusive_time = node.metrics.actual_total_time

    def _calculate_cost_distribution(self, analysis: PlanAnalysis):
        """Calculate how costs are distributed across the plan tree."""
        all_nodes = []
        self._collect_nodes(analysis.root_node, all_nodes)

        # Calculate cost percentages
        if analysis.total_cost > 0:
            for node in all_nodes:
                cost_percentage = (node.metrics.total_cost / analysis.total_cost) * 100
                node.cost_percentage = cost_percentage

        # Find the most expensive operations (pev2's key insight)
        expensive_nodes = [
            n for n in all_nodes if n.metrics.total_cost > analysis.total_cost * 0.1
        ]
        analysis.expensive_operations = expensive_nodes

    def _calculate_efficiency_metrics(self, analysis: PlanAnalysis):
        """Calculate efficiency metrics like pev2 does."""
        all_nodes = []
        self._collect_nodes(analysis.root_node, all_nodes)

        # Calculate planner estimate vs actual efficiency
        estimation_errors = []

        for node in all_nodes:
            if (
                node.metrics.plan_rows > 0
                and node.metrics.actual_rows is not None
                and node.metrics.actual_rows > 0
            ):
                estimated = node.metrics.plan_rows
                actual = node.metrics.actual_rows

                # Calculate estimation error ratio
                error_ratio = abs(estimated - actual) / max(estimated, actual)
                estimation_errors.append(error_ratio)

                # Mark nodes with significant estimation errors
                if error_ratio > 0.5:  # 50% error threshold
                    node.has_estimation_error = True

        # Calculate overall estimation accuracy
        if estimation_errors:
            analysis.planner_estimate_accuracy = 1 - (
                sum(estimation_errors) / len(estimation_errors)
            )

    def _analyze_estimation_accuracy(self, analysis: PlanAnalysis):
        """Analyze how accurate the planner's estimates were."""
        if not analysis.has_actual_times:
            return

        total_estimated_time = 0
        total_actual_time = 0

        def collect_times(node: PlanNode):
            nonlocal total_estimated_time, total_actual_time

            # Use cost as estimate proxy if no actual startup time
            if node.metrics.actual_total_time:
                total_actual_time += node.metrics.actual_total_time
                total_estimated_time += node.metrics.total_cost  # Rough approximation

            for child in node.children:
                collect_times(child)

        collect_times(analysis.root_node)

        if total_estimated_time > 0 and total_actual_time > 0:
            accuracy = min(total_estimated_time, total_actual_time) / max(
                total_estimated_time, total_actual_time
            )
            analysis.time_estimate_accuracy = accuracy

    def _collect_nodes(self, node: PlanNode, collection: List[PlanNode]):
        """Recursively collect all nodes."""
        collection.append(node)
        for child in node.children:
            self._collect_nodes(child, collection)
