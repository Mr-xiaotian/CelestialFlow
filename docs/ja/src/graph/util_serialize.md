# GraphSerialize

> 📅 最終更新日: 2026/05/15

`graph/util_serialize.py` は TaskGraph の構造シリアライズとテキスト化を担当します。

## 主要機能

- `build_structure_graph(source_stages, out_edges, stage_runtime_dict)`: ソースノード集合から再帰的に構造 JSON を構築。
- `format_structure_list_from_graph(roots)`: 構造 JSON を印刷可能なツリー形式テキストにフォーマット。

## 出力特性

- 循環/参照ノードのマーキング（`is_ref`）をサポート。
- マルチソースノード（フォレスト）構造の出力をサポート。
