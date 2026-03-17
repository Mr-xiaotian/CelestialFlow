# TaskTools

TaskTools 模块提供了一系列辅助函数，涵盖图结构分析、数据格式化、日志持久化等方面。

## 图结构处理

### build_structure_graph

```python
def build_structure_graph(root_stages: List[TaskStage]) -> List[Dict[str, Any]]:
    """
    从多个根节点构建任务链的 JSON 图结构。
    """
```

### format_networkx_graph

将 JSON 结构的图转换为 `networkx.DiGraph` 对象，便于使用 NetworkX 库进行复杂的图论分析（如 DAG 检测、拓扑排序）。

```python
def format_networkx_graph(structure_graph: List[Dict]) -> nx.DiGraph: ...
```

### compute_node_levels

计算 DAG 中每个节点的层级（最早执行阶段）。用于分层调度 (`staged` mode)。

```python
def compute_node_levels(G: nx.DiGraph) -> Dict[str, int]: ...
```

## 数据格式化

- `format_table`: 将二维数据格式化为 ASCII 表格。
- `format_repr`: 将对象格式化为字符串，支持截断超长文本。
- `format_duration`: 将秒数格式化为 `HH:MM:SS`。
- `format_avg_time`: 计算并格式化平均处理时间。

## 日志与持久化

### JSONL 操作

- `append_jsonl_log`: 追加写入单条 JSON 日志。
- `append_jsonl_logs`: 批量追加写入 JSON 日志。
- `load_jsonl_logs`: 读取 JSONL 日志。
- `load_jsonl_grouped_by_keys`: 读取并按指定键分组。

## 估算算法

### calc_global_remain_equal_pred

基于 DAG 拓扑和当前运行状态，估算全局剩余执行时间。
采用“拥塞放大型”估算策略：
1. 假设下游节点的任务量来自所有上游的贡献。
2. 使用“已完成任务数”作为放大基准，提前暴露拥塞风险。

```python
def calc_global_remain_equal_pred(
    G: nx.DiGraph,
    processed_map: Dict[str, int],
    pending_map: Dict[str, int],
    elapsed_map: Dict[str, float],
) -> Dict[str, float]: ...
```
