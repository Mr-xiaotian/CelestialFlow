# GraphSerialize

> 📅 最后更新日期: 2026/04/22

`graph/util_serialize.py` 负责 TaskGraph 的结构序列化与文本化。

## 主要能力

- `build_structure_graph(source_stages, out_edges, stage_runtime_dict)`：从源节点集合递归构建结构 JSON。
- `format_structure_list_from_graph(root_roots)`：将结构 JSON 格式化为可打印树形文本。

## 输出特点

- 支持循环/引用节点标记（`is_ref`）。
- 支持多源节点（forest）结构输出。
