# UtilsCollections

> 📅 最后更新日期: 2026/04/22

`utils/util_collections.py` 提供集合/字典聚类工具。

## 主要函数

- `cluster_by_value_sorted(input_dict)`：按 value 聚类并按 value 升序返回。

## 使用示例

### cluster_by_value_sorted 的完整示例

以下展示各种聚类场景的用法：

```python
from celestialflow.utils.util_collections import cluster_by_value_sorted

# 示例 1：基本用法——按任务处理量对阶段分组
stage_stats = {
    "data_loader": 100,
    "preprocessor": 50,
    "analyzer": 100,
    "exporter": 50,
    "validator": 200,
}
result = cluster_by_value_sorted(stage_stats)
print("按处理量聚类结果:")
for value, stages in result.items():
    print(f"  处理量 {value:>3}: {stages}")
# 输出：
#   处理量  50: ['preprocessor', 'exporter']
#   处理量 100: ['data_loader', 'analyzer']
#   处理量 200: ['validator']

# 示例 2：独立的键导致每个键自成一类
test_data = {"a": 1, "b": 2, "c": 3}
print(f"\n独立值聚类: {cluster_by_value_sorted(test_data)}")
# 输出：{1: ['a'], 2: ['b'], 3: ['c']}

# 示例 3：所有键共享同一个值
test_data = {"x": 0, "y": 0, "z": 0}
print(f"\n相同值聚类: {cluster_by_value_sorted(test_data)}")
# 输出：{0: ['x', 'y', 'z']}

# 示例 4：按错误数量对服务进行聚类
error_counts = {
    "auth-service": 23,
    "payment-service": 45,
    "inventory-service": 12,
    "notification-service": 45,
    "search-service": 23,
    "gateway": 67,
}
grouped = cluster_by_value_sorted(error_counts)
print("\n按错误数量聚类（用于定位同级别问题服务）:")
for count, services in grouped.items():
    bar = "#" * (count // 5)
    print(f"  {count:>2} 个错误 {bar:>15}: {services}")
# 输出：
#  12 个错误           ##: ['inventory-service']
#  23 个错误          ####: ['auth-service', 'search-service']
#  45 个错误        #########: ['payment-service', 'notification-service']
#  67 个错误        #############: ['gateway']
```
