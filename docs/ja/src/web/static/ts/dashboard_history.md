# dashboard_history.ts

> 📅 最終更新日: 2026/06/11

ノードの多指標履歴データの維持と折れ線グラフの初期化・再描画を管理します。履歴データは完全にフロントエンドで状態スナップショットの累積によって構築され、独立したバックエンド API に依存しません。

## 型定義

```typescript
/** 履歴グラフで切り替え表示可能な指標フィールドキー */
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

/** 単一ノードのある時点での履歴サンプリングポイント */
type NodeHistoryPoint = {
  timestamp: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  tasks_duplicated: number;
  tasks_pending: number;
};

type NodeHistory = NodeHistoryPoint[];

type ThemeColors = {
  text: string;   // 座標軸と凡例のテキスト色
  grid: string;   // グリッド線の色
  border: string; // 座標軸ボーダーの色
};
```

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | 各ノードのローカルで維持される履歴データシーケンス |
| `progressChart` | `ChartInstance \| null` | Chart.js 折れ線グラフインスタンス |
| `hiddenNodes` | `Set<string>` | 凡例でユーザーが手動で非表示にしたノードの集合（ページライフサイクル内のみ保持、**永続化しない**） |
| `currentHistoryMetric` | `HistoryMetricKey` | 現在グラフに表示されている指標、デフォルト `"tasks_processed"` |
| `metricDots` | `NodeListOf<HTMLLabelElement>` | すべての `.metric-dot` ラベル要素、指標表示の切り替えに使用 |

## 補助関数

### `getColor(index: number): string`

インデックスに基づいて CSS 変数から事前定義されたテーマ色を読み取り、異なるノードの折れ線を区別します。全 9 色で巡回剰余。

| Index | CSS 変数 | 説明 |
|-------|---------|------|
| 0 | `--cornflower-500` | コーンフラワーブルー |
| 1 | `--jade-500` | ジェイドグリーン |
| 2 | `--marigold-500` | マリーゴールドイエロー |
| 3 | `--crimson-500` | クリムゾンレッド |
| 4 | `--violet-500` | バイオレット |
| 5 | `--rose-500` | ローズレッド |
| 6 | `--jade-400` | ジェイドグリーン（淡） |
| 7 | `--sky-500` | スカイブルー |
| 8 | `--amber-500` | アンバーオレンジ |

### `getHistoryMetricLabelKey(metric: HistoryMetricKey): string`

`HistoryMetricKey` を国際化翻訳キーにマッピングします。

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

### `updateHistoryMetricButtons(): void`

`metricDots` を走査し、`currentHistoryMetric` に基づいて一致する `<label>` に `.active` クラスを追加し、残りから削除します。

### `updateChartAxisLabels(): void`

折れ線グラフの X/Y 軸タイトルテキストを更新し、現在の言語の「時間」と対応する指標名にマッピングします。

---

## コアロジック関数

### `initChart(): void`

Chart.js 折れ線グラフインスタンスを初期化（または再構築）します。

- 既存のインスタンスがある場合、まず `destroy()` を呼び出して破棄
- `getChartThemeColors()` を呼び出して現在のテーマのテキスト色、グリッド色、軸線色を読み取り
- 凡例クリックイベントを設定：ノードの表示/非表示を切り替え `hiddenNodes` Set に同期
- **アニメーション無効**（`animation: false`）でリアルタイムリフレッシュ性能を向上
- インタラクションモードは `index`、`intersect: false`

### `updateChartTheme(): void`

折れ線グラフのカラースキーム（テキスト色、グリッド線色、軸線色）を更新します。テーマ切り替え後に呼び出され、インスタンスの再構築は不要です。

### `updateChartData(): void`

`currentHistoryMetric` に基づいて `extractProgressData()` を呼び出し、`nodeHistories` 内の対応する指標データを折れ線グラフに書き込み更新します。`legendItem.hidden` を同期して凡例のレンダリングが `hiddenNodes` と一致するようにします。

