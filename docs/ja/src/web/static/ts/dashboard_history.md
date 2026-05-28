# dashboard_history.ts

> 📅 最終更新日: 2026/05/28

ノードごとの複数指標履歴データの維持と折れ線グラフの初期化・再描画を管理します。履歴データは完全にフロントエンドで状態スナップショットによって蓄積されます。

## 型定義

```ts
/** グラフ表示切替可能な履歴指標キーフィールド */
type HistoryMetricKey =
  | "tasks_processed"
  | "tasks_succeeded"
  | "tasks_failed"
  | "tasks_duplicated"
  | "tasks_pending"
  | "delta_tasks_processed"
  | "delta_tasks_succeeded"
  | "delta_tasks_failed"
  | "delta_tasks_duplicated";

/** ある時点での単一ノードの履歴サンプルポイント */
type NodeHistoryPoint = {
  timestamp: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  tasks_duplicated: number;
  tasks_pending: number;
};

type NodeHistory = NodeHistoryPoint[];
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | 各ノードのローカル維持履歴データシーケンス |
| `progressChart` | `any` | Chart.js インスタンス |
| `hiddenNodes` | `Set<string>` | 折れ線グラフで非表示のノード集合。localStorage に永続化 |
| `currentHistoryMetric` | `HistoryMetricKey` | グラフに表示する現在の指標。デフォルトは `tasks_processed` |
| `metricDots` | `NodeListOf<HTMLLabelElement>` | すべての `.metric-dot` ラベル要素。指標表示の切り替えに使用 |

## 補助関数

### `getColor(index)`

インデックスに基づいて事前定義されたテーマ色を返します（CSS 変数から読み取り）。異なるノードの折れ線を区別するために使用。

| インデックス | CSS 変数 | 説明 |
|------------|---------|------|
| 0 | `--cornflower-500` | コーンフラワーブルー |
| 1 | `--jade-500` | ジェードグリーン |
| 2 | `--marigold-500` | マリーゴールドイエロー |
| 3 | `--crimson-500` | クリムゾン |
| 4 | `--violet-500` | バイオレット |
| 5+ | 巡回剰余、9色プール | — |

### `getHistoryMetricLabelKey(metric)`

`HistoryMetricKey` を i18n 翻訳キーにマッピングします。

| 入力 | 出力 |
|------|------|
| `tasks_processed` | `chart.metric.processed` |
| `tasks_succeeded` | `chart.metric.succeeded` |
| `tasks_failed` | `chart.metric.failed` |
| `tasks_duplicated` | `chart.metric.duplicated` |
| `tasks_pending` | `chart.metric.pending` |
| `delta_tasks_processed` | `chart.metric.deltaProcessed` |
| `delta_tasks_succeeded` | `chart.metric.deltaSucceeded` |
| `delta_tasks_failed` | `chart.metric.deltaFailed` |
| `delta_tasks_duplicated` | `chart.metric.deltaDuplicated` |

### `updateHistoryMetricButtons()`

`metricDots` を走査し、`currentHistoryMetric` に基づいて一致する `<label>` に `.active` クラスを追加し、他からは削除します。

### `updateChartAxisLabels()`

折れ線グラフの X/Y 軸タイトルテキストを更新し、それぞれ現在の言語の「時間」と対応する指標名にマッピングします。

---

## コアロジック関数

### `initChart()`

Chart.js 折れ線グラフインスタンスを初期化（または再構築）します。

- 既存のインスタンスがある場合は最初に `destroy()` を呼び出す
- `getChartThemeColors()` を呼び出して現在のテーマの文字色、グリッド色、軸色を読み取る
- 凡例クリックイベントを設定：ノードの表示/非表示を切り替え、localStorage に同期
- **`animation` を使用せず、リアルタイムリフレッシュ性能を向上させるために遷移アニメーションを無効化**

### `updateChartTheme()`

インスタンスを再構築せずに折れ線グラフの配色（文字色、グリッド線色、軸色）を更新。テーマ切り替え後に呼び出されます。

### `updateChartData()`

`currentHistoryMetric` に基づいて `nodeHistories` の対応する指標データを折れ線グラフに書き込み、リフレッシュします。

### `appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses)`

コアロジック：最新の状態スナップショットに基づいて履歴ポイントを追加します。

- **リセット検出**: ノードの `start_time` が変更された場合（再起動）や `tasks_processed` が後退した場合（ロールバック）、そのノードの履歴をクリア。
- **重複排除**: タイムスタンプが同じ場合は最後のポイントを更新、そうでない場合は新しいポイントを追加。
- すべての変更は `getCurrentHistoryLimit()` によるトリミング制約を受けます。

### `extractProgressData(histories, metric)`

ローカルで維持されている `nodeHistories` を Chart.js 互換の `{x, y}` 座標ポイント配列にマッピングします。

- `metric` パラメータが抽出する指標を決定（例: `tasks_succeeded`, `tasks_failed` など）。
- **デルタモード**: `metric` が `delta_` で始まる場合（例: `delta_tasks_processed`）、累積値を差分変化率（`dy/dt`）に変換。
  - 計算式: `dy = point[sourceMetric] - prev[sourceMetric]`, `dt = point.timestamp - prev.timestamp`
  - 最初のポイントは強制的に `y = 0` を返す（差分計算のための前ポイントがないため）
  - 絶対累積値ではなく指標の変化傾向を表示するために使用

### `trimNodeHistories()`

`webConfig.historyLimit` に基づいてローカルで維持されている履歴ポイント数をトリミングし、パフォーマンスを確保。履歴データが変更されたかどうかを示すブール値を返します。

### `getCurrentHistoryLimit()`

現在の履歴曲線保持ポイント制限を取得。`webConfig?.historyLimit` を優先し、無効な場合はデフォルトで `20` を返します。

### `getChartThemeColors()`

現在のテーマ（ダーク/ライト）のグラフ文字色、グリッド色、境界色を CSS 変数から読み取ります。

| テーマ | 文字色 | グリッド色 | 境界色 |
|--------|--------|----------|--------|
| ライト | `--carbon-900` | `--carbon-200` | `--carbon-300` |
| ダーク | `--carbon-200` | `--carbon-600` | `--carbon-500` |

---

## 指標切替器（モジュールレベル自動実行）

```ts
function initHistoryMetricSwitcher() { ... }
initHistoryMetricSwitcher(); // モジュールレベル即時実行
```

`initHistoryMetricSwitcher()` は `dashboard_history.js` ファイルの先頭でモジュールスコープで自動的に呼び出され、**`main.js` からはアクティブに呼び出されません**。以下の役割を担います：
1. `metricDots` ボタンのアクティブスタイルを同期
2. クリックイベントをバインドし、`currentHistoryMetric` を切り替えた後に軸タイトルを更新して再描画

## データフロー

```
GET /api/pull_status
  └─ { timestamp, data: { node: NodeStatus } }
        └─ appendStatusSnapshotToHistory() -> nodeHistories
              └─ updateChartData(currentHistoryMetric) -> Chart.js 再描画
