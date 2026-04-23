# task_statuses.ts

> 📅 最終更新日: 2026/04/22

各ステージの実行状態データの読み込みとダッシュボード状態カードのレンダリングを管理します。

## 型定義

```ts
type NodeStatus = {
  status: number;            // 0=未実行, 1=実行中, 2=停止済み
  tasks_processed: number;   // 処理済みタスク数
  tasks_pending: number;     // 待機中タスク数
  tasks_succeeded: number;   // 累計成功数
  add_tasks_succeeded: number; // 今サイクルの新規成功数
  add_tasks_pending: number;
  tasks_failed: number;
  add_tasks_failed: number;
  tasks_duplicated: number;
  add_tasks_duplicated: number;
  stage_mode: string;        // serial / thread / process
  execution_mode: string;    // serial / thread / process / async
  start_time: number;        // Unix タイムスタンプ（秒）
  elapsed_time: number;      // 経過秒数
  remaining_time: number;    // 推定残り秒数
  task_avg_time: string;     // 平均タスク処理時間文字列
};
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `nodeStatuses` | `Record<string, NodeStatus>` | 全ステージの現在の状態 |
| `statusRev` | `number` | 前回取得時のバージョン番号、増分取得（`known_rev`）に使用 |
| `draggingNodeName` | `string \| null` | 現在ドラッグ中のステージ名。レンダリング時にスキップ |

## 関数

### `loadStatuses()`

`GET /api/pull_status?known_rev=N` から非同期でステージ状態を取得します。サーバー側のデータが変更されていない場合（`body.data === null`）、`false` を返します。それ以外の場合は `nodeStatuses` と `statusRev` を更新し、`true` を返します。

---

### `initSortableDashboard()`

ステージカードのドラッグ&ドロップソートを初期化します（Sortable.js）。モバイルデバイスでは初期化をスキップします。

ドラッグ操作中に `draggingNodeName` を記録し、`renderDashboard()` がドラッグ中のカードを再描画して位置がジャンプすることを防ぎます。

---

### `renderDashboard()`

`nodeStatuses` を走査し、各ステージの状態カードを生成して `#dashboard-grid` に挿入します。

**カード内容:**
- ステージ名 + 状態バッジ（未実行 / 実行中 / 停止済み）
- 統計データ: 成功数、待機中、エラー数（クリックでナビゲーション）、重複数、ステージモード、実行モード
- 開始時刻
- タスク完了率プログレスバー（経過/残り時間、平均処理時間、パーセンテージ付き）

エラー数字は `error-clickable` スタイルを持ち、クリックすると `switchToErrorsTab(node)`（`utils.ts` で定義）を呼び出してナビゲーションとフィルター設定を行います。

## バッジ状態マッピング

| `status` 値 | CSS クラス | テキスト |
|-------------|-----------|---------|
| `0` | `badge-inactive` | 未実行 |
| `1` | `badge-running` | 実行中 |
| `2` | `badge-completed` | 停止済み |
