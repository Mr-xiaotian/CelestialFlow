# GraphSerialize

> 📅 最終更新日: 2026/04/22

`graph/util_serialize.py` は TaskGraph の構造シリアライズとテキスト化を担当します。

## 主な機能

- `build_structure_graph(source_stages, out_edges, stage_runtime_dict)`: ソースノードの集合から再帰的に構造 JSON を構築します。
- `format_structure_list_from_graph(root_roots)`: 構造 JSON を印刷可能なツリー形式のテキストにフォーマットします。

## 出力の特徴

- 循環/参照ノードのマーキング（`is_ref`）をサポートします。
- 複数ソースノード（フォレスト）構造の出力をサポートします。