```

## 使用例

### 手動でのグラフ初期化/更新の呼び出し

以下の例はブラウザコンソールまたはカスタムスクリプトでグラフを手動操作する方法を示します：

```typescript
// ページが読み込まれ、グローバル変数が利用可能と仮定

// 1. グラフを手動で初期化（まだ初期化されていない場合）
initChart();
console.log("グラフを初期化しました");

// 2. 手動で履歴データポイントを構築して追加
const timestamp = Date.now() / 1000;  // 現在のタイムスタンプ（秒）
const statuses: Record<string, NodeStatus> = {
    "Processor": {
        status: 1,
        tasks_processed: 150,
        tasks_succeeded: 145,
        tasks_failed: 3,
        tasks_duplicated: 2,
        tasks_pending: 10,
        stage_mode: "thread",
        execution_mode: "thread",
        start_time: timestamp - 300,
        elapsed_time: 300,
        remaining_time: 20,
        task_avg_time: "2.00s/it",
    },
    "Validator": {
        status: 1,
        tasks_processed: 80,
        tasks_succeeded: 78,
        tasks_failed: 1,
        tasks_duplicated: 1,
        tasks_pending: 5,
        stage_mode: "serial",
        execution_mode: "serial",
        start_time: timestamp - 250,
        elapsed_time: 250,
        remaining_time: 15,
        task_avg_time: "3.12s/it",
    },
};

// 3. 状態スナップショットを履歴シーケンスに追加
// appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses)
// これは自動的に nodeHistories グローバル変数を更新します

// 4. 現在表示されている指標を切り替え
// currentHistoryMetric = "tasks_succeeded";
// updateChartData();  // グラフをリフレッシュ

// 5. 指標の切り替え（異なる指標ボタンのクリックをシミュレート）
function switchMetric(metric: HistoryMetricKey) {
    // currentHistoryMetric = metric;
    // updateHistoryMetricButtons();
    // updateChartData();
    console.log(`指標を切り替え: ${metric}`);
}

switchMetric("tasks_failed");  // 失敗傾向を表示
switchMetric("tasks_pending"); // 待機キューの傾向を表示

// 6. 手動で履歴データをトリミング（最後の N 件を強制保持）
// webConfig.historyLimit = 10;
// const changed = trimNodeHistories();
// if (changed) updateChartData();

// 7. テーマ切り替え後にグラフの色を更新
// updateChartTheme();
```

### 履歴データの構築と直接レンダリング

```typescript
// 完全な nodeHistories データを直接手動で構築
const mockHistory: Record<string, NodeHistory> = {
    "Processor": [
        { timestamp: 1000, tasks_processed: 10, tasks_succeeded: 9, tasks_failed: 1, tasks_duplicated: 0, tasks_pending: 90 },
        { timestamp: 1005, tasks_processed: 25, tasks_succeeded: 23, tasks_failed: 1, tasks_duplicated: 1, tasks_pending: 75 },
        { timestamp: 1010, tasks_processed: 40, tasks_succeeded: 37, tasks_failed: 2, tasks_duplicated: 1, tasks_pending: 60 },
        { timestamp: 1015, tasks_processed: 55, tasks_succeeded: 51, tasks_failed: 2, tasks_duplicated: 2, tasks_pending: 45 },
        { timestamp: 1020, tasks_processed: 70, tasks_succeeded: 65, tasks_failed: 3, tasks_duplicated: 2, tasks_pending: 30 },
    ],
};

// nodeHistories = mockHistory;
// updateChartData();  // 折れ線グラフにレンダリング

// getColor を使用してノードの折れ線色を取得
// const color = getColor(0);  // 1番目のノード、コーンフラワーブルー
```
