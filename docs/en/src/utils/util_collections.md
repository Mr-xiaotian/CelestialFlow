# UtilsCollections

> 📅 Last Updated: 2026/04/22

`utils/util_collections.py` provides collection/dictionary clustering utilities.

## Key Function

- `cluster_by_value_sorted(input_dict)`: Clusters by value and returns results sorted by value in ascending order.

## Usage Examples

### Complete Examples for cluster_by_value_sorted

The following demonstrates usage across various clustering scenarios:

```python
from celestialflow.utils.util_collections import cluster_by_value_sorted

# Example 1: Basic usage — group stages by task throughput
stage_stats = {
    "data_loader": 100,
    "preprocessor": 50,
    "analyzer": 100,
    "exporter": 50,
    "validator": 200,
}
result = cluster_by_value_sorted(stage_stats)
print("Clustered by throughput:")
for value, stages in result.items():
    print(f"  Throughput {value:>3}: {stages}")
# Output:
#   Throughput  50: ['preprocessor', 'exporter']
#   Throughput 100: ['data_loader', 'analyzer']
#   Throughput 200: ['validator']

# Example 2: Unique keys — each key forms its own cluster
test_data = {"a": 1, "b": 2, "c": 3}
print(f"\nUnique value clustering: {cluster_by_value_sorted(test_data)}")
# Output: {1: ['a'], 2: ['b'], 3: ['c']}

# Example 3: All keys share the same value
test_data = {"x": 0, "y": 0, "z": 0}
print(f"\nSame value clustering: {cluster_by_value_sorted(test_data)}")
# Output: {0: ['x', 'y', 'z']}

# Example 4: Cluster services by error count
error_counts = {
    "auth-service": 23,
    "payment-service": 45,
    "inventory-service": 12,
    "notification-service": 45,
    "search-service": 23,
    "gateway": 67,
}
grouped = cluster_by_value_sorted(error_counts)
print("\nClustered by error count (for identifying services at the same severity level):")
for count, services in grouped.items():
    bar = "#" * (count // 5)
    print(f"  {count:>2} errors {bar:>15}: {services}")
# Output:
#  12 errors           ##: ['inventory-service']
#  23 errors          ####: ['auth-service', 'search-service']
#  45 errors        #########: ['payment-service', 'notification-service']
#  67 errors        #############: ['gateway']
```
