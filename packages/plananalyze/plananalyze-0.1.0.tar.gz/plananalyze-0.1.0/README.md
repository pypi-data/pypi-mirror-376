# `plananalyze`

# PostgreSQL `EXPLAIN` Plan Analyzer - Extract insights from execution plans Query

## For best results, run `EXPLAIN` like so `EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS)`

``

# Quickstart

1. Run "ANALYZE" on your Query
2. Copy-paste output from PostgreSQL
3. Review details :)

```python
from plananalyze import analyze_plan

plan = """
Hash Join  (cost=12.70..30.50 rows=120 width=743)
  Hash Cond: ((d.name)::text = (employees.department)::text)
  ->  Seq Scan on departments d  (cost=0.00..14.80 rows=480 width=142)
  ->  Hash  (cost=11.20..11.20 rows=120 width=601)
        ->  Seq Scan on employees  (cost=0.00..11.20 rows=120 width=601)
"""

result = analyze_plan(plan, format_type="summary")
print(result)
```

Output:

```shell
📊 EXECUTION OVERVIEW:
   Total Cost: 30.50
   Node Count: 5

🔍 OPERATIONS:
   Sequential Scans: 2
   Index Scans: 0
   Joins: 1
   Sorts: 0
```

# Detailed Response

```python
# Use format_type="detailed"
result = analyze_plan(plan, format_type="detailed")
```

Output:

```shell
📈 EXECUTION METRICS:
   Total Cost: 30.50
   Root Operation: Hash Join

🏗️  PLAN STRUCTURE:
   Total Nodes: 5
   Plan Depth: 0

🔍 OPERATION BREAKDOWN:
   Sequential Scans: 2
   Index Scans: 0
   Index Only Scans: 0
   Bitmap Scans: 0
   Join Operations: 1
   Sort Operations: 0
   Hash Operations: 2
   Aggregate Operations: 0

💰 MOST EXPENSIVE OPERATIONS:
   1. Hash Join - Cost: 30.50 (100.0%)
   2. ->  Seq Scan on departments - Cost: 14.80 (48.5%)
   3. ->  Hash - Cost: 11.20 (36.7%)
```

# JSON output

```python
# Use format_type="json"
result = analyze_plan(plan, format_type="json")
```

# JSON Input

### Run "explain" on PostgreSQL query using `EXPLAIN (FORMAT JSON)`

```python
from plananalyze import analyze_plan

plan_json = """
[
  {
    "Plan": {
      "Node Type": "Hash Join",
      "Parallel Aware": false,
      "Async Capable": false,
      "Join Type": "Inner",
      "Startup Cost": 12.70,
      "Total Cost": 30.50,
      "Plan Rows": 120,
      "Plan Width": 743,
      "Inner Unique": false,
      "Hash Cond": "((d.name)::text = (employees.department)::text)",
      "Plans": [
        {
          "Node Type": "Seq Scan",
          "Parent Relationship": "Outer",
          "Parallel Aware": false,
          "Async Capable": false,
          "Relation Name": "departments",
          "Alias": "d",
          "Startup Cost": 0.00,
          "Total Cost": 14.80,
          "Plan Rows": 480,
          "Plan Width": 142
        },
        {
          "Node Type": "Hash",
          "Parent Relationship": "Inner",
          "Parallel Aware": false,
          "Async Capable": false,
          "Startup Cost": 11.20,
          "Total Cost": 11.20,
          "Plan Rows": 120,
          "Plan Width": 601,
          "Plans": [
            {
              "Node Type": "Seq Scan",
              "Parent Relationship": "Outer",
              "Parallel Aware": false,
              "Async Capable": false,
              "Relation Name": "employees",
              "Alias": "employees",
              "Startup Cost": 0.00,
              "Total Cost": 11.20,
              "Plan Rows": 120,
              "Plan Width": 601
            }
          ]
        }
      ]
    }
  }
]
"""

result = analyze_plan(plan_json, format_type="summary")
print(result)
```
