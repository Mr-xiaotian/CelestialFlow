# task_analysis.ts

> 📅 最終更新日: 2026/04/22

グラフ分析情報の読み込みと分析パネルのレンダリングを管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `analysisData` | `Record<string, any>` | バックエンドから取得した分析データ |
| `analysisRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |

## 関数

### `loadAnalysis()`

`GET /api/pull_analysis?known_rev=N` から非同期で分析データを取得します。サーバーデータが変更されていない場合（`body.data === null`）、`false` を返します。それ以外の場合は `analysisData` と `analysisRev` を更新し、`true` を返します。

---

### `renderAnalysisInfo()`

分析データを `#analysis-info` コンテナにレンダリングします。

データが空の場合、プレースホルダーテキスト「分析情報なし」を表示します。

**表示フィールド：**

| `analysisData` フィールド | 表示ラベル | 説明 |
|--------------------------|-----------|------|
| `class_name` | 構造タイプ | TaskGraph のトポロジークラス名（TaskChain、TaskLoop など） |
| `isDAG` | DAG かどうか | ブール値、「はい（非循環）」または「いいえ（循環あり）」をカラーマーカー付きで表示 |
| `schedule_mode` | スケジュールモード | `eager` または `staged` |
| `layers_dict` | レイヤー数 | `Object.keys(layers_dict).length` がレイヤー数 |

`isDAG` が `true` の場合、テキストは `ok`（緑）スタイル。`false` の場合は `warn`（オレンジ）スタイル。
