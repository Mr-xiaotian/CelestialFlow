# injection_layout.css

> 📅 最終更新日: 2026/06/22

タスク注入ページの検索フィルタ、2 カラムレイアウト、およびレスポンシブブレークポイントのスタイルを担当します。

## 2 カラムレイアウト (`.card-grid`)

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
