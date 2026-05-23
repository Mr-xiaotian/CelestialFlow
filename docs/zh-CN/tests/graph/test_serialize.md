# 图序列化工具测试 (test_serialize.py)

> 最后更新日期: 2026/05/23

## 作用
验证图结构的序列化和可视化格式化功能，确保图拓扑能被正确转换为树状 JSON 结构或易读的文本列表。

## 核心测试对象
- `build_structure_graph`: 将邻接表形式的图转换为嵌套的树状字典结构。
- `format_structure_list_from_graph`: 将嵌套结构转换为带缩进的格式化字符串列表。

## 关键测试流程
1. **DAG 序列化**: 验证典型的分层结构（如 A -> {B, C} -> D）能否被正确解析，并检查 `is_ref` 标记是否在节点被多次引用时正确设置。
2. **循环图序列化**: 验证含环图（如 A -> B -> C -> A）在序列化时不会陷入死循环，且循环点能被标记为 `is_ref: True`。
3. **文本格式化**: 验证生成的字符串列表是否包含预期的缩进、函数名、模式标记（如 `(S:serial, E:serial)`）以及引用标记（`[Ref]`）。

## 测试重点
- **引用标记 (is_ref)**: 确保在非树状 DAG 或循环图中，重复出现的节点仅在首次出现时展示详情，后续出现均标记为引用。
- **递归终止**: 确保序列化算法在处理循环引用时能够正确识别已访问节点并及时终止递归。

## 运行方式

```bash
# 全部执行
pytest tests/graph/test_serialize.py -v

# 匹配特定测试名称
pytest tests/graph/test_serialize.py -k "dag" -v
pytest tests/graph/test_serialize.py -k "cycle" -v
pytest tests/graph/test_serialize.py -k "format" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestUtilSerialize`（DAG/循环/格式化） | ~0.1s 整体 |

## 重要细节
- 使用 `create_mock_stage_runtime` 辅助函数创建包含模拟队列和日志组件的运行时环境。
- 测试覆盖了 JSON 数据层和最终展示文本层。

## 注意事项
- 测试代码位于 `tests/graph/test_serialize.py`，对应实现位于 `src/celestialflow/graph/util_serialize.py`。
