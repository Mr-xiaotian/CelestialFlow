# globals.d.ts

> 📅 最終更新日: 2026/04/22

TypeScript グローバル型宣言ファイル。CDN の `<script>` タグで読み込まれるサードパーティライブラリの型宣言を提供し、コンパイルエラーを防止します。

## 宣言内容

```ts
declare const Chart: any;    // Chart.js — 折れ線グラフ
declare const Sortable: any; // SortableJS — ドラッグ＆ドロップソート

interface Window {
  mermaid: any; // Mermaid — フローチャートレンダリング
}
```

## 説明

これらの 3 つのライブラリはすべて `index.html` の CDN `<script>` タグでグローバルにマウントされます：

- `Chart.js` → `window.Chart`、`task_history.ts` の折れ線グラフに使用
- `SortableJS` → `window.Sortable`、`task_statuses.ts` のノードカードのドラッグ＆ドロップソートに使用
- `mermaid` → `window.mermaid`、`task_structure.ts` のタスクグラフ可視化に使用、ESM 動的インポートで読み込み

このファイルにはランタイムコードは含まれず、TypeScript コンパイル段階でのみ作用します。
