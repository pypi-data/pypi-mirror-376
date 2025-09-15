"""Helper functions for plananalyze."""

from typing import Any, Dict, List, Optional

from ..core import PlanNode


def calculate_tree_depth(node: PlanNode, current_depth: int = 0) -> int:
    """Calculate the maximum depth of the plan tree."""
    if not node.children:
        return current_depth

    max_child_depth = max(
        calculate_tree_depth(child, current_depth + 1) for child in node.children
    )
    return max_child_depth


def find_nodes_by_type(root_node: PlanNode, node_type: str) -> List[PlanNode]:
    """Find all nodes of a specific type in the plan tree."""
    results = []

    def search_node(node: PlanNode):
        if node_type.lower() in node.node_type.lower():
            results.append(node)
        for child in node.children:
            search_node(child)

    search_node(root_node)
    return results


def calculate_inclusive_cost(node: PlanNode) -> float:
    """Calculate total cost including all children."""
    total = node.metrics.total_cost
    for child in node.children:
        total += calculate_inclusive_cost(child)
    return total


def get_node_path(node: PlanNode) -> List[str]:
    """Get the path from root to this node."""
    path = []
    current = node
    while current:
        path.insert(0, current.node_type)
        current = current.parent
    return path


def format_duration(milliseconds: Optional[float]) -> str:
    """Format duration in human-readable format."""
    if milliseconds is None:
        return "N/A"

    if milliseconds < 1:
        return f"{milliseconds:.3f} ms"
    elif milliseconds < 1000:
        return f"{milliseconds:.1f} ms"
    else:
        seconds = milliseconds / 1000
        if seconds < 60:
            return f"{seconds:.2f} s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"


def format_bytes(bytes_count: Optional[int]) -> str:
    """Format byte count in human-readable format."""
    if bytes_count is None:
        return "N/A"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_count)
    unit_idx = 0

    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1

    if unit_idx == 0:
        return f"{int(size)} {units[unit_idx]}"
    else:
        return f"{size:.1f} {units[unit_idx]}"


def calculate_selectivity(node: PlanNode) -> Optional[float]:
    """Calculate selectivity ratio (actual/estimated rows)."""
    if node.metrics.plan_rows > 0 and node.metrics.actual_rows is not None:
        return node.metrics.actual_rows / node.metrics.plan_rows
    return None


def is_scan_node(node: PlanNode) -> bool:
    """Check if node is a scan operation."""
    scan_types = ["seq scan", "index scan", "index only scan", "bitmap heap scan"]
    return any(scan_type in node.node_type.lower() for scan_type in scan_types)


def is_join_node(node: PlanNode) -> bool:
    """Check if node is a join operation."""
    return "join" in node.node_type.lower()


def get_table_name(node: PlanNode) -> Optional[str]:
    """Extract table name from node."""
    if node.relation_name:
        if node.schema_name:
            return f"{node.schema_name}.{node.relation_name}"
        return node.relation_name
    return None
