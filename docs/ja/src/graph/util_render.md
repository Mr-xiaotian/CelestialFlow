# GraphRender

> 📅 最終更新日: 2026/08/31

`graph/util_render.py` は、グラフ構造を枠付きのツリー型テキストリストにレンダリングするユーティリティを提供し、`TaskGraph.get_structure_list()` から直接呼び出されます。ログ/CLI におけるタスクグラフのトポロジー可視化に使用されます。

## 主な能力

- `render_structure_list(nodes, edges, source_nodes)`：ノードのメタ情報、隣接リスト、ソースノードリストから、枠付きのツリー型テキストリストを生成します。

## render_structure_list

```python
def render_structure_list(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, list[str]],
    source_nodes: list[str],
) -> list[str]: ...
```

### レンダリングルール

- `source_nodes` をルートとして、`edges` の隣接リストに従ってツリー型テキストに展開します。
- 環や共有サブグラフのノードは一度だけ展開されます。再度出現した場合には ` [Ref]` とマークされます。
- どのルートからもレンダリングされなかった孤立ノードは末尾に追加されます。
- ルートノードには接続記号を描画せず、子ノードには `╞-->` / `╘-->` の接続記号を使用します。
- **明示スタックによる反復 DFS** の先行順走査を使用し、深いチェーングラフで Python の再帰上限（デフォルトで約 1000 層）がトリガーされるのを回避します。
- `+---+` の上下枠を持つ文字列リストを返します。各行のフォーマットは `| <content> |` です。

### パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `nodes` | `dict[str, dict[str, Any]]` | ノードのメタ情報辞書。各ノードには `func_name` / `execution_mode` / `max_workers` フィールドを含める必要があります |
| `edges` | `dict[str, list[str]]` | 出辺隣接リスト `{stage_name: [next_stage_name, ...]}` |
| `source_nodes` | `list[str]` | ソースノード名リスト。空の場合、`edges` から自動的に推測するか、`nodes` の最初のキーを取得します |

### 戻り値

`list[str]` — 各行が 1 つの文字列。最初と最後は `+---+` の枠で、中央は左右に `| ` のマージンを持つコンテンツ行です。

## 使用例

以下の例は、`render_structure_list` の直接呼び出し方と、`TaskGraph.get_structure_list()` を通じた間接呼び出し方を示します。

### 直接呼び出し

```python
from celestialflow.graph.util_render import render_structure_list

# ノードメタ情報: 通常は TaskGraph.get_stages_summary() から取得
nodes = {
    "Fetch": {"func_name": "fetch_data", "execution_mode": "serial", "max_workers": 1},
    "Parse": {"func_name": "parse_data", "execution_mode": "thread", "max_workers": 4},
    "Save":  {"func_name": "save_data",  "execution_mode": "async",  "max_workers": 8},
}

# 出辺隣接リスト
edges = {
    "Fetch": ["Parse"],
    "Parse": ["Save"],
}

# ソースノード
source_nodes = ["Fetch"]

lines = render_structure_list(nodes, edges, source_nodes)
for line in lines:
    print(line)

# 出力例：
# +---------------------------------------------------------------------------+
# | Fetch::fetch_data (E:serial, W:1)                                          |
# | ╘-->Parse::parse_data (E:thread, W:4)                                      |
# |     ╘-->Save::save_data (E:async, W:8)                                     |
# +---------------------------------------------------------------------------+
```

### 空グラフの処理

```python
from celestialflow.graph.util_render import render_structure_list

print(render_structure_list({}, {}, []))
# ['+ No stages defined +']
```

### TaskGraph 内蔵メソッド経由

`TaskGraph.get_structure_list()` は `get_stages_summary()`、`order_graph.out_edges`、`source_names` を自動的に収集し、`render_structure_list` を呼び出します：

```python
from celestialflow import TaskGraph, TaskStage

s1 = TaskStage("Step1", func=lambda x: x.upper())
s2 = TaskStage("Step2", func=lambda x: len(x))
s3 = TaskStage("Step3", func=lambda x: x * 10)

graph = TaskGraph(name="RenderDemo", graph_mode="thread")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

graph.run({s1.get_name(): ["hello"]})

# フォーマット済みツリーテキストを取得
tree_lines = graph.get_structure_list()
for line in tree_lines:
    print(line)
```

## 出力の特徴

- 循環/参照ノードマーク（`[Ref]`）をサポート：あるノードがすでに展開済みで、再度ツリーに現れた場合には ` [Ref]` が付加されます。
- 複数ソースノード（フォレスト）構造の出力をサポート：ルート間は空行で区切られます。
- 未接続ノード（親ノードがなくソースノードリストにも含まれないノード）も、独立したツリーのルートとしてレンダリングされます。
- DFS は明示スタックフレーム `(node_name, prefix, is_last, is_root)` を使用し、再帰版と完全に同じ結果を得られますが、深いチェーングラフを処理できます。

## 他のモジュールとの関係

- `TaskGraph.get_structure_list()` は本関数の主要な呼び出しポイントであり、ログやモニタリングパネルでトポロジーを可視化するために使用されます。
- 入力の `nodes` フィールド名（`func_name` / `execution_mode` / `max_workers`）は `TaskStage.get_summary()` の出力フィールドと一致しています。
