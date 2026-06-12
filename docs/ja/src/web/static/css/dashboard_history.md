# dashboard_history.css

> 📅 最終更新日: 2026/06/11

ノード指標履歴グラフ（Chart.js）の上部にあるコントロールエリアのスタイルを担当し、指標切り替えボタングループを含みます。

> ⚠️ **変更済み**: 旧版ドキュメントで言及されていた `.history-metric-switcher` および `.history-metric-btn` クラス名は `.metric-indicators` および `.metric-dot` に変更されました。

## レイアウト設計 (`.progress-card-header`)

- **構造**: `flex` レイアウトを使用し、左側にカードタイトル、右側に指標切り替え器を表示します。
- **適応型**: `flex-wrap: wrap` を有効にし、狭い画面で自動的に折り返します。

## 指標切り替え器 (`.metric-indicators`)

- **コンテナ**: `flex` レイアウト、`flex-wrap: wrap`、中央揃え、`gap: 1rem`。
- **切り替えボタン (`.metric-dot`)**:
  - 各ボタンはカラードット（`.dot`）とテキストラベル（`.label`）を含みます。
  - **デフォルト状態**: `opacity: 0.55`、未選択の指標を弱めます。
  - **ホバー状態**: `opacity: 0.8`。
  - **アクティブ状態 (`.active`)**: `opacity: 1`、薄い灰色背景（`--carbon-100`）、ダークモードでは `--carbon-700`。
  - **トレンド指標 (`.dot.delta`)**: 中空円（`background: transparent`、ボーダーのみ着色）、増分系指標と累積系指標を区別します。
- **区切り線 (`.metric-sep`)**: `1px` 幅の縦線、累積指標とトレンド指標グループを区切ります。

## 関連モジュール

- 実際の折れ線グラフは `dashboard_history.ts` が Chart.js と連携して canvas 内にレンダリングし、その内部色（テキスト、軸線）は TS コード内で CSS 変数を読み取り Chart.js インスタンスに設定します。
- 指標切り替えは `initHistoryMetricSwitcher()` によって自動的にバインドされます（モジュールレベルで実行）。
