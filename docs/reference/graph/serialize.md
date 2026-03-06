# GraphSerialize

`graph/serialize.py` 负责 TaskGraph 的结构序列化与文本化。

## 主要能力

- `build_structure_graph(root_stages)`：从根节点集合递归构建结构 JSON。
- `format_structure_list_from_graph(root_roots)`：将结构 JSON 格式化为可打印树形文本。

## 输出特点

- 支持循环/引用节点标记（`is_ref`）。
- 支持多根节点（forest）结构输出。
