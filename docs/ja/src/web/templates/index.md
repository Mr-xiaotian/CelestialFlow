# index.html

> 📅 最終更新日: 2026/05/15

Web UI の Jinja2 テンプレートファイルで、監視システムの完全なページ構造を定義します。

## 全体レイアウト

ページは3つの主要エリアに分かれています：

```
<header>  — 上部コントロールバー（設定パネル、テーマ切り替え）
<main>
  ├─ .tabs          — タブナビゲーション
  ├─ #dashboard     — ダッシュボード（3カラムレイアウト）
  ├─ #errors        — エラーログ
  └─ #task-injection — タスクインジェクション
```

## Header コントロールバー

| 要素 | ID / Class | 説明 |
|------|-----------|------|
| 設定ボタン | `#settings-btn` / `.btn-settings` | 歯車 SVG アイコン、クリックで設定パネルを開く |
| 設定パネル | `#settings-panel` / `.settings-panel` | リフレッシュ間隔と履歴長の2つの設定を含むフローティングパネル |
| 閉じるボタン | `#settings-close` / `.settings-close` | 設定パネル内の閉じるボタン |
| リフレッシュ間隔 | `#refresh-interval` | ドロップダウン、選択肢: 1s/2s/5s/10s/30s |
| 履歴長 | `#history-limit` | ドロップダウン、選択肢: 10/20/50/100 |
| テーマ切り替え | `#theme-toggle` | ライト/ダークモード切り替えボタン |

設定パネルはデフォルトで非表示（`hidden` クラス）。歯車ボタンのクリックで表示を切り替え、パネル外またはバツボタンのクリックで非表示にします。

## タブ

| Tab ID | ボタン `data-tab` | 説明 |
|--------|-------------------|------|
| `#dashboard` | `dashboard` | リアルタイムタスクグラフ監視パネル |
| `#errors` | `errors` | エラーログリスト |
| `#task-injection` | `task-injection` | タスクインジェクション |

## ダッシュボード3カラム構造

### 左カラム `.left-panel`

| カード | Class | 説明 |
|--------|-------|------|
| タスク構造図 | `.mermaid-card` | Mermaid フローチャートコンテナ `#mermaid-container` |
| グラフ分析情報 | `.analysis-card` | DAG 状態、スケジューリングモード、レイヤー数を表示 |

### 中央カラム `.middle-panel`

| カード | Class | 説明 |
|--------|-------|------|
| ノード実行状態 | `.status-card` | 動的に生成されるノードステータスカードグリッド `#dashboard-grid` |

### 右カラム `.right-panel`

| カード | Class | 説明 |
|--------|-------|------|
| ノード完了推移 | `.progress-card` | Chart.js 折れ線グラフ `<canvas id="node-progress-chart">` |
| 全体ステータスサマリー | `.summary-card` | 6セル統計：成功/待機中/エラー/重複/アクティブノード/残り時間 |

> カードの実際のカラム配置と表示/非表示は `web_config.ts` の `applyDashboardLayout()` により動的に制御されます。初期 HTML ではすべてのカードが `display: none` に設定されています。

## エラーログパネル

- キーワード検索ボックス `#error-search`
- ノードフィルタドロップダウン `#node-filter`
- エラーテーブル `#errors-table`（列：番号 / エラー ID / エラーメッセージ / ノード / タスク / 時間）
- ページネーションコントロールコンテナ `#pager-container`

## タスクインジェクションパネル

- ノード検索 `#search-input` + ノードリスト `#node-list`
- 全選択/クリアボタン
- 選択済みノードエリア `#selected-section` / `#selected-list`
- 入力方法切り替え：JSON テキスト（`#json-textarea`）/ ファイルアップロード（`#file-input`）
- 終了信号挿入ショートカットボタン `fillTermination()`
- 送信ボタン `#submit-btn` + ステータスメッセージ `#status-message`

## 外部依存（CDN）

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| Chart.js | latest | 折れ線グラフ |
| SortableJS | latest | ノードカードのドラッグ＆ドロップソート |
| Mermaid | `^10` (ESM) | タスクグラフの可視化 |

Mermaid は `<script type="module">` で ESM モジュールとして読み込まれ、`window.mermaid` にマウントされ、`task_structure.ts` で使用されます。

## JS スクリプト読み込み順序

スクリプトは以下の順序で読み込まれます（依存関係順）：

```html
utils.js          ← ユーティリティ関数（依存なし）
web_config.js     ← utils に依存（refreshSelect 等の DOM 要素を参照）
task_statuses.js  ← utils に依存
task_structure.js ← utils, task_statuses に依存（nodeStatuses を参照）
task_errors.js    ← utils, task_statuses に依存（nodeStatuses を参照）
task_analysis.js  ← utils に依存
task_summary.js   ← utils に依存
task_history.js   ← utils に依存（extractProgressData, getColor）
task_injection.js ← task_statuses（nodeStatuses を参照）, utils に依存
main.js           ← 上記すべてのモジュールに依存
```

## CSS スタイル参照

```html
css/_colors.css    ← カラー変数定義
css/base.css       ← グローバルスタイル、テーマ変数、設定パネルスタイル
css/dashboard.css  ← ダッシュボード、カード、プログレスバーのスタイル
css/errors.css     ← エラーテーブル、ページネーションのスタイル
css/inject.css     ← タスクインジェクションページのスタイル
```
