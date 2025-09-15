"""
Data models for plananalyze.
Separated from core.py to avoid circular imports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeMetrics:
    """Performance metrics for a single plan node - pev2 equivalent."""

    node_type: str
    startup_cost: float = 0.0
    total_cost: float = 0.0
    plan_rows: int = 0
    plan_width: int = 0
    actual_rows: Optional[int] = None
    actual_loops: Optional[int] = None
    actual_startup_time: Optional[float] = None
    actual_total_time: Optional[float] = None

    # Buffer statistics (like pev2's buffer analysis)
    shared_hit_blocks: Optional[int] = None
    shared_read_blocks: Optional[int] = None
    shared_dirtied_blocks: Optional[int] = None
    shared_written_blocks: Optional[int] = None

    # Derived metrics (calculated like pev2)
    exclusive_time: Optional[float] = None
    inclusive_time: Optional[float] = None
    rows_per_loop: Optional[float] = None
    cost_per_row: Optional[float] = None


@dataclass
class PlanNode:
    """
    Plan node representation - mirrors pev2's node structure.
    Contains all the essential data pev2 uses for visualization and analysis.
    """

    node_type: str
    node_id: str
    relation_name: Optional[str] = None
    schema_name: Optional[str] = None
    alias: Optional[str] = None
    index_name: Optional[str] = None
    parent_relationship: Optional[str] = None

    # Metrics (like pev2's cost/time analysis)
    metrics: Optional[NodeMetrics] = None

    # Tree structure
    children: List["PlanNode"] = field(default_factory=list)
    parent: Optional["PlanNode"] = None

    # Raw node data (for advanced analysis)
    raw_node: Optional[Dict] = None

    # pev2-style analysis flags
    is_costliest: bool = False
    is_slowest: bool = False
    is_largest: bool = False
    is_outlier: bool = False

    # Additional attributes that pev2 tracks
    join_type: Optional[str] = None
    index_condition: Optional[str] = None
    filter_condition: Optional[str] = None
    sort_key: Optional[List[str]] = None
    hash_buckets: Optional[int] = None


@dataclass
class PlanAnalysis:
    """
    Complete analysis result - equivalent to pev2's analysis output.
    Contains all the insights and breakdowns that pev2 provides.
    """

    # Basic plan info
    root_node: PlanNode
    planning_time: Optional[float] = None
    execution_time: Optional[float] = None
    total_cost: float = 0.0
    total_runtime: Optional[float] = None

    # Node analysis (pev2's key features)
    node_count: int = 0
    max_depth: int = 0
    costliest_nodes: List[PlanNode] = field(default_factory=list)
    slowest_nodes: List[PlanNode] = field(default_factory=list)
    largest_nodes: List[PlanNode] = field(default_factory=list)

    # Operation counts (pev2's statistics)
    seq_scan_count: int = 0
    index_scan_count: int = 0
    index_only_scan_count: int = 0
    bitmap_scan_count: int = 0
    join_count: int = 0
    sort_count: int = 0
    hash_count: int = 0
    aggregate_count: int = 0

    # Performance insights (pev2's analysis)
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    performance_issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Buffer analysis (like pev2's I/O insights)
    total_buffers_hit: int = 0
    total_buffers_read: int = 0
    buffer_hit_ratio: Optional[float] = None

    # Execution characteristics
    has_actual_times: bool = False
    has_buffers: bool = False
    planner_estimate_accuracy: Optional[float] = None
