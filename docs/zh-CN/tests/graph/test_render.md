# 图结构渲染测试 (test_render.py)

> 📅 最后更新日期: 2026/08/31

## 作用
验证 `celestialflow.graph.util_render.render_structure_list` 能够将图结构（节点元信息、邻接表、源节点）渲染为带边框的树形文本列表，覆盖普通 DAG、含环图、空图与超深链等场景，并确保深度图渲染不会触发 Python 默认递归上限。

## 核心测试对象
- `render_structure_list(nodes, edges, source_nodes)`: 渲染函数，返回带边框的字符串列表。
- `DEEP = 5000`: 超过 Python 默认递归上限（约 1000）的深链规模，用于回归迭代版渲染逻辑。
- `make_node(name, mode, workers)`: 辅助函数，构造包含 `func_name` / `execution_mode` / `max_workers` 的节点元信息字典。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 | 关键断言 |
|--------|--------|---------|---------|
| `TestUtilRender` | 4 | 普通 DAG 渲染、空结构、环图引用标记、超深链渲染 | 节点标签格式 `(E:<mode>, W:<workers>)`；空结构返回 `"+ No stages defined +"`；环图重复节点只展开一次并标记 `[Ref]`；深链长度 = `DEEP + 2` 且不抛 `RecursionError` |

## 关键测试场景

1. **普通 DAG 渲染** (`test_render_structure_list`): 4 节点钻石形结构（s1→{s2,s3}→s4），验证节点标签格式正确、列表中含 `[Ref]` 标记。
2. **空结构** (`test_render_structure_list_no_nodes`): 空 `nodes` 应返回占位提示 `"+ No stages defined +"`。
3. **环图引用标记** (`test_render_structure_list_cycle`): 三节点闭环（c1→c2→c3→c1），验证 `c1` 出现 2 次（首次展开 + `[Ref]` 回指），整段输出含 `[Ref]`。
4. **超深链不触发递归上限** (`test_render_deep_chain_no_recursion_error`): 5000 节点线性链，验证渲染行数恰好为 `DEEP + 2`（上边框 + 节点行 + 下边框），首末节点标签均正确。

## 测试重点
- **节点标签格式**: `name::func_name (E:execution_mode, W:max_workers)`，引用节点附加 ` [Ref]`。
- **递归安全**: 实现采用显式栈的迭代 DFS，深链渲染不应触发 `RecursionError`。
- **空输入与边界**: 空 `nodes` 返回固定占位文本，避免空列表渲染。
- **环图收敛**: 共享子图节点只展开一次，防止无限循环或冗余输出。

## 运行方式

```bash
# 全部执行
pytest tests/graph/test_render.py -v

# 仅运行环图引用标记测试
pytest tests/graph/test_render.py -k "cycle" -v

# 仅运行深链回归测试
pytest tests/graph/test_render.py -k "deep" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestUtilRender` | < 0.2s（5000 节点纯字符串构造） |

## 重要细节
- `make_node` 默认 `execution_mode="serial"`、`max_workers=2`，调用方可按需覆盖。
- `test_render_structure_list` 断言 `rendered_list[1]` 包含根节点标签，因为实现会先输出上边框。
- 深链测试的预期行数 `DEEP + 2` 由「上边框 + 5000 个节点行 + 下边框」构成。

## 注意事项
- 本模块是早期 `test_serialize.py` 拆分/重命名后的渲染专用测试，序列化相关 JSON 行为已不再覆盖。
- 相关实现位于 `src/celestialflow/graph/util_render.py`。
