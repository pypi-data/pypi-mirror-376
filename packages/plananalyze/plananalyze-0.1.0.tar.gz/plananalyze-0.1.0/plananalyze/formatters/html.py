"""HTML formatter - produces rich HTML reports with visualizations."""

from ..models import PlanAnalysis


class HTMLFormatter:
    """HTML formatter for rich visual reports."""

    def format(self, analysis: PlanAnalysis) -> str:
        """Format analysis as HTML report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PostgreSQL Plan Analysis Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #7f8c8d; margin-top: 5px; }}
        .bottleneck {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .bottleneck.high {{ background-color: #ffebee; border-left: 4px solid #f44336; }}
        .bottleneck.medium {{ background-color: #fff3e0; border-left: 4px solid #ff9800; }}
        .bottleneck.low {{ background-color: #e8f5e8; border-left: 4px solid #4caf50; }}
        .recommendation {{ background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #2196f3; }}
        .node-list {{ list-style: none; padding: 0; }}
        .node-item {{ background: #f8f9fa; margin: 5px 0; padding: 10px; border-radius: 5px; }}
        .progress-bar {{ background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ background: linear-gradient(90deg, #3498db, #2ecc71); height: 100%; text-align: center; line-height: 20px; color: white; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: 600; }}
        .severity-high {{ color: #f44336; }}
        .severity-medium {{ color: #ff9800; }}
        .severity-low {{ color: #4caf50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>PostgreSQL Plan Analysis Report</h1>

        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{analysis.total_cost:.1f}</div>
                <div class="metric-label">Total Cost</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{analysis.node_count}</div>
                <div class="metric-label">Plan Nodes</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{analysis.execution_time:.1f}ms</div>
                <div class="metric-label">Execution Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(analysis.bottlenecks)}</div>
                <div class="metric-label">Issues Found</div>
            </div>
        </div>

        <h2>Operation Breakdown</h2>
        <table>
            <thead>
                <tr><th>Operation Type</th><th>Count</th><th>Percentage</th></tr>
            </thead>
            <tbody>
                <tr><td>Sequential Scans</td><td>{analysis.seq_scan_count}</td><td>{(analysis.seq_scan_count / analysis.node_count * 100):.1f}%</td></tr>
                <tr><td>Index Scans</td><td>{analysis.index_scan_count}</td><td>{(analysis.index_scan_count / analysis.node_count * 100):.1f}%</td></tr>
                <tr><td>Joins</td><td>{analysis.join_count}</td><td>{(analysis.join_count / analysis.node_count * 100):.1f}%</td></tr>
                <tr><td>Sorts</td><td>{analysis.sort_count}</td><td>{(analysis.sort_count / analysis.node_count * 100):.1f}%</td></tr>
            </tbody>
        </table>

        {self._format_top_nodes_html(analysis)}
        {self._format_bottlenecks_html(analysis)}
        {self._format_recommendations_html(analysis)}

    </div>
</body>
</html>
"""
        return html

    def _format_top_nodes_html(self, analysis: PlanAnalysis) -> str:
        """Format top nodes section."""
        if not analysis.costliest_nodes:
            return ""

        html = "<h2>Most Expensive Operations</h2><ul class='node-list'>"
        for i, node in enumerate(analysis.costliest_nodes, 1):
            pct = (
                (node.metrics.total_cost / analysis.total_cost * 100)
                if analysis.total_cost > 0
                else 0
            )
            relation = f" on {node.relation_name}" if node.relation_name else ""
            html += f"""
            <li class="node-item">
                <strong>{i}. {node.node_type}{relation}</strong>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {pct}%">{pct:.1f}%</div>
                </div>
                Cost: {node.metrics.total_cost:.2f}
            </li>
            """
        html += "</ul>"
        return html

    def _format_bottlenecks_html(self, analysis: PlanAnalysis) -> str:
        """Format bottlenecks section."""
        if not analysis.bottlenecks:
            return ""

        html = "<h2>Performance Issues</h2>"
        for bottleneck in analysis.bottlenecks:
            severity_class = f"severity-{bottleneck['severity']}"
            html += f"""
            <div class="bottleneck {bottleneck['severity']}">
                <strong class="{severity_class}">[{bottleneck['severity'].upper()}]</strong> {bottleneck['description']}
                <br><small>Impact: {bottleneck['impact']:.2f} | Type: {bottleneck['type']}</small>
            </div>
            """
        return html

    def _format_recommendations_html(self, analysis: PlanAnalysis) -> str:
        """Format recommendations section."""
        if not analysis.recommendations:
            return ""

        html = "<h2>Optimization Recommendations</h2>"
        for i, rec in enumerate(analysis.recommendations, 1):
            html += f'<div class="recommendation"><strong>{i}.</strong> {rec}</div>'
        return html
