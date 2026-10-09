# tests/persist/test_render.py

> 📅 最后更新日期: 2026/10/09

## 作用

验证 `celestialflow.persist.util_render.render_structure_list` 的结构渲染逻辑：能否将节点与邻接表渲染为带边框的树形文本列表、正确处理空结构与环图，并在深链图上不会触发 Python 递归上限。

> `util_render` 重构后由 `src/celestialflow/graph` 迁移至 `src/celestialflow/persist`，本测试镜像随之位于 `tests/persist` 目录。

## 核心测试对象

| 类 / 对象 | 来源 | 说明 |
|-----------|------|------|
| `render_structure_list(nodes, edges, source_nodes)` | `celestialflow.persist.util_render` | 从节点列表、邻接表与源节点生成带边框的树形文本列表，返回字符串列表（首尾为边框行） |
| `DEEP`（=5000） | 本文件常量 | 超过 Python 默认递归上限（约 1000），用于回归显式栈迭代渲染逻辑 |

## 测试覆盖矩阵

### `TestUtilRender`

| 用例 | 覆盖目标 |
|------|---------|
| `test_render_structure_list` | 普通 DAG（`s1→s2/s3→s4`）渲染出含 `s1` 的树形列表，且含 `[Ref]` 标记的循环引用行 |
| `test_render_structure_list_no_nodes` | 空结构返回占位提示 `["+ No nodes defined +"]` |
| `test_render_structure_list_cycle` | 环图（`c1→c2→c3→c1`）只展开一次，重复节点标记为 `[Ref]`；`c1` 出现次数恰为 2（首次展开 + 回指） |
| `test_render_deep_chain_no_recursion_error` | 5000 节点深链图不触发递归上限，渲染行数为 `DEEP + 2`（边框 + 节点行 + 边框） |

## 关键测试场景

### `test_render_structure_list_cycle`

- 构造环 `{"c1": ["c2"], "c2": ["c3"], "c3": ["c1"]}`，以 `["c1"]` 为根渲染。
- 断言合并后的文本中 `c1` 恰好出现 2 次（首次展开 + `[Ref]` 回指），且包含 `[Ref]`。

### `test_render_deep_chain_no_recursion_error`

- 构造 5000 个节点的单链（`n0 → n1 → ... → n4999`）。
- 断言 `render_structure_list` 返回 `DEEP + 2` 行（首尾边框 + 5000 节点行），首行为 `n0`、末节点为 `n4999`。
- 该用例验证渲染采用**显式栈迭代 DFS**而非递归，从而规避 Python 默认递归上限。

## 运行方式

```bash
# 全部执行
pytest tests/persist/test_render.py -v

# 按关键字匹配
pytest tests/persist/test_render.py -k "cycle" -v
pytest tests/persist/test_render.py -k "deep" -v
```

## 注意事项

- 深链用例（`DEEP=5000`）依赖 `render_structure_list` 的内部实现改为显式栈迭代；若回退为递归实现，会触发 `RecursionError`。
- 相关实现位于 `src/celestialflow/persist/util_render.py`。