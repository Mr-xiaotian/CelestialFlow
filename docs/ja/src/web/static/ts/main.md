# main.ts

> 📅 最終更新日: 2026/04/22

ページのメインエントリーポイントで、初期化、イベントバインディング、統一データリフレッシュスケジューリングを担当します。

## 責務

- DOMContentLoaded 後に設定を読み込み、ポーリングを開始
- リフレッシュ間隔選択、テーマ切り替え、タブ切り替えなどの UI イベントをバインド
- `refreshAll()` ですべてのデータを並列に取得し、必要に応じて各モジュールのレンダリングをトリガー

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `refreshRate` | `number` | 現在のリフレッシュ間隔（ミリ秒）、デフォルト 5000 |
| `refreshIntervalId` | `ReturnType<typeof setInterval> \| null` | タイマーハンドル |

## 初期化フロー

```
DOMContentLoaded
  └─ loadWebConfig()        /api/pull_config から設定を読み込み
  └─ applyConfig()          テーマ、リフレッシュ間隔、ダッシュボードレイアウトを適用
  └─ イベントバインディング
      ├─ refreshSelect      リフレッシュ間隔変更 → タイマーリセット + 設定保存
      ├─ themeToggleBtn     テーマ切り替え → 折れ線グラフ再構築 + 設定保存
      └─ tabButtons         タブ切り替え
  └─ initSortableDashboard()  ステージカードのドラッグ&ドロップ初期化
  └─ refreshAll()             即時リフレッシュを1回実行
  └─ initChart()              折れ線グラフインスタンスの初期化
  └─ setInterval(refreshAll)  定期ポーリングの開始
```

## コア関数

### `refreshAll()`

すべてのデータ更新と UI レンダリングを調整するメインリフレッシュ関数です。

**フロー:**

1. すべての `load*()` 関数を並列に呼び出して最新データを取得。各関数はデータが変更されたかどうかを示す `boolean` を返します
2. データドメインごとにグループ化し、データが変更された場合にのみ対応するレンダリング関数を呼び出します

**変更検出とレンダリングマッピング:**

| 変更条件 | トリガーされるレンダリング |
|----------|--------------------------|
| `statusesChanged \|\| structureChanged` | `renderMermaidStructure()` |
| `topologyChanged` | `renderTopologyInfo()` |
| `summaryChanged` | `renderSummary()` |
| `historiesChanged` | `updateChartData()` |
| `statusesChanged` | `renderDashboard()` / `populateNodeFilter()` / `renderNodeList()` |
| `errorsChanged` | `renderErrors()` |

## モジュール間依存関係

`main.ts` は他のモジュールが公開するグローバル関数と変数に依存します（`<script>` タグの読み込み順序で利用可能性を保証）:

- **web_config.ts** -- `loadWebConfig`, `saveWebConfig`, `applyConfig`, `webConfig`, `applyDashboardLayout`
- **task_history.ts** -- `loadHistories`, `nodeHistories`, `initChart`, `updateChartData`, `updateChartTheme`
- **task_statuses.ts** -- `loadStatuses`, `nodeStatuses`, `renderDashboard`, `initSortableDashboard`
- **task_structure.ts** -- `loadStructure`, `structureData`, `renderMermaidStructure`
- **task_errors.ts** -- `loadErrors`, `errors`, `renderErrors`, `populateNodeFilter`
- **task_topology.ts** -- `loadTopology`, `topologyData`, `renderTopologyInfo`
- **task_summary.ts** -- `loadSummary`, `summaryData`, `renderSummary`
- **task_injection.ts** -- `renderNodeList`
- **utils.ts** -- `toggleDarkTheme`, `switchToErrorsTab`
