# injection_preview.css

> 📅 最終更新日: 2026/06/11

タスク注入ページ下部の下書きプレビューエリア、送信ボタン、状態メッセージ、ローディングアニメーションのスタイル定義を担当します。

> 🆕 **新規ドキュメント**: このファイルは元の統合 `injection.css` から分割され、プレビューと送信のスタイルを専門に扱います。

## 下書きプレビューカード (`.draft-card`)

- 縦方向 flex レイアウト、`gap: 0.75rem`、`margin-bottom: 1rem`。
- 全編集済み下書きの集約表示エリアとして機能。

## 下書きプレビューエリア (`.draft-preview`)

- **読み取り専用スタイル**: `margin: 0`、`padding: 1rem`。入力状態なし。
- **等幅フォント**: `Monaco, Menlo, monospace`、`font-size: 0.75rem`。
- **背景**: 明色モード `--carbon-50`、ダークモード `--carbon-800`。
- **オーバーフロー**: `overflow: auto`。長い内容のスクロールに対応。
- **最小高さ**: `min-height: 12rem`。

## 空状態プレースホルダー (`.empty-placeholder`)

- 下書きがない場合に表示。等幅フォントスタイル。

## 送信ブロック (`.submit-section`)

- `flex` レイアウト、左右分布（状態ヒント + 送信ボタン）、`gap: 1rem`、`margin-top: auto`。

## 状態メッセージ (`.status-message`)

- `flex` レイアウト、`align-items: center`、`font-weight: 500`。

| CSS クラス | 説明 | 色 |
|--------|------|------|
| `.status-success` | 送信成功 | `--jade-600`（明）/ `--jade-400`（暗） |
| `.status-error` | 送信失敗 | `--crimson-600`（明）/ `--crimson-400`（暗） |

- **状態アイコン (`.status-icon`)**: `1.25rem`、右マージン `0.5rem`。SVG インラインアイコン用に予約。

## 送信ボタン (`.btn-submit`)

- **基本スタイル**: 青塗りつぶし（`--cornflower-500`）、白文字、角丸 `0.5rem`、影付き。
- **ホバー効果**: 背景が濃くなる（`--cornflower-600`）、わずかに上移動 `-1px`。
- **無効状態**: `--carbon-400` 背景、`cursor: not-allowed`、影なし・変位なし。
- **ダークモード**: 背景 `--cornflower-600`、無効状態 `--carbon-500`。

## ローディングインジケーター (`.spinner`)

```css
.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--frost-0);
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: injection-spin 1s linear infinite;
}
```

- 送信中に送信ボタン内部に動的挿入。白い円環 + 透明上部の回転効果。

## 回転アニメーション (`@keyframes injection-spin`)

```css
@keyframes injection-spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

## 関連モジュール

- 下書きプレビューは `injection.ts` の `renderDraftList()` によって動的レンダリングされます。
- 送信インタラクションは `handleSubmit()` によって駆動されます（ボタンのローディング状態切り替え、状態メッセージ表示）。
- 送信ボタンの有効性は `updateSubmitButtonAvailability()` によって制御されます。