### `appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses?): boolean`

コアロジック：最新の状態スナップショットに基づいて履歴ポイントを追加します。

- **リセット検出**: ノードの `start_time` が変化（再起動）した場合、または `tasks_processed` が後退（ロールバック）した場合、そのノードの履歴をクリアします。
- **重複排除**: タイムスタンプが同じ場合は最後のポイントを更新、それ以外は新しいポイントを追加します。
- **トリミング**: すべての変更は `getCurrentHistoryLimit()` の制約を受けます。
- **戻り値**: `boolean` — 履歴データが実際に変更されたかどうか。

### `extractProgressData(histories, metric): Record<string, Array<{x: number; y: number}>>`

ローカルで維持される `nodeHistories` マッピングを Chart.js 互換の `{x, y}` 座標点配列に変換します。

- **累積モード**: サンプリングポイントの元のフィールド値を直接読み取ります。
- **増分モード（delta）**: `metric` が `delta_` で始まる場合、隣接サンプリングポイントの差分/時間差を計算して毎秒レートを求めます。最初のポイントは強制的に `y = 0` となります。

### `trimNodeHistories(): boolean`

`webConfig.dashboard.historyLimit` に基づいてフロントエンドでローカルに維持される履歴ポイント数をトリミングします。履歴データが変更されたかどうかを示すブール値を返します。

### `getCurrentHistoryLimit(): number`

現在の履歴曲線保持ポイント数制限を取得します。`webConfig.dashboard.historyLimit` を優先し、無効な場合はデフォルトの `20` を返します。

### `getChartThemeColors(): ThemeColors`

CSS 変数から現在のテーマ（ダーク/ライト）におけるグラフのテキスト、グリッド線、ボーダー色を読み取ります。

| テーマ | テキスト色 | グリッド色 | ボーダー色 |
|------|--------|--------|--------|
| ライト | `--carbon-900` | `--carbon-200` | `--carbon-300` |
| ダーク | `--carbon-200` | `--carbon-600` | `--carbon-500` |

---

## 指標切り替え器（モジュールレベルで自動実行）

```typescript
function initHistoryMetricSwitcher() { ... }
initHistoryMetricSwitcher(); // モジュールレベルで即時実行
```

`initHistoryMetricSwitcher()` はモジュールスコープ内で自動的に呼び出され、**`main.ts` から能動的に呼び出されることはありません**。以下の役割を担います：

1. `metricDots` ボタンのアクティブスタイルを同期
2. クリックイベントをバインドし、`currentHistoryMetric` 切り替え後に軸タイトルを更新して再描画

## データフロー

```mermaid
flowchart LR
    subgraph "dashboard_statuses.ts"
        LS[loadStatuses]
    end
    subgraph "dashboard_history.ts"
        AS[appendStatusSnapshotToHistory]
        NH[nodeHistories]
        EC[extractProgressData]
        UC[updateChartData]
        CH[Chart.js インスタンス]
    end
    LS -->|timestamp + statuses| AS
    AS --> NH
    NH --> EC
    EC -->|{x, y} 座標| UC
    UC --> CH
```

## 使用例

```typescript
// 手動で履歴データを構築してレンダリング
const mockHistory: Record<string, NodeHistory> = {
  "Processor": [
    { timestamp: 1000, tasks_processed: 10, tasks_succeeded: 9, tasks_failed: 1, tasks_duplicated: 0, tasks_pending: 90 },
    { timestamp: 1005, tasks_processed: 25, tasks_succeeded: 23, tasks_failed: 1, tasks_duplicated: 1, tasks_pending: 75 },
  ],
};

// nodeHistories = mockHistory;
// currentHistoryMetric = "tasks_succeeded";
// updateChartData();  // 折れ線グラフにレンダリング

// テーマ切り替え後にグラフ色を更新
// updateChartTheme();

// 手動で履歴データをトリミング
// webConfig.dashboard.historyLimit = 10;
// if (trimNodeHistories()) updateChartData();
```
