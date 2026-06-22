# injection_nodes.css

> 📅 最終更新日: 2026/06/22

タスク注入ページ左側のノードブラウズリストのスタイル定義を担当します。ノード項目、選択状態、無効状態、「編集済み」タグを含みます。

## ノードリストコンテナ (`.node-list`)

- 縦方向 flex レイアウト、`gap: 0.5rem`。
- `max-height: 30rem`。超過時は縦スクロール（`overflow-y: auto`）。

## ノード項目 (`.node-item`)

- **レイアウト**: `flex` 左右分布（ノード情報 + 右側タグ）、`gap: 0.75rem`。
- **基本スタイル**: 角丸 `0.75rem`、ボーダー `1px solid --carbon-200`。
- **ホバー効果**: 背景が薄くなり（`--carbon-50`）、ボーダーが青く（`--cornflower-300`）なり、わずかに上移動 `-1px`。
- **ダークモード**: 背景 `--carbon-700`、ホバー時 `--carbon-600`。

| CSS クラス | 説明 |
|--------|------|
| `.node-item` | 基本ノード項目スタイル |
| `.node-item.active-node` | 現在選択中のノード：青ボーダー（`--cornflower-500`）+ 薄青背景（`--cornflower-50`） |
| `.disabled-node` | 注入不可ノード：`opacity: 0.55`、`cursor: not-allowed`、`pointer-events: none` |

## ノード情報エリア (`.node-info`)

- `min-width: 0`、`flex: 1`。テキストが狭い空間で縮小することを許可。

## ノード名 (`.node-name`)

- `font-weight: 600`、`word-break: break-all`。
- 明色モード `--carbon-800`、ダークモード `--carbon-100`。

## 「編集済み」タグ (`.node-side-tag`)

- `inline-flex`、`flex-shrink: 0`。
- カプセル形（`border-radius: 999px`）、小型内側パディング。
- 明色モード：青背景（`--cornflower-100`）+ 青文字（`--cornflower-700`）。
- ダークモード：濃青背景（`--cornflower-800`）+ 薄青文字（`--cornflower-100`）。

## 関連モジュール

- ノードリストは `injection.ts` の `renderNodeList()` によって動的レンダリングされます。
- 選択ロジックは `selectNode()` によって駆動され、`.active-node` クラスの切り替えでハイライトを実現します。
- 「注入可能ノードのみ表示」スイッチのフィルタロジックは `isInjectableNode()` を参照してください。
