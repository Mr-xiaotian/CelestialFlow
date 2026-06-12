# injection_editor.css

> 📅 最終更新日: 2026/06/11

タスク注入ページ右側のエディターのスタイル定義を担当します。JSON 入力エリア、検証メッセージ、操作ボタングループを含みます。

> 🆕 **新規ドキュメント**: このファイルは元の統合 `injection.css` から分割され、エディターパネルのスタイルを専門に扱います。

## エディターコンテナ (`.injection-editor-card`)

- 縦方向 flex レイアウト、固定間隔 `gap: 1rem`。

## エディターヘッダー (`.editor-header`)

- **レイアウト**: `flex` 左右分布。左側は説明テキスト + 現在のノード情報、右側は操作ボタングループ。
- `.editor-node-meta`: 狭い幅での縮小を許可（`min-width: 0`）。
- `.editor-caption`: 「現在のノード」タイトル上部の小型説明テキスト。`0.75rem`、グレートーン（`--carbon-500`）。

## 現在のノード情報 (`.editor-node-row`)

- ノード名と右側の「編集済み」タグの行レイアウト。`flex-wrap: wrap` をサポート。
- `.current-node-name`: 現在選択中のノード名。`1rem`、`font-weight: 600`。

## ボタンスタイル (`.btn-small`, `.btn-select`, `.btn-clear`)

| セレクタ | 用途 | 背景色 | 文字色 |
|--------|------|--------|--------|
| `.btn-small` | 汎用小ボタン | — | — |
| `.btn-select` | 検証/フォーマットボタン | `--cornflower-50`（明）/ `--cornflower-700`（暗） | `--cornflower-700`（明）/ `--carbon-100`（暗） |
| `.btn-clear` | 下書きクリアボタン | `--carbon-100`（明）/ `--carbon-600`（暗） | `--carbon-700`（明）/ `--carbon-100`（暗） |

- **無効状態**: `opacity: 0.6`、`cursor: not-allowed`。

## JSON 入力エリア (`.json-input-section`)

- **JSON ヘッダー (`.json-header`)**: ラベルと「終端子テンプレートを挿入」ボタンの左右分布。
- **JSON ラベル (`.json-label`)**: `0.75rem`、`font-weight: 500`。
- **テンプレートボタン (`.example-btn`)**: 背景なしテキストボタン。`color: --cornflower-500`、ホバーで濃くなる。
- **JSON 編集ボックス (`.json-textarea`)**:
  - 等幅フォント（`Monaco, Menlo, monospace`）、`min-height: 20rem`、縦方向伸縮可能。
  - フォーカス時にボーダーが `--cornflower-400` に変わる。
  - 無効状態：`--carbon-50` 背景、`--carbon-400` 文字。

## 検証メッセージ (`.validation-message`)

| 状態 | CSS クラス | 色 |
|------|--------|------|
| 成功 | `.validation-success` | `--jade-600`（明）/ `--jade-400`（暗） |
| 失敗 | `.validation-error` | `--crimson-600`（明）/ `--crimson-400`（暗） |
| 中立 | `.validation-neutral` | `--carbon-500`（明）/ `--carbon-400`（暗） |

- `min-height: 1.25rem`、`font-size: 0.75rem`。JSON 編集ボックスの下に配置。

## エディター下部ボタングループ (`.editor-actions`)

- `flex` レイアウト、`gap: 0.75rem`、`flex-wrap: wrap`。

## 関連モジュール

- インタラクションロジックは `injection.ts` の `renderCurrentNodeEditor()`、`validateCurrentDraft()`、`formatCurrentDraft()` などの関数によって駆動されます。
- 「終端子テンプレートを挿入」ボタンは `fillTerminationDraft()` によって処理されます。
