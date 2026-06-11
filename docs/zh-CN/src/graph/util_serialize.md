# GraphSerialize

> 📅 最后更新日期: 2026/06/11

`graph/util_serialize.py` 负责 TaskGraph 的结构序列化与文本化。

## 主要能力

- `build_structure_graph(stage_dict, out_edges, source_stages)`：从节点字典、邻接表和源节点构建结构 JSON。
- `format_structure_list_from_graph(structure)`：将结构 JSON 格式化为可打印树形文本。

## 使用示例

以下示例展示图序列化和文本化工具的使用方式。

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.graph.util_serialize import (
    build_structure_graph,
    format_structure_list_from_graph,
)

# 1. 构建一个简单的 DAG 图
s1 = TaskStage("Fetch", func=lambda x: x)
s2 = TaskStage("Parse", func=lambda x: x * 2)
s3 = TaskStage("Save", func=lambda x: x + 1)

graph = TaskGraph(name="SerializeGraph")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 2. 获取源节点
sources = graph.get_source_stages()
print(f"源节点数: {len(sources)}")

# 3. 构建结构 JSON
graph_json = build_structure_graph(
    stage_dict=graph.stage_dict,
    out_edges=graph.out_edges,
    source_stages=sources,
)
print(f"结构 JSON: {graph_json}")

# 4. 格式化为树形文本
rendered = format_structure_list_from_graph(graph_json)
for line in rendered:
    print(line)

# 输出示例：
# +-------------------------------------------+
# | Fetch::<lambda> (S:serial, E:serial)       |
# | ╘-->Parse::<lambda> (S:serial, E:serial)   |
# |     ╘-->Save::<lambda> (S:serial, E:serial)|
# +-------------------------------------------+
```

### 通过 TaskGraph 内置方法

`TaskGraph` 提供了便捷的 `get_structure_graph()` 和 `get_structure_list()` 方法：

```python
from celestialflow import TaskGraph, TaskStage

s1 = TaskStage("Step1", func=lambda x: x.upper())
s2 = TaskStage("Step2", func=lambda x: len(x))
s3 = TaskStage("Step3", func=lambda x: x * 10)

graph = TaskGraph(name="SerializeGraph2")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 获取 JSON 图结构 (dict)
structure = graph.get_structure_graph()
print("JSON 结构:")
import json
print(json.dumps(structure, indent=2, ensure_ascii=False))

# 获取格式化树形文本
tree_lines = graph.get_structure_list()
print("\n树形结构:")
for line in tree_lines:
    print(line)
```

## 输出特点

- 支持循环/引用节点标记（`[Ref]`）。
- 支持多源节点（forest）结构输出。
- 未连接节点（无父节点也未在源节点列表中）也会被渲染为独立树根。
