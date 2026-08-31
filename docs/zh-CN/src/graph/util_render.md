# GraphRender

> 📅 最后更新日期: 2026/08/31

`graph/util_render.py` 提供将图结构渲染为带边框的树形文本列表的工具，被 `TaskGraph.get_structure_list()` 直接调用，用于在日志/CLI 中可视化任务图拓扑。

## 主要能力

- `render_structure_list(nodes, edges, source_nodes)`：从节点元信息、邻接表和源节点列表生成带边框的树形文本列表。

## render_structure_list

```python
def render_structure_list(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, list[str]],
    source_nodes: list[str],
) -> list[str]: ...
```

### 渲染规则

- 以 `source_nodes` 为根，按 `edges` 邻接表展开为树形文本。
- 环或共享子图节点只展开一次；再次出现时标记 ` [Ref]`。
- 未从任意根渲染到的孤立节点追加在末尾。
- 根节点不画连接符，子节点使用 `╞-->` / `╘-->` 连接符。
- 使用**显式栈迭代的 DFS** 先序遍历，避免深链图触发 Python 递归上限（默认约 1000 层）。
- 返回一个带 `+---+` 上下边框的字符串列表，每行格式为 `| <content> |`。

### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `nodes` | `dict[str, dict[str, Any]]` | 节点元信息字典，每个节点需包含 `func_name` / `execution_mode` / `max_workers` 字段 |
| `edges` | `dict[str, list[str]]` | 出边邻接表 `{stage_name: [next_stage_name, ...]}` |
| `source_nodes` | `list[str]` | 源节点名称列表；为空时会自动从 `edges` 推断或取 `nodes` 第一个键 |

### 返回值

`list[str]` — 每行一个字符串，首尾分别是 `+---+` 边框，中间是带左右 `| ` 边距的内容行。

## 使用示例

以下示例展示 `render_structure_list` 的直接调用方式，以及通过 `TaskGraph.get_structure_list()` 的间接调用。

### 直接调用

```python
from celestialflow.graph.util_render import render_structure_list

# 节点元信息：通常来自 TaskGraph.get_stages_summary()
nodes = {
    "Fetch": {"func_name": "fetch_data", "execution_mode": "serial", "max_workers": 1},
    "Parse": {"func_name": "parse_data", "execution_mode": "thread", "max_workers": 4},
    "Save":  {"func_name": "save_data",  "execution_mode": "async",  "max_workers": 8},
}

# 出边邻接表
edges = {
    "Fetch": ["Parse"],
    "Parse": ["Save"],
}

# 源节点
source_nodes = ["Fetch"]

lines = render_structure_list(nodes, edges, source_nodes)
for line in lines:
    print(line)

# 输出示例：
# +---------------------------------------------------------------------------+
# | Fetch::fetch_data (E:serial, W:1)                                          |
# | ╘-->Parse::parse_data (E:thread, W:4)                                      |
# |     ╘-->Save::save_data (E:async, W:8)                                     |
# +---------------------------------------------------------------------------+
```

### 处理空图

```python
from celestialflow.graph.util_render import render_structure_list

print(render_structure_list({}, {}, []))
# ['+ No stages defined +']
```

### 通过 TaskGraph 内置方法

`TaskGraph.get_structure_list()` 会自动收集 `get_stages_summary()`、`order_graph.out_edges` 与 `source_names`，并调用 `render_structure_list`：

```python
from celestialflow import TaskGraph, TaskStage

s1 = TaskStage("Step1", func=lambda x: x.upper())
s2 = TaskStage("Step2", func=lambda x: len(x))
s3 = TaskStage("Step3", func=lambda x: x * 10)

graph = TaskGraph(name="RenderDemo", graph_mode="thread")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

graph.run({s1.get_name(): ["hello"]})

# 获取格式化树形文本
tree_lines = graph.get_structure_list()
for line in tree_lines:
    print(line)
```

## 输出特点

- 支持循环/引用节点标记（`[Ref]`）：当某节点已被展开过，再次出现在树中时附加 ` [Ref]`。
- 支持多源节点（forest）结构输出：根之间以空行分隔。
- 未连接节点（无父节点也未在源节点列表中）也会被作为独立树根渲染。
- DFS 使用显式栈帧 `(node_name, prefix, is_last, is_root)`，与递归版本结果完全一致但可处理深链图。

## 与其他模块的关系

- `TaskGraph.get_structure_list()` 是该函数的主要调用点，用于在日志和监控面板中可视化拓扑。
- 输入中的 `nodes` 字段名（`func_name` / `execution_mode` / `max_workers`）与 `TaskStage.get_summary()` 的输出字段保持一致。
