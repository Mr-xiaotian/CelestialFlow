# main.ts

> 📅 最終更新日: 2026/05/15

ページのメインエントリポイント。初期化、イベントバインディング、統一データリフレッシュスケジューリングを担当します。

## 責務

- DOMContentLoaded 後に設定を読み込み、ポーリングを開始
- 設定パネル、リフレッシュ間隔、履歴長、テーマ切り替え、タブ切り替えなどの UI イベントをバインド
- `refreshAll()` を通じてすべてのデータを並列取得し、必要に応じて各モジュールのレンダリングをトリガー

## グローバル変数

| 変数 | 型 | 説明 |
|------|------|------|
| `refreshRate` | `number` | 現在のリフレッシュ間隔（ミリ秒）、デフォルト 5000 |
| `refreshIntervalId` | `ReturnType<typeof setInterval> \| null` | タイマーハンドル |

## DOM 要素参照

| 変数 | セレクタ | 説明 |
|------|----------|------|
| `refreshSelect` | `#refresh-interval` | リフレッシュ間隔ドロップダウン |
| `historyLimitSelect` | `#history-limit` | 履歴長ドロップダウン |
| `settingsBtn` | `#settings-btn` | 設定ギアボタン |
| `settingsPanel` | `#settings-panel` | 設定フローティングパネル |
| `settingsClose` | `#settings-close` | 設定パネル閉じるボタン |
| `themeToggleBtn` | `#theme-toggle` | テーマ切り替えボタン |
| `tabButtons` | `.tab-btn` | タブボタンリスト |
| `tabContents` | `.tab-content` | タブコンテンツリスト |

## 初期化フロー

```
DOMContentLoaded
  └─ loadWebConfig()        /api/pull_config から設定を読み込み
  └─ applyConfig()          テーマ、リフレッシュ間隔、履歴長、ダッシュボードレイアウトを適用
  └─ イベントバインディング
      ├─ settingsBtn        ギアボタンクリック：設定パネルの表示/非表示を切り替え
      ├─ settingsClose      閉じるボタンクリック：設定パネルを非表示
      ├─ document click     ページ空白部分クリック：設定パネルを自動的に閉じる
      ├─ refreshSelect      リフレッシュ間隔変更 → タイマーリセット + 設定保存
      ├─ historyLimitSelect 履歴長変更 → 設定保存（バックエンドの次回スナップショット時に反映）
      ├─ themeToggleBtn     テーマ切り替え → チャート再レンダリング + 設定保存
      └─ tabButtons         タブ切り替え
  └─ initSortableDashboard()  ノードカードのドラッグ＆ドロップを初期化
  └─ refreshAll()             即座に1回リフレッシュを実行
  └─ initChart()              折れ線グラフインスタンスを初期化
  └─ setInterval(refreshAll)  定期ポーリングを開始
```

## コア関数

### `refreshAll()`

すべてのデータ更新と UI レンダリングを調整するメインリフレッシュ関数。

**フロー：**

1. すべての `load*()` 関数を並列で呼び出して最新データを取得。各関数はデータが変化したかを示す `boolean` を返す
2. データドメインごとにグループ化し、データが変化した場合のみ対応するレンダリング関数を呼び出す

**変化検出とレンダリングマッピング：**

| 変化条件 | トリガーされるレンダリング |
|----------|--------------------------|
| `statusesChanged \|\| structureChanged` | `renderMermaidStructure()` |
| `analysisChanged` | `renderAnalysisInfo()` |
| `summaryChanged` | `renderSummary()` |
| `historiesChanged` | `updateChartData()` |
| `statusesChanged` | `renderDashboard()` / `populateNodeFilter()` / `renderNodeList()` |
| `errorsChanged` | `renderErrors()` |

## クロスモジュール依存関係

`main.ts` は他のモジュールが公開するグローバル関数と変数に依存しています（`<script>` タグの読み込み順序で利用可能性を保証）：

- **web_config.ts** — `loadWebConfig`, `saveWebConfig`, `applyConfig`, `webConfig`, `applyDashboardLayout`
- **task_history.ts** — `loadHistories`, `nodeHistories`, `initChart`, `updateChartData`, `updateChartTheme`
- **task_statuses.ts** — `loadStatuses`, `nodeStatuses`, `renderDashboard`, `initSortableDashboard`
- **task_structure.ts** — `loadStructure`, `structureData`, `renderMermaidStructure`
- **task_errors.ts** — `loadErrors`, `errors`, `renderErrors`, `populateNodeFilter`
- **task_analysis.ts** — `loadAnalysis`, `analysisData`, `renderAnalysisInfo`
- **task_summary.ts** — `loadSummary`, `summaryData`, `renderSummary`
- **task_injection.ts** — `renderNodeList`
- **utils.ts** — `toggleDarkTheme`, `switchToErrorsTab`
