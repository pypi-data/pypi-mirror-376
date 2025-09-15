"""
Core tests for plananalyze functionality.
Tests the main analysis pipeline with real PostgreSQL EXPLAIN output.
"""

import pytest

from plananalyze import PlanAnalyzer, PlanParseError, analyze_plan


class TestPlanAnalyzer:
    """Test the main PlanAnalyzer class."""

    def test_text_format_parsing(self):
        """Test parsing of PostgreSQL text format."""
        plan_text = """
                             QUERY PLAN
         Seq Scan on employees  (cost=0.00..155.00 rows=10000 width=244)
           Filter: (department = 'Engineering'::text)
         Planning Time: 0.123 ms
         Execution Time: 45.678 ms
        (2 rows)
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan_text)

        assert analysis is not None
        assert analysis.root_node.node_type == "Seq Scan"
        assert analysis.root_node.relation_name == "employees"
        assert analysis.total_cost == 155.00
        assert analysis.planning_time == 0.123
        assert analysis.execution_time == 45.678
        assert analysis.seq_scan_count == 1

    def test_json_format_parsing(self):
        """Test parsing of JSON format EXPLAIN output."""
        plan_json = """
        [
          {
            "Plan": {
              "Node Type": "Seq Scan",
              "Relation Name": "employees",
              "Startup Cost": 0.00,
              "Total Cost": 155.00,
              "Plan Rows": 10000,
              "Plan Width": 244,
              "Filter": "(department = 'Engineering'::text)"
            },
            "Planning Time": 0.123,
            "Execution Time": 45.678
          }
        ]
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan_json)

        assert analysis.root_node.node_type == "Seq Scan"
        assert analysis.root_node.relation_name == "employees"
        assert analysis.root_node.metrics.total_cost == 155.00
        assert analysis.root_node.metrics.plan_rows == 10000
        assert analysis.planning_time == 0.123
        assert analysis.execution_time == 45.678

    def test_complex_plan_analysis(self):
        """Test analysis of complex plan with joins."""
        complex_plan = """
        [
          {
            "Plan": {
              "Node Type": "Hash Join",
              "Startup Cost": 15.42,
              "Total Cost": 87.18,
              "Plan Rows": 1000,
              "Plan Width": 244,
              "Actual Startup Time": 2.123,
              "Actual Total Time": 45.678,
              "Actual Rows": 850,
              "Actual Loops": 1,
              "Join Type": "Inner",
              "Hash Cond": "(e.department_id = d.id)",
              "Plans": [
                {
                  "Node Type": "Seq Scan",
                  "Parent Relationship": "Outer",
                  "Relation Name": "employees",
                  "Alias": "e",
                  "Startup Cost": 0.00,
                  "Total Cost": 25.50,
                  "Plan Rows": 1000,
                  "Plan Width": 100,
                  "Actual Startup Time": 0.012,
                  "Actual Total Time": 15.234,
                  "Actual Rows": 1000,
                  "Actual Loops": 1,
                  "Filter": "(salary > 50000)"
                },
                {
                  "Node Type": "Hash",
                  "Parent Relationship": "Inner",
                  "Startup Cost": 12.50,
                  "Total Cost": 12.50,
                  "Plan Rows": 5,
                  "Plan Width": 144,
                  "Actual Startup Time": 1.456,
                  "Actual Total Time": 1.456,
                  "Actual Rows": 5,
                  "Actual Loops": 1,
                  "Plans": [
                    {
                      "Node Type": "Index Scan",
                      "Parent Relationship": "Outer",
                      "Relation Name": "departments",
                      "Alias": "d",
                      "Index Name": "departments_pkey",
                      "Startup Cost": 0.42,
                      "Total Cost": 12.08,
                      "Plan Rows": 5,
                      "Plan Width": 144,
                      "Actual Startup Time": 0.123,
                      "Actual Total Time": 1.234,
                      "Actual Rows": 5,
                      "Actual Loops": 1
                    }
                  ]
                }
              ]
            },
            "Planning Time": 0.567,
            "Execution Time": 46.123
          }
        ]
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(complex_plan)

        # Test basic structure
        assert analysis.root_node.node_type == "Hash Join"
        assert len(analysis.root_node.children) == 2
        assert analysis.join_count == 1
        assert analysis.seq_scan_count == 1
        assert analysis.index_scan_count == 1

        # Test metrics calculation
        assert analysis.has_actual_times is True
        assert analysis.node_count == 4  # Hash Join + Seq Scan + Hash + Index Scan

        # Test node identification
        assert len(analysis.costliest_nodes) <= 3
        assert (
            analysis.costliest_nodes[0].node_type == "Hash Join"
        )  # Should be most expensive

    def test_bottleneck_detection(self):
        """Test bottleneck detection functionality."""
        problematic_plan = """
        [
          {
            "Plan": {
              "Node Type": "Sort",
              "Startup Cost": 1250.42,
              "Total Cost": 1275.42,
              "Plan Rows": 50000,
              "Plan Width": 244,
              "Sort Key": ["salary", "hire_date"],
              "Plans": [
                {
                  "Node Type": "Seq Scan",
                  "Relation Name": "large_table",
                  "Startup Cost": 0.00,
                  "Total Cost": 1200.00,
                  "Plan Rows": 45000,
                  "Plan Width": 244,
                  "Filter": "(status = 'active'::text)"
                }
              ]
            },
            "Planning Time": 2.567,
            "Execution Time": 1456.789
          }
        ]
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(problematic_plan)

        # Should detect bottlenecks
        assert len(analysis.bottlenecks) > 0

        # Should detect sequential scan bottleneck
        seq_scan_bottleneck = next(
            (b for b in analysis.bottlenecks if b["type"] == "Sequential Scan"), None
        )
        assert seq_scan_bottleneck is not None
        assert seq_scan_bottleneck["severity"] in ["high", "medium"]

        # Should detect expensive sort
        sort_bottleneck = next(
            (b for b in analysis.bottlenecks if b["type"] == "Expensive Sort"), None
        )
        assert sort_bottleneck is not None

    def test_recommendations_generation(self):
        """Test recommendation generation."""
        plan_with_issues = """
        [
          {
            "Plan": {
              "Node Type": "Nested Loop",
              "Startup Cost": 0.42,
              "Total Cost": 1125.42,
              "Plan Rows": 50000,
              "Plan Width": 244,
              "Join Type": "Inner",
              "Plans": [
                {
                  "Node Type": "Seq Scan",
                  "Relation Name": "employees",
                  "Startup Cost": 0.00,
                  "Total Cost": 450.00,
                  "Plan Rows": 25000,
                  "Plan Width": 200
                },
                {
                  "Node Type": "Seq Scan",
                  "Relation Name": "departments",
                  "Startup Cost": 0.00,
                  "Total Cost": 15.00,
                  "Plan Rows": 2,
                  "Plan Width": 44
                }
              ]
            }
          }
        ]
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan_with_issues)

        # Should generate recommendations
        assert len(analysis.recommendations) > 0

        # Should recommend indexes for sequential scans
        index_recommendations = [
            r
            for r in analysis.recommendations
            if "index" in r.lower() and ("employees" in r or "departments" in r)
        ]
        assert len(index_recommendations) > 0

    def test_format_outputs(self):
        """Test different output formats."""
        simple_plan = """
        [
          {
            "Plan": {
              "Node Type": "Index Scan",
              "Relation Name": "users",
              "Index Name": "users_pkey",
              "Startup Cost": 0.42,
              "Total Cost": 8.44,
              "Plan Rows": 1,
              "Plan Width": 244
            },
            "Planning Time": 0.123,
            "Execution Time": 1.456
          }
        ]
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(simple_plan)

        # Test summary format
        summary = analyzer.format_analysis(analysis, "summary")
        assert "PostgreSQL Plan Analysis Summary" in summary
        assert "Index Scans: 1" in summary

        # Test detailed format
        detailed = analyzer.format_analysis(analysis, "detailed")
        assert "Detailed PostgreSQL Plan Analysis" in detailed
        assert "users" in detailed

        # Test JSON format
        json_output = analyzer.format_analysis(analysis, "json")
        assert '"total_cost": 8.44' in json_output
        assert '"index_scan_count": 1' in json_output

        # Test HTML format
        html_output = analyzer.format_analysis(analysis, "html")
        assert "<html" in html_output
        assert "PostgreSQL Plan Analysis Report" in html_output

    def test_convenience_function(self):
        """Test the convenience analyze_plan function."""
        plan = """
        [
          {
            "Plan": {
              "Node Type": "Seq Scan",
              "Relation Name": "test_table",
              "Startup Cost": 0.00,
              "Total Cost": 100.00,
              "Plan Rows": 1000,
              "Plan Width": 50
            }
          }
        ]
        """

        # Test returning analysis object
        analysis = analyze_plan(plan, format_type="object")
        assert analysis.root_node.node_type == "Seq Scan"
        assert analysis.total_cost == 100.00

        # Test returning formatted string
        summary = analyze_plan(plan, format_type="summary")
        assert isinstance(summary, str)
        assert "PostgreSQL Plan Analysis Summary" in summary


