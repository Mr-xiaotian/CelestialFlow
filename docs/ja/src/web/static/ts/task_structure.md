# task_structure.ts

> 📅 最終更新日: 2026/04/22

タスクグラフ構造データの読み込みと Mermaid フローチャートのオンデマンドレンダリングを管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `structureData` | `any[]` | バックエンドから取得したタスクグラフのルートノード配列 |
| `structureRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |

## 関数

### `loadStructure()`

`GET /api/pull_structure?known_rev=N` から非同期でグラフ構造配列を取得します。サーバー側のデータが変更されていない場合（`body.data === null`）、`false` を返します。それ以外の場合は `structureData` と `structureRev` を更新し、`true` を返します。

---

### `getNodeId(node)`

ノード名内の非単語文字を `_` に置換し、Mermaid 互換のノード ID を生成します。

---

### `getShapeWrappedLabel(label, shape)`

形状タイプに基づいて Mermaid ノードラベル構文を生成します。

| `shape` 値 | Mermaid 構文 | 用途 |
|-----------|-------------|------|
| `box`（デフォルト）| `[label]` | 標準矩形ノード |
| `round` | `(label)` | 角丸矩形 |
| `circle` | `((label))` | 円形 |
| `rhombus` | `{{label}}` | ひし形（Router ノード） |
| `subgraph` | `[[label]]` | サブルーチンボックス（Splitter ノード） |
| `parallelogram` | `[/label/]` | 平行四辺形（Redis トランスポートノード） |
| `db` | `[(label)]` | データベースシリンダー |
| `hex` | `{{{label}}}` | 六角形 |
| `arrow` | `>label]` | 矢印形 |

---

### `renderMermaidStructure(statuses?)`

`structureData` と渡された `statuses`（`Record<string, NodeStatus>`、デフォルトは空オブジェクト）から Mermaid コードを構築し、DOM にレンダリングします。

**フロー:**

1. `structureData` を走査（DFS `walk()`）:
   - `func_name` に基づいてノード形状を決定（`_split` → subgraph、`_route` → rhombus、`_transport/_source/_ack` → parallelogram）
   - `nodeStatuses[tag].status` に基づいてノードスタイルクラスを決定（`greenNode` / `greyNode` / `whiteNode`）
   - すべてのエッジを収集（Set で重複排除）
2. 現在のテーマに基づいて `classDef` カラースキームを選択
3. `graph TD` Mermaid コードを生成
4. 新しい `<div>` を作成して古い `#mermaid-container` を置換し、`window.mermaid.run()` を呼び出してレンダリング

**ノード状態の色:**

| `status` | スタイルクラス | 意味 |
|----------|--------------|------|
| `1` | `greenNode` | 実行中 |
| `2` | `greyNode` | 停止済み |
| データなし | `whiteNode` | 未開始 |
