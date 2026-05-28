# GraphSerialize

> 📅 最終更新日: 2026/05/28

`graph/util_serialize.py` は TaskGraph の構造シリアライズとテキスト化を担当します。

## 主要機能

- `build_structure_graph(source_stages, out_edges, stage_dict)`: ソースノード集合から再帰的に構造 JSON を構築。
- `format_structure_list_from_graph(roots)`: 構造 JSON を印刷可能なツリー形式テキストにフォーマット。

## 使用例

以下に、グラフシリアライズおよびテキスト化ツールの使用例を示します。

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.graph.util_serialize import (
    build_structure_graph,
    format_structure_list_from_graph,
)

# 1. シンプルな DAG グラフを構築
s1 = TaskStage("Fetch", func=lambda x: x)
s2 = TaskStage("Parse", func=lambda x: x * 2)
s3 = TaskStage("Save", func=lambda x: x + 1)

graph = TaskGraph()
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 2. ソースノードを取得
sources = graph.get_source_stages()
print(f"ソースノード数: {len(sources)}")

# 3. 構造 JSON を構築
graph_json = build_structure_graph(
    source_stages=sources,
    out_edges=graph.out_edges,
    stage_dict=graph.stage_dict,
)
print(f"構造 JSON: {graph_json}")

# 4. ツリーテキストにフォーマット
rendered = format_structure_list_from_graph(graph_json)
for line in rendered:
    print(line)

# 出力例：
# +-------------------------------------------+
# | Fetch::<lambda> (S:serial, E:serial)       |
# | ╘-->Parse::<lambda> (S:serial, E:serial)   |
# |     ╘-->Save::<lambda> (S:serial, E:serial)|
# +-------------------------------------------+
```

### TaskGraph 組み込みメソッド経由

`TaskGraph` は便利な `get_structure_json()` と `get_structure_list()` メソッドを提供します：

```python
from celestialflow import TaskGraph, TaskStage

s1 = TaskStage("Step1", func=lambda x: x.upper())
s2 = TaskStage("Step2", func=lambda x: len(x))
s3 = TaskStage("Step3", func=lambda x: x * 10)

graph = TaskGraph()
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# JSON グラフ構造を取得
json_structure = graph.get_structure_json()
print("JSON 構造:")
import json
print(json.dumps(json_structure, indent=2, ensure_ascii=False))

# フォーマット済みツリーテキストを取得
tree_lines = graph.get_structure_list()
print("\nツリー構造:")
for line in tree_lines:
    print(line)
```

## 出力特性

- 循環/参照ノードのマーキング（`is_ref`）をサポート。
- マルチソースノード（フォレスト）構造の出力をサポート。
