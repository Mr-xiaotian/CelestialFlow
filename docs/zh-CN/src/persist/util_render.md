# src/celestialflow/persist/util_render.py

> 📅 最后更新日期: 2026/10/09

`util_render.py`（原 `graph/util_render.py`，已迁移至 `persist`）提供了**图结构渲染工具**。当前仅包含一个函数 `render_structure_list`，用于将图结构（节点、邻接表、源节点）渲染为**带边框的树形文本列表**，供日志模块在任务图启动时输出图结构概览。

## render_structure_list

```python
def render_structure_list(
    nodes: list[str],
    edges: dict[str, list[str]],
    source_nodes: list[str],
) -> list[str]:
```

从图结构（节点元信息、邻接表、源节点）生成带边框的树形文本列表。

### 渲染规则

1. 以 `source_nodes` 为根，按 `edges` 邻接表展开为树形文本；
2. 环或共享子图节点只展开一次，再次出现时标记 `[Ref]`；
3. 未从任意根渲染到的节点（孤立节点）追加在末尾；
4. 根节点不画连接符，子节点使用 `╞-->` / `╘-->` 连接符。

### 边界处理

- 无节点（空 `nodes`）时返回 `["+ No nodes defined +"]`；
- 未显式提供源节点时，推断为所有不作为任何边的子节点的节点；若仍为空，则取第一个节点作为源。

### 返回值格式

返回的字符串列表首尾各一条边框线，中间为逐行内容，例如：

```text
+----------------------+
| A                    |
| ╞--> B               |
|     ╘--> C [Ref]     |
| ╘--> D               |
+----------------------+
```

行内内容通过 `ljust` 补齐到同一宽度，保证边框对齐。

## 内部实现要点

- **显式栈迭代的 DFS 先序遍历**：避免深链图触发 Python 递归上限（默认约 1000 层）。
- 栈帧携带 `(node_name, prefix, is_last, is_root)`：`is_root` 表示根节点——根节点不画连接符且其子节点前缀为空；其余节点的前缀由父节点是否为同级最后一项决定。
- 每个节点首次访问时被加入 `expanded_nodes`；后续再遇到即以 `[Ref]` 标记并停止向下展开。
- 根节点之间、以及末尾追加的孤立节点之前，各插入一个空行。

## 使用示例

```python
from celestialflow.persist.util_render import render_structure_list

lines = render_structure_list(
    nodes=["A", "B", "C"],
    edges={"A": ["B", "C"]},
    source_nodes=["A"],
)
for line in lines:
    print(line)
```

## 调用方

`LogInlet`（`persist/core_log.py`）在 `on_graph_start` 中调用本函数，把 `GraphStartEvent` 携带的图元信息（`nodes` / `edges` / `source_nodes`）渲染为结构文本后逐行写入日志。

## 注意事项

1. **纯内存渲染**：函数不落盘、不依赖运行期状态，仅基于传入的图结构参数生成文本。
2. **迁移说明**：该工具原位于 `graph` 模块的 `util_render.py`，现已迁移至 `persist`，供日志模块复用。
3. **返回文本列表**：调用方需要自行决定如何消费返回的字符串列表（如逐行打印或写入文件）。