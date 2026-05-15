# task_summary.ts

> 📅 最終更新日: 2026/04/22

全体統計データの読み込みとサマリーパネルのレンダリングを管理します。

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `summaryData` | `Record<string, any>` | 集計統計データ、バックエンドから取得 |
| `summaryRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |

## 関数

### `loadSummary()`

`GET /api/pull_summary?known_rev=N` から非同期でサマリーデータを取得します。サーバーデータが変更されていない場合（`body.data === null`）、`false` を返します。それ以外の場合は `summaryData` と `summaryRev` を更新し、`true` を返します。

---

### `renderSummary()`

`summaryData` の統計値を `#summary-card` パネル内の各 DOM 要素に更新します。

**表示フィールド：**

| `summaryData` フィールド | DOM 要素 | 説明 |
|-------------------------|---------|------|
| `total_succeeded` | `#total-succeeded` | 総成功タスク数 |
| `total_pending` | `#total-pending` | 総待機タスク数 |
| `total_failed` | `#total-failed` | 総失敗タスク数 |
| `total_duplicated` | `#total-duplicated` | 総重複タスク数 |
| `total_nodes` | `#total-nodes` | アクティブノード数 |
| `total_remain` | `#total-remain` | 総残り時間（`formatDuration()` でフォーマット済み） |

`total_failed > 0` の場合、`#total-failed` に `error-clickable` スタイルが追加されます。クリックすると `switchToErrorsTab()`（`utils.ts` で定義、ノードフィルタのプリセットなし）を呼び出してエラーログページにジャンプします。
