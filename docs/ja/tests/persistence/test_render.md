# tests/persist/test_render.py

> 📅 最終更新日: 2026/10/09

## 役割

`celestialflow.persist.util_render.render_structure_list` の構造レンダリングロジックを検証します。ノードと隣接リストを枠付きツリー型テキストリストにレンダリングできること、空構造と環グラフを正しく処理できること、深連鎖グラフで Python の再帰上限をトリガーしないことを確認します。

> `util_render` はリファクタリング後に `src/celestialflow/graph` から `src/celestialflow/persist` へ移行されました。本テストのミラーも `tests/persist` ディレクトリ配下にあります。

## コアテスト対象

| クラス / オブジェクト | ソース | 説明 |
|-----------|------|------|
| `render_structure_list(nodes, edges, source_nodes)` | `celestialflow.persist.util_render` | ノードリスト、隣接リスト、ソースノードから枠付きツリー型テキストリストを生成し、文字列リスト（先頭と末尾が枠行）を返す |
| `DEEP`（=5000） | 本ファイルの定数 | Python のデフォルト再帰上限（約 1000）を超え、明示的スタックの反復レンダリングロジックのリグレッション用 |

## テストカバレッジマトリックス

### `TestUtilRender`

| ケース | カバレッジ対象 |
|------|---------|
| `test_render_structure_list` | 通常の DAG（`s1→s2/s3→s4`）が `s1` を含むツリーリストをレンダリングし、`[Ref]` マーカーの循環参照行を含む |
| `test_render_structure_list_no_nodes` | 空構造はプレースホルダー `["+ No nodes defined +"]` を返す |
| `test_render_structure_list_cycle` | 環グラフ（`c1→c2→c3→c1`）は一度だけ展開され、重複ノードは `[Ref]` とマークされる。`c1` の出現回数はちょうど 2（初回展開 + バックリファレンス） |
| `test_render_deep_chain_no_recursion_error` | 5000 ノードの深連鎖グラフが再帰上限をトリガーせず、レンダリング行数は `DEEP + 2`（枠 + ノード行 + 枠） |

## 主要テストシナリオ

### `test_render_structure_list_cycle`

- 環 `{"c1": ["c2"], "c2": ["c3"], "c3": ["c1"]}` を構築し、`["c1"]` をルートとしてレンダリング。
- 結合後のテキストで `c1` がちょうど 2 回出現（初回展開 + `[Ref]` バックリファレンス）し、かつ `[Ref]` を含むことをアサート。

### `test_render_deep_chain_no_recursion_error`

- 5000 ノードの単一連鎖（`n0 → n1 → ... → n4999`）を構築。
- `render_structure_list` が `DEEP + 2` 行（先頭末尾の枠 + 5000 ノード行）を返し、先頭が `n0`、末尾が `n4999` であることをアサート。
- このケースは、レンダリングが再帰ではなく**明示的スタックによる反復 DFS**を採用することで Python のデフォルト再帰上限を回避することを検証します。

## 実行方法

```bash
# 全部実行
pytest tests/persist/test_render.py -v

# キーワードでマッチ
pytest tests/persist/test_render.py -k "cycle" -v
pytest tests/persist/test_render.py -k "deep" -v
```

## 注意事項

- 深連鎖ケース（`DEEP=5000`）は `render_structure_list` の内部実装が明示的スタック反復に変更されたことに依存します。再帰実装に戻ると `RecursionError` がトリガーされます。
- 関連実装は `src/celestialflow/persist/util_render.py` にあります。