"""JSON formatter - produces machine-readable analysis output."""

import json
from datetime import datetime

from ..models import PlanAnalysis


class JSONFormatter:
    """JSON formatter for machine-readable output."""

    def format(self, analysis: PlanAnalysis) -> str:
        """Format analysis as JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_cost": analysis.total_cost,
                "execution_time": analysis.execution_time,
                "planning_time": analysis.planning_time,
                "total_runtime": analysis.total_runtime,
                "node_count": analysis.node_count,
                "has_actual_times": analysis.has_actual_times,
                "has_buffers": analysis.has_buffers,
            },
            "operations": {
                "seq_scan_count": analysis.seq_scan_count,
                "index_scan_count": analysis.index_scan_count,
                "index_only_scan_count": analysis.index_only_scan_count,
                "bitmap_scan_count": analysis.bitmap_scan_count,
                "join_count": analysis.join_count,
                "sort_count": analysis.sort_count,
                "hash_count": analysis.hash_count,
                "aggregate_count": analysis.aggregate_count,
            },
            "performance": {
                "buffer_hit_ratio": analysis.buffer_hit_ratio,
                "total_buffers_hit": analysis.total_buffers_hit,
                "total_buffers_read": analysis.total_buffers_read,
                "planner_estimate_accuracy": getattr(
                    analysis, "planner_estimate_accuracy", None
                ),
            },
            "top_nodes": {
                "costliest": [
                    {
                        "node_type": node.node_type,
                        "relation_name": node.relation_name,
                        "total_cost": node.metrics.total_cost,
                        "cost_percentage": (
                            node.metrics.total_cost / analysis.total_cost * 100
                        )
                        if analysis.total_cost > 0
                        else 0,
                    }
                    for node in analysis.costliest_nodes
                ],
                "slowest": [
                    {
                        "node_type": node.node_type,
                        "relation_name": node.relation_name,
                        "actual_total_time": node.metrics.actual_total_time,
                        "exclusive_time": node.metrics.exclusive_time,
                    }
                    for node in analysis.slowest_nodes
                    if node.metrics.actual_total_time
                ],
            },
            "bottlenecks": [
                {
                    "type": bottleneck["type"],
                    "severity": bottleneck["severity"],
                    "description": bottleneck["description"],
                    "impact": bottleneck["impact"],
                    "recommendation": bottleneck.get("recommendation"),
                    "node_type": bottleneck["node"].node_type
                    if bottleneck.get("node")
                    else None,
                    "relation_name": bottleneck["node"].relation_name
                    if bottleneck.get("node")
                    else None,
                }
                for bottleneck in analysis.bottlenecks
            ],
            "recommendations": analysis.recommendations,
        }

        return json.dumps(data, indent=2, default=str)