class TestEdgeCases:
    """Test edge cases and unusual plan structures."""

    def test_plan_without_costs(self):
        """Test handling plans without cost information."""
        minimal_plan = """
        [
          {
            "Plan": {
              "Node Type": "Seq Scan",
              "Relation Name": "test_table"
            }
          }
        ]
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(minimal_plan)

        assert analysis.root_node.node_type == "Seq Scan"
        assert analysis.root_node.metrics.total_cost == 0.0
        assert analysis.total_cost == 0.0

    def test_deep_nested_plan(self):
        """Test deeply nested plan structures."""
        nested_plan = """
        [
          {
            "Plan": {
              "Node Type": "Limit",
              "Startup Cost": 0.42,
              "Total Cost": 8.45,
              "Plan Rows": 10,
              "Plan Width": 244,
              "Plans": [
                {
                  "Node Type": "Sort",
                  "Startup Cost": 0.42,
                  "Total Cost": 8.44,
                  "Plan Rows": 1000,
                  "Plan Width": 244,
                  "Plans": [
                    {
                      "Node Type": "Hash Join",
                      "Startup Cost": 0.42,
                      "Total Cost": 7.44,
                      "Plan Rows": 1000,
                      "Plan Width": 244,
                      "Plans": [
                        {
                          "Node Type": "Seq Scan",
                          "Relation Name": "table1",
                          "Startup Cost": 0.00,
                          "Total Cost": 3.50,
                          "Plan Rows": 500,
                          "Plan Width": 122
                        },
                        {
                          "Node Type": "Hash",
                          "Startup Cost": 0.21,
                          "Total Cost": 0.21,
                          "Plan Rows": 500,
                          "Plan Width": 122,
                          "Plans": [
                            {
                              "Node Type": "Index Scan",
                              "Relation Name": "table2",
                              "Index Name": "table2_idx",
                              "Startup Cost": 0.00,
                              "Total Cost": 0.21,
                              "Plan Rows": 500,
                              "Plan Width": 122
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          }
        ]
        """

        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(nested_plan)

        # Test structure
        assert analysis.node_count == 6
        assert analysis.join_count == 1
        assert analysis.sort_count == 1
        assert analysis.seq_scan_count == 1
        assert analysis.index_scan_count == 1

        # Test that all nodes are properly connected
        def count_nodes_recursive(node):
            count = 1
            for child in node.children:
                count += count_nodes_recursive(child)
            return count

        assert count_nodes_recursive(analysis.root_node) == analysis.node_count


if __name__ == "__main__":
    pytest.main([__file__])
