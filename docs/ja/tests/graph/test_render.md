# グラフ構造レンダリングテスト (test_render.py)

> 📅 最終更新日: 2026/08/31

## 役割
`celestialflow.graph.util_render.render_structure_list` がグラフ構造（ノードメタ情報、隣接リスト、ソースノード）を枠付きツリー型テキストリストにレンダリングできることを検証し、通常の DAG、循環グラフ、空グラフ、超深鎖などのシナリオをカバーし、深いグラフのレンダリングが Python のデフォルト再帰上限をトリガーしないことを確認します。

## コアテスト対象
- `render_structure_list(nodes, edges, source_nodes)`: レンダリング関数。枠付きの文字列リストを返します。
- `DEEP = 5000`: Python のデフォルト再帰上限（約 1000）を超える深鎖規模。イテレーション版レンダリングロジックのリグレッション用。
- `make_node(name, mode, workers)`: ヘルパー関数。`func_name` / `execution_mode` / `max_workers` を含むノードメタ情報辞書を構築します。

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 | 主なアサーション |
|------------|---------|------------|------------------|
| `TestUtilRender` | 4 | 通常 DAG レンダリング、空構造、循環参照マーカー、超深鎖レンダリング | ノードラベル書式 `(E:<mode>, W:<workers>)`；空構造は `"+ No stages defined +"` を返す；循環の重複ノードは一度だけ展開され `[Ref]` でマークされる；深鎖の長さは `DEEP + 2` で `RecursionError` をスローしない |

## 主要テストシナリオ

1. **通常 DAG レンダリング** (`test_render_structure_list`): 4 ノードのダイヤモンド構造（s1→{s2,s3}→s4）。ノードラベルの書式が正しく、リストに `[Ref]` マーカーが含まれることを検証。
2. **空構造** (`test_render_structure_list_no_nodes`): 空の `nodes` はプレースホルダー `"+ No stages defined +"` を返します。
3. **循環参照マーカー** (`test_render_structure_list_cycle`): 3 ノードの閉ループ（c1→c2→c3→c1）。`c1` が 2 回出現（初回展開 + `[Ref]` バックリファレンス）し、出力全体に `[Ref]` が含まれることを検証。
4. **超深鎖が再帰上限をトリガーしない** (`test_render_deep_chain_no_recursion_error`): 5000 ノードの線形鎖。レンダリング行数がちょうど `DEEP + 2`（上枠 + ノード行 + 下枠）であり、最初と最後のノードラベルが正しいことを検証。

## テストの重点
- **ノードラベル書式**: `name::func_name (E:execution_mode, W:max_workers)`。参照ノードには ` [Ref]` が付加されます。
- **再帰安全性**: 実装は明示的スタックによる反復 DFS を採用しており、深鎖レンダリングは `RecursionError` をトリガーしません。
- **空入力と境界**: 空の `nodes` は固定プレースホルダーテキストを返し、空リストのレンダリングを回避します。
- **循環グラフ収束**: 共有サブグラフのノードは一度だけ展開され、無限ループや冗長な出力を防ぎます。

## 実行方法

```bash
# 全部実行
pytest tests/graph/test_render.py -v

# 循環参照マーカーテストのみ実行
pytest tests/graph/test_render.py -k "cycle" -v

# 深鎖リグレッションテストのみ実行
pytest tests/graph/test_render.py -k "deep" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestUtilRender` | < 0.2s（5000 ノードの純粋な文字列構築） |

## 重要な詳細
- `make_node` のデフォルトは `execution_mode="serial"`、`max_workers=2`。呼び出し側は必要に応じて上書き可能。
- `test_render_structure_list` は `rendered_list[1]` にルートノードラベルが含まれることをアサートします（実装がまず上枠を出力するため）。
- 深鎖テストの予想行数 `DEEP + 2` は「上枠 + 5000 ノード行 + 下枠」で構成されます。

## 注意事項
- 本モジュールは旧 `test_serialize.py` の分割/リネーム後のレンダリング専用テストです。シリアライズ関連の JSON 動作はもはやカバーされません。
- 関連実装は `src/celestialflow/graph/util_render.py` にあります。
