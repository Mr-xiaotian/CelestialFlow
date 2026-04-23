# index.html

> 📅 最終更新日: 2026/04/22

Web UI の Jinja2 テンプレートファイルで、監視システムの完全なページ構造を定義します。

## 全体レイアウト

ページは3つの主要エリアに分かれています:

```
<header>  — 上部コントロールバー（リフレッシュ間隔、テーマ切り替え）
<main>
  ├─ .tabs          — タブナビゲーション
  ├─ #dashboard     — ダッシュボード（3カラムレイアウト）
  ├─ #errors        — エラーログ
  └─ #task-injection — タスクインジェクション
```

## タブ

| Tab ID | ボタン `data-tab` | 説明 |
|--------|-------------------|------|
| `#dashboard` | `dashboard` | リアルタイムタスクグラフ監視パネル |
| `#errors` | `errors` | エラーログリスト |
| `#task-injection` | `task-injection` | タスクインジェクション |

## ダッシュボード3カラム構造

### 左カラム `.left-panel`

| カード | ID / Class | デフォルト表示 | 説明 |
|--------|-----------|---------------|------|
| タスク構造図 | `.mermaid-card` | レイアウト設定による | Mermaid フローチャートコンテナ `#mermaid-container` |
| グラフトポロジ情報 | `.topology-card` / `#topology-card` | レイアウト設定による | DAG 状態、スケジューリングモード、レイヤー数を表示 |

### 中央カラム `.middle-panel`

| カード | Class | 説明 |
|--------|-------|------|
| ステージ実行状態 | `.status-card` | 動的に生成されるステージ状態カードグリッド `#dashboard-grid` |

### 右カラム `.right-panel`

| カード | Class | 説明 |
|--------|-------|------|
| ステージ完了推移 | `.progress-card` | Chart.js 折れ線グラフ `<canvas id="node-progress-chart">` |
| 全体ステータスサマリー | `.summary-card` | 6セル統計: 成功/待機中/エラー/重複/アクティブノード/残り時間 |

> カードの実際のカラム配置と表示/非表示は `web_config.ts` の `applyDashboardLayout()` により動的に制御されます。初期 HTML ではすべてのカードが `display: none` に設定されています。

## エラーログパネル

- キーワード検索ボックス `#error-search`
- ステージフィルタードロップダウン `#node-filter`
- エラーテーブル `#errors-table`（列: エラーID / エラーメッセージ / ステージ / タスク / 時刻）
- ページネーションコントロールコンテナ `#pagination-container`

## タスクインジェクションパネル

- ステージ検索 `#search-input` + ステージリスト `#node-list`
- 全選択/クリアボタン
- 選択済みステージエリア `#selected-section` / `#selected-list`
- 入力方法切り替え: JSON テキスト（`#json-textarea`）/ ファイルアップロード（`#file-input`）
- 終了信号挿入ショートカットボタン `fillTermination()`
- 送信ボタン `#submit-btn` + ステータスメッセージ `#status-message`

## 外部依存（CDN）

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| Chart.js | latest | 折れ線グラフ |
| SortableJS | latest | ステージカードのドラッグ&ドロップソート |
| Mermaid | `^10` (ESM) | タスクグラフの可視化 |

Mermaid は `<script type="module">` で ESM モジュールとして読み込まれ、`window.mermaid` にマウントされ、`task_structure.ts` で使用されます。

## JS スクリプト読み込み順序

スクリプトは以下の順序で読み込まれます（依存関係順）:

```html
utils.js          ← ユーティリティ関数（依存なし）
task_statuses.js  ← utils に依存
task_structure.js ← utils, task_statuses に依存（nodeStatuses を参照）
task_errors.js    ← utils, task_statuses に依存（nodeStatuses を参照）
task_topology.js  ← utils に依存
task_summary.js   ← utils に依存
task_history.js   ← utils に依存（extractProgressData, getColor）
task_injection.js ← task_statuses（nodeStatuses を参照）, utils に依存
main.js           ← 上記すべてのモジュールに依存
```

## CSS スタイル参照

```html
css/base.css       ← グローバルスタイル、テーマ変数
css/dashboard.css  ← ダッシュボード、カード、プログレスバーのスタイル
css/errors.css     ← エラーテーブル、ページネーションのスタイル
css/inject.css     ← タスクインジェクションページのスタイル
```
