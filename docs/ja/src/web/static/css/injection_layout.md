# injection_layout.css

> 📅 最終更新日: 2026/06/11

タスク注入ページの上部ヒントエリア、検索フィルタ、2カラムレイアウト、レスポンシブブレークポイントのスタイルを担当します。

> 🆕 **新規ドキュメント**: このファイルは元の統合 `injection.css` から分割され、レイアウトとフィルタのスタイルを専門に扱います。

## ヒントエリア (`.tip-section`)

- ページ上部に位置。薄青色背景（`--cornflower-50`）+ 濃青色左ボーダー（`4px solid --cornflower-500`）。
- ダークモード：背景が `--cornflower-900` に切り替わる。
- `.tip-content`: flex レイアウトでアイコンとテキストを配置。
- `.tip-icon`: SVG アイコン。`1.25rem`、色 `--cornflower-500`。
- `.tip-text`: ヒント本文。`0.75rem`。

## 2カラムレイアウト (`.card-grid`)

```css
.card-grid {
  display: grid;
  grid-template-columns: minmax(18rem, 22rem) minmax(0, 1fr);
  gap: 1.5rem;
}
```

- 左側ノードリストは 18–22rem に固定、右側エディターは残りの幅に自動調整。

## 検索フィルタ

- **検索コンテナ (`.search-container`)**: 相対配置。検索アイコンを配置するために使用。
- **検索入力ボックス (`.search-input`)**:
  - 左内側パディング `2.5rem` で検索アイコンのスペースを確保。
  - フォーカス時にボーダー色が `--cornflower-400` に切り替わる。
  - ダークモード：`--carbon-700` 背景。
- **検索アイコン (`.search-icon`)**: 入力ボックス左側に絶対配置。`1rem`、`color: --carbon-400`。

## 注入可能ノードスイッチ (`.injectable-toggle`)

- `flex` レイアウト、`gap: 0.5rem`、`font-size: 0.75rem`。
- 検索ボックスの下、ノードリストの上に配置。

## レスポンシブ (`@media (max-width: 2048px)`)

狭い画面（≤2048px）では：
- `.card-grid` が単一カラムに切り替わる（`grid-template-columns: 1fr`）。
- `.node-list` の `max-height` 制限が解除される。
- `.editor-header` と `.submit-section` が縦方向スタックに切り替わる。
- `.editor-actions` が縦方向配置に切り替わる。

## 関連モジュール

- レイアウト構造は `injection.ts` の `renderInjectionPage()` によって動的に埋め込まれます。
- 検索とフィルタイベントは `setupEventListeners()` によってバインドされます。
