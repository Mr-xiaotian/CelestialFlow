# task_statuses.ts

> 📅 最終更新日: 2026/05/15

各ノードの実行ステータスデータの読み込みとダッシュボードステータスカードのレンダリングを管理します。

## 型定義

```ts
type NodeStatus = {
  status: number;            // 0=未実行, 1=実行中, 2=停止済み
  tasks_processed: number;   // 処理済みタスク数
  tasks_pending: number;     // 待機中タスク数
  tasks_succeeded: number;   // 累計成功数
  tasks_failed: number;      // 累計失敗数
  tasks_duplicated: number;  // 累計重複数
  stage_mode: string;        // serial / thread
  execution_mode: string;    // serial / thread / async
  start_time: number;        // Unix タイムスタンプ（秒）
  elapsed_time: number;      // 経過秒数
  remaining_time: number;    // 推定残り秒数
  task_avg_time: string;     // 平均タスク所要時間文字列
};
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `nodeStatuses` | `Record<string, NodeStatus>` | すべてのノードの現在のステータス |
| `lastNodeStatuses` | `Record<string, NodeStatus>` | 前回のステータススナップショット、差分計算に使用 |
| `statusRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |
| `draggingNodeName` | `string \| null` | 現在ドラッグ中のノード名、レンダリング時にスキップ |

## 関数

### `loadStatuses()`

`GET /api/pull_status?known_rev=N` から非同期でノードステータスを取得します。サーバーデータが変更されていない場合（`body.data === null`）、`false` を返します。それ以外の場合は現在の `nodeStatuses` を `lastNodeStatuses` として保存し、`nodeStatuses` と `statusRev` を更新して `true` を返します。

---

### `initSortableDashboard()`

ノードカードのドラッグ＆ドロップソート（Sortable.js）を初期化します。モバイルデバイスでは初期化をスキップします。

ドラッグ中は `draggingNodeName` を記録し、`renderDashboard()` がドラッグ中のカードを再描画して位置がジャンプするのを防止します。

---

### `renderDashboard()`

`nodeStatuses` を走査し、各ノードのステータスカードを生成して `#dashboard-grid` に挿入します。

差分は `lastNodeStatuses` から計算され（例：`data.tasks_succeeded - last.tasks_succeeded`）、カラー付き小文字で表示されます。

**カードの内容：**
- ノード名
- 統計データ：成功数、待機中、エラー数（クリックでジャンプ可能）、重複数、ステージモード、実行モード
- 開始時間
- タスク完了率プログレスバー（4 セグメント：成功/エラー/重複/待機）、経過/残り時間、平均所要時間、パーセンテージ

エラー数字には `error-clickable` スタイルが付き、クリックすると `switchToErrorsTab(node)`（`utils.ts` で定義）を呼び出してジャンプし、フィルタをプリセットします。

## カードステータススタイル

| `status` 値 | CSS クラス | 意味 |
|-------------|-----------|------|
| `0` | `node-card` | 未実行 |
| `1` | `node-card status-running` | 実行中 |
| `2` | `node-card status-stopped` | 停止済み |
