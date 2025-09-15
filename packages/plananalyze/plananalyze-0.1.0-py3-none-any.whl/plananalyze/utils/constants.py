"""Constants and enums used throughout plananalyze."""


class NodeTypes:
    """PostgreSQL plan node types - pev2's node type constants."""

    # Scan operations
    SEQ_SCAN = "Seq Scan"
    INDEX_SCAN = "Index Scan"
    INDEX_ONLY_SCAN = "Index Only Scan"
    BITMAP_INDEX_SCAN = "Bitmap Index Scan"
    BITMAP_HEAP_SCAN = "Bitmap Heap Scan"

    # Join operations
    NESTED_LOOP = "Nested Loop"
    HASH_JOIN = "Hash Join"
    MERGE_JOIN = "Merge Join"

    # Other operations
    SORT = "Sort"
    HASH = "Hash"
    AGGREGATE = "Aggregate"
    GROUP = "Group"
    LIMIT = "Limit"
    SUBQUERY_SCAN = "Subquery Scan"
    CTE_SCAN = "CTE Scan"
    FUNCTION_SCAN = "Function Scan"
    VALUES_SCAN = "Values Scan"


class CostThresholds:
    """Cost and performance thresholds for analysis."""

    # Cost thresholds (relative to total cost)
    HIGH_COST_PERCENTAGE = 0.3  # 30% of total cost
    MEDIUM_COST_PERCENTAGE = 0.1  # 10% of total cost

    # Row count thresholds
    LARGE_TABLE_ROWS = 10000
    MEDIUM_TABLE_ROWS = 1000

    # Time thresholds (milliseconds)
    SLOW_OPERATION_TIME = 100
    VERY_SLOW_OPERATION_TIME = 1000

    # Buffer thresholds
    GOOD_BUFFER_HIT_RATIO = 0.95
    POOR_BUFFER_HIT_RATIO = 0.80
    HIGH_DISK_READS = 1000

    # Estimation accuracy thresholds
    GOOD_ESTIMATION_ACCURACY = 0.8
    POOR_ESTIMATION_ACCURACY = 0.5


class Severity:
    """Severity levels for issues and bottlenecks."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
