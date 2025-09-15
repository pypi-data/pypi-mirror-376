"""
plananalyze.core - Main PostgreSQL EXPLAIN Plan Analyzer

Core implementation inspired by GL's analysis logic.
Extracts the essential plan parsing and analysis capabilities.
"""

from typing import Any, Dict, List, Optional, Union

from .exceptions import AnalysisError, PlanParseError
from .formatters import get_formatter
from .models import NodeMetrics, PlanAnalysis, PlanNode
from .parsers import get_parser
from .utils.constants import CostThresholds, NodeTypes


class PlanAnalyzer:
    """
    Main analyzer class - the core of plananalyze.

    This is the equivalent of GL's main analysis engine.
    It orchestrates parsing, analysis, and formatting just like GL does.
    """

    def __init__(self):
        self._node_counter = 0

    def analyze(
        self,
        plan_input: str,
        query: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> PlanAnalysis:
        """
        Main analysis method - equivalent to GL's analyze() function.

        Args:
            plan_input: Raw EXPLAIN output (any format)
            query: Original SQL query (optional)
            options: Analysis options

        Returns:
            PlanAnalysis: Complete analysis results
        """
        options = options or {}

        try:
            # Step 1: Parse the plan (like GL's parser)
            parsed_plan = self._parse_plan(plan_input)

            # Step 2: Build tree structure (GL's tree building)
            root_node = self._build_tree(parsed_plan)

            # Step 3: Calculate metrics (GL's metric calculation)
            analysis = PlanAnalysis(root_node=root_node)
            self._calculate_basic_metrics(analysis, parsed_plan)

            # Step 4: Perform deep analysis (GL's analysis engine)
            # Import here to avoid circular imports
            from .analyzers.bottlenecks import BottleneckDetector
            from .analyzers.performance import PerformanceAnalyzer
            from .analyzers.recommendations import RecommendationEngine

            performance_analyzer = PerformanceAnalyzer()
            bottleneck_detector = BottleneckDetector()
            recommendation_engine = RecommendationEngine()

            performance_analyzer.analyze(analysis, options)
            bottleneck_detector.detect(analysis, options)
            recommendation_engine.generate(analysis, query, options)

            # Step 5: Mark significant nodes (GL's node highlighting)
            self._mark_significant_nodes(analysis)

            return analysis

        except Exception as e:
            raise AnalysisError(f"Failed to analyze plan: {e}") from e

    def _parse_plan(self, plan_input: str) -> Dict[str, Any]:
        """Parse plan input using appropriate parser - GL's parsing logic."""
        parser = get_parser(plan_input)
        return parser.parse(plan_input)

    def _build_tree(self, parsed_plan: Dict[str, Any]) -> PlanNode:
        """
        Build tree structure from parsed plan.
        This mirrors GL's tree construction logic.
        """
        self._node_counter = 0
        plan_data = parsed_plan.get("Plan", parsed_plan)

        if not plan_data:
            raise PlanParseError("No plan data found")

        return self._create_node(plan_data, None)

    def _create_node(
        self, node_data: Dict[str, Any], parent: Optional[PlanNode]
    ) -> PlanNode:
        """
        Create a plan node from raw data.
        Implements GL's node creation logic with all essential attributes.
        """
        self._node_counter += 1

        # Extract basic node information (GL's approach)
        node_type = node_data.get("Node Type", "Unknown")

        # Create metrics object (GL's metrics structure)
        metrics = NodeMetrics(
            node_type=node_type,
            startup_cost=float(node_data.get("Startup Cost", 0)),
            total_cost=float(node_data.get("Total Cost", 0)),
            plan_rows=int(node_data.get("Plan Rows", 0)),
            plan_width=int(node_data.get("Plan Width", 0)),
            actual_rows=node_data.get("Actual Rows"),
            actual_loops=node_data.get("Actual Loops"),
            actual_startup_time=node_data.get("Actual Startup Time"),
            actual_total_time=node_data.get("Actual Total Time"),
            shared_hit_blocks=node_data.get("Shared Hit Blocks"),
            shared_read_blocks=node_data.get("Shared Read Blocks"),
            shared_dirtied_blocks=node_data.get("Shared Dirtied Blocks"),
            shared_written_blocks=node_data.get("Shared Written Blocks"),
        )

        # Calculate derived metrics (GL's calculations)
        self._calculate_derived_metrics(metrics, node_data)

        # Create node (GL's node structure)
        node = PlanNode(
            node_type=node_type,
            node_id=f"node_{self._node_counter}",
            relation_name=node_data.get("Relation Name"),
            schema_name=node_data.get("Schema"),
            alias=node_data.get("Alias"),
            index_name=node_data.get("Index Name"),
            parent_relationship=node_data.get("Parent Relationship"),
            metrics=metrics,
            parent=parent,
            raw_node=node_data,
            join_type=node_data.get("Join Type"),
            index_condition=node_data.get("Index Cond"),
            filter_condition=node_data.get("Filter"),
            sort_key=node_data.get("Sort Key"),
            hash_buckets=node_data.get("Hash Buckets"),
        )

        # Process children recursively (GL's tree building)
        if "Plans" in node_data:
            for child_data in node_data["Plans"]:
                child_node = self._create_node(child_data, node)
                node.children.append(child_node)

        return node

    def _calculate_derived_metrics(
        self, metrics: NodeMetrics, node_data: Dict[str, Any]
    ):
        """Calculate derived metrics like GL does."""
        # Exclusive time calculation (GL's logic)
        if metrics.actual_total_time is not None and metrics.actual_loops:
            metrics.exclusive_time = metrics.actual_total_time

        # Rows per loop
        if metrics.actual_rows is not None and metrics.actual_loops:
            metrics.rows_per_loop = metrics.actual_rows / metrics.actual_loops

        # Cost per row
        if metrics.total_cost > 0 and metrics.plan_rows > 0:
            metrics.cost_per_row = metrics.total_cost / metrics.plan_rows

    def _calculate_basic_metrics(
        self, analysis: PlanAnalysis, parsed_plan: Dict[str, Any]
    ):
        """Calculate basic plan metrics - GL's metric calculation."""
        # Extract timing info
        analysis.planning_time = parsed_plan.get("Planning Time")
        analysis.execution_time = parsed_plan.get("Execution Time")
        analysis.total_cost = analysis.root_node.metrics.total_cost

        # Calculate derived values
        if analysis.execution_time and analysis.planning_time:
            analysis.total_runtime = analysis.execution_time + analysis.planning_time

        # Count nodes and operations (GL's statistics)
        self._count_operations(analysis.root_node, analysis)

        # Buffer analysis
        self._calculate_buffer_metrics(analysis.root_node, analysis)

        # Check for actual times and buffers
        analysis.has_actual_times = self._has_actual_times(analysis.root_node)
        analysis.has_buffers = self._has_buffer_data(analysis.root_node)

    def _count_operations(self, node: PlanNode, analysis: PlanAnalysis):
        """Count different operation types - GL's operation counting."""
        analysis.node_count += 1

        node_type = node.node_type.lower()

        if "seq scan" in node_type:
            analysis.seq_scan_count += 1
        elif "index scan" in node_type and "only" not in node_type:
            analysis.index_scan_count += 1
        elif "index only scan" in node_type:
            analysis.index_only_scan_count += 1
        elif "bitmap" in node_type:
            analysis.bitmap_scan_count += 1
        elif "join" in node_type:
            analysis.join_count += 1
        elif "sort" in node_type:
            analysis.sort_count += 1
        elif "hash" in node_type and "join" not in node_type:
            analysis.hash_count += 1
        elif "aggregate" in node_type:
            analysis.aggregate_count += 1

        # Recursively count children
        for child in node.children:
            self._count_operations(child, analysis)

    def _calculate_buffer_metrics(self, node: PlanNode, analysis: PlanAnalysis):
        """Calculate buffer statistics - GL's buffer analysis."""
        if node.metrics.shared_hit_blocks:
            analysis.total_buffers_hit += node.metrics.shared_hit_blocks
        if node.metrics.shared_read_blocks:
            analysis.total_buffers_read += node.metrics.shared_read_blocks

        # Process children
        for child in node.children:
            self._calculate_buffer_metrics(child, analysis)

        # Calculate hit ratio
        total_buffers = analysis.total_buffers_hit + analysis.total_buffers_read
        if total_buffers > 0:
            analysis.buffer_hit_ratio = analysis.total_buffers_hit / total_buffers

    def _has_actual_times(self, node: PlanNode) -> bool:
        """Check if plan has actual execution times."""
        if node.metrics.actual_total_time is not None:
            return True
        return any(self._has_actual_times(child) for child in node.children)

    def _has_buffer_data(self, node: PlanNode) -> bool:
        """Check if plan has buffer statistics."""
        if node.metrics.shared_hit_blocks is not None:
            return True
        return any(self._has_buffer_data(child) for child in node.children)

    def _mark_significant_nodes(self, analysis: PlanAnalysis):
        """Mark significant nodes for highlighting - GL's node marking logic."""
        all_nodes = []
        self._collect_all_nodes(analysis.root_node, all_nodes)

        # Find costliest nodes (GL's approach)
        nodes_by_cost = sorted(
            all_nodes, key=lambda n: n.metrics.total_cost, reverse=True
        )
        analysis.costliest_nodes = nodes_by_cost[:3]
        for node in analysis.costliest_nodes:
            node.is_costliest = True

        # Find slowest nodes (if we have actual times)
        if analysis.has_actual_times:
            nodes_with_time = [
                n for n in all_nodes if n.metrics.actual_total_time is not None
            ]
            nodes_by_time = sorted(
                nodes_with_time, key=lambda n: n.metrics.actual_total_time, reverse=True
            )
            analysis.slowest_nodes = nodes_by_time[:3]
            for node in analysis.slowest_nodes:
                node.is_slowest = True

        # Find largest nodes (by row count)
        nodes_by_rows = sorted(
            all_nodes, key=lambda n: n.metrics.plan_rows, reverse=True
        )
        analysis.largest_nodes = nodes_by_rows[:3]
        for node in analysis.largest_nodes:
            node.is_largest = True

    def _collect_all_nodes(self, node: PlanNode, collection: List[PlanNode]):
        """Collect all nodes in the tree."""
        collection.append(node)
        for child in node.children:
            self._collect_all_nodes(child, collection)

    def format_analysis(
        self, analysis: PlanAnalysis, format_type: str = "summary"
    ) -> str:
        """
        Format analysis results - GL's formatting logic.

        Args:
            analysis: Analysis results
            format_type: Output format ('summary', 'detailed', 'json', 'html')

        Returns:
            Formatted analysis string
        """
        formatter = get_formatter(format_type)
        return formatter.format(analysis)


# Convenience function for quick analysis (like GL's simple interface)
def analyze_plan(
    plan_input: str, query: Optional[str] = None, format_type: str = "summary"
) -> Union[PlanAnalysis, str]:
    """
    Quick plan analysis function - GL's simple interface equivalent.

    Args:
        plan_input: EXPLAIN output
        query: Optional SQL query
        format_type: Output format

    Returns:
        Analysis results or formatted string
    """
    analyzer = PlanAnalyzer()
    analysis = analyzer.analyze(plan_input, query)

    if format_type == "object":
        return analysis
    else:
        return analyzer.format_analysis(analysis, format_type)
