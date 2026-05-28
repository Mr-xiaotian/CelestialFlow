# index.html

> 📅 最終更新日: 2026/05/28

Web UI の Jinja2 テンプレートファイルで、監視システムの完全なページ構造を定義します。

## 全体レイアウト

ページは3つの主要エリアに分かれています：

```
<header>  — 上部コントロールバー（設定パネル、テーマ切替）
<main>
  ├─ .tabs           — タブナビゲーション（ダッシュボード / エラーログ / タスク注入）
  ├─ #dashboard      — ダッシュボード（3カラムレイアウト）
  ├─ #errors         — エラーログ
  └─ #task-injection  — タスク注入
```

## Header コントロールバー

| 要素 | ID / Class | 説明 |
|------|-----------|------|
| 設定ボタン | `#settings-btn` | クリックで設定パネルを開く。a11y 属性付き |
| 設定パネル | `#settings-panel` | リフレッシュ、履歴、言語、ページサイズ、デルタトグルなどの設定を含む |
| UI 言語 | `#language-select` | 中国語、英語、日本語の切替をサポート |
| 構造図デルタ | `#structure-edge-delta` | Mermaid グラフエッジに成功数デルタを表示するかを制御するトグル |
| テーマ切替 | `#theme-toggle` | 角丸カプセルボタン。ライト/ダークモードを切り替え |

## ダッシュボード3カラム構造

### 左カラム `.left-panel`

| カード | Class | 説明 |
|--------|-------|------|
| タスク構造図 | `.mermaid-card` | Mermaid フローチャート。ノード着色とエッジデルタをサポート |
| グラフ分析情報 | `.analysis-card` | トポロジ構造の洞察情報 |

### 中央カラム `.middle-panel`

| カード | Class | 説明 |
|--------|-------|------|
| ノード実行状態 | `.status-card` | プログレスバーとリアルタイムデルタ統計付きの動的ノードカード |

### 右カラム `.right-panel`

| カード | Class | 説明 |
|--------|-------|------|
| ノード指標推移 | `.progress-card` | 指標切替（処理済/成功/失敗/重複/保留中）対応の履歴折れ線グラフ |
| 全体状態サマリー | `.summary-card` | グローバル6セル統計ダッシュボード |

## 外部依存（CDN）

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| Chart.js | latest | 折れ線グラフ描画 |
| SortableJS | latest | ノードカードのドラッグ＆ドロップソート |
| Mermaid | `^10` (ESM) | タスクグラフの可視化レンダリング |

## JS スクリプト読み込み順序

スクリプトは依存関係順に読み込まれます：

```html
i18n.js               ← 国際化サポート
utils.js              ← 共通ユーティリティ関数
web_config.js         ← 設定管理ロジック
dashboard_statuses.js ← ノード状態管理
dashboard_structure.js← 構造図レンダリング
errors.js             ← エラーログページネーション
dashboard_analysis.js ← トポロジ分析表示
dashboard_summary.js  ← サマリー統計
dashboard_history.js  ← 履歴グラフ
injection.js          ← タスク注入ロジック
layout_editor.js      ← カードレイアウトエディター（web_config の CARD_TEMPLATES、PANEL_SELECTOR_MAP、applyDashboardLayout に依存）
main.js               ← グローバルエントリポイントとポーリング調整
```

## CSS スタイル参照

```html
css/_colors.css             ← カラー変数定義
css/base.css                ← グローバル基本スタイルと設定パネル
css/dashboard.css           ← ダッシュボードレイアウトとタブコンテナ
css/dashboard_structure.css  ← 構造図専用スタイル
css/dashboard_analysis.css   ← 分析カード専用スタイル
css/dashboard_statuses.css   ← ノードカード専用スタイル
css/dashboard_summary.css    ← サマリーパネル専用スタイル
css/dashboard_history.css    ← 履歴グラフ専用スタイル
css/errors.css              ← エラーログページスタイル
css/injection.css           ← タスク注入ページスタイル
```

## カードレイアウトエディターモーダル (`#layout-editor-overlay`)

3カラムダッシュボードカードのドラッグ＆ドロップ並べ替えをサポートするフローティングモーダルウィンドウ（デフォルトでは `.overlay.hidden` で非表示）。

- **オーバーレイ**: `#layout-editor-overlay` / `.overlay` — 全画面半透明黒背景、`z-index: 200`
- **エディター本体**: `#layout-editor` / `.layout-editor` — 角丸カードコンテナ、`max-width: 700px`
- **3カラムドロップゾーン**: 左中右ドロップゾーン（`#layout-dropzone-left`、`#layout-dropzone-middle`、`#layout-dropzone-right`）、SortableJS ベースのドラッグ＆ドロップ
- **未使用プール**: `#layout-dropzone-unused` — 3カラムから外されたカードを収容する水平ドロップゾーン
- **フッターボタン**: 保存（`#layout-save-btn`）とデフォルトにリセット（`#layout-reset-btn`）
- 設定パネルの `.btn-layout-editor` ボタンで開く。`#layout-editor-close` クリックまたはオーバーレイ外クリックで閉じる
- 保存時に `applyDashboardLayout()` を呼び出して即時反映し、その後 `saveWebConfig()` でバックエンドに永続化

## 使用例

### ブラウザからのアクセス

Web サーバー起動後、ブラウザのアドレスバーでアクセス：

```
http://127.0.0.1:5000
```

起動コマンド：

```bash
# コマンドライン起動（デフォルト 0.0.0.0:5000）
celestialflow-web

# または Python で起動
python -c "from celestialflow import TaskWebServer; TaskWebServer(host='127.0.0.1', port=5000).start_server()"
```

ブラウザで開くと3つのタブが表示されます：
- **ダッシュボード (Dashboard)**: タスクグラフの構造図、ノード実行状態、指標推移、全体サマリーをリアルタイム表示
- **エラーログ (Errors)**: エラーレコードのページネーション表示と検索
- **タスク注入 (Task Injection)**: 指定ノードへの新規タスク注入

### テンプレートの変更

`index.html` は Jinja2 テンプレートエンジンを使用しています。カスタムテンプレート変数を使用するか、HTML を直接変更することでインターフェースをカスタマイズできます。

#### ページタイトルの変更

`index.html` を編集し `<title>` タグを見つけます：

```html
<!-- 元の内容 -->
<title>タスクグラフ監視システム</title>

<!-- カスタムタイトルに変更 -->
<title>マイタスクモニター</title>
```

#### ダッシュボードレイアウトの調整

テンプレートには3カラム構造（left-panel / middle-panel / right-panel）がハードコードされています。対応するカードコンテナの順序を変更することで位置を入れ替えられます：

```html
<!-- 構造図と分析情報を入れ替え -->
<div class="left-panel">
  <div class="analysis-card"><!-- 分析パネル --></div>
  <div class="mermaid-card"><!-- 構造図 --></div>
</div>
```

#### 設定による動的制御

実行時のカードレイアウトは実際には `WebConfig.dashboard` によって制御されます。`web_config.ts` でデフォルトを変更するか、バックエンドの `config.json` で調整します：

```json
{
    "dashboard": {
        "left": ["status"],
        "middle": ["mermaid"],
        "right": ["summary", "progress"]
    }
}
```

#### カスタム CSS の追加

カスタムスタイルファイルを `web/static/css/` ディレクトリに配置し、`index.html` で参照します：

```html
<link rel="stylesheet" href="static/css/custom.css">
```
