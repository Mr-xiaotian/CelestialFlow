# 图序列化工具测试 (test_serialize.py)

> 最后更新日期: 2026/06/11

## 作用
验证图结构的序列化和可视化格式化功能，确保图拓扑能被正确转换为 JSON 结构或易读的文本列表。

## 核心测试对象
- `build_structure_graph`: 将邻接表形式的图转换为嵌套的字典结构。
- `format_structure_list_from_graph`: 将嵌套结构转换为带缩进的格式化字符串列表。
- `make_stage`: 测试辅助函数，根据 `stage_mode` × `execution_mode` 组合构造 `TaskStage`。

## 关键测试场景
1. **DAG 序列化**: 验证典型的分层结构（如 s1→{s2,s3}→s4）能否被正确解析，各节点 func_name、stage_mode、execution_mode、max_workers 等属性是否准确。
2. **循环图序列化**: 验证含环图（如 cs1→cs2→cs3→cs1）在序列化时不会陷入死循环。
3. **文本格式化**: 验证生成的字符串列表是否包含预期的模式标记（如 `(S:serial, E:serial, W:2)`）以及引用标记（`[Ref]`）。

## 测试重点
- **引用标记**: 确保在非树状 DAG 或循环图中，重复出现的节点仅在首次出现时展示详情，后续出现均标记为引用。
- **递归终止**: 确保序列化算法在处理循环引用时能够正确识别已访问节点并及时终止递归。

## 运行方式

```bash
# 全部执行
pytest tests/graph/test_serialize.py -v

# 匹配特定测试名称
pytest tests/graph/test_serialize.py -k "dag" -v
pytest tests/graph/test_serialize.py -k "cyclic" -v
pytest tests/graph/test_serialize.py -k "format" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestUtilSerialize`（DAG/循环/格式化） | ~0.1s 整体 |

## 重要细节
- 使用 `make_stage` 辅助函数构造不同 `stage_mode` × `execution_mode` 组合的测试节点。
- 测试覆盖了 JSON 数据层和最终展示文本层。

## 注意事项
- 测试代码位于 `tests/graph/test_serialize.py`，对应实现位于 `src/celestialflow/graph/util_serialize.py`。
