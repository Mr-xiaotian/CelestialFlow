# globals.d.ts

> 📅 最終更新日: 2026/04/22

TypeScript のグローバル型宣言ファイルです。CDN `<script>` タグで読み込まれるサードパーティライブラリの型宣言を提供し、コンパイルエラーを防止します。

## 宣言内容

```ts
declare const Chart: any;    // Chart.js — 折れ線グラフ
declare const Sortable: any; // SortableJS — ドラッグ&ドロップソート

interface Window {
  mermaid: any; // Mermaid — フローチャートレンダリング
}
```

## 説明

3つのライブラリはすべて `index.html` の CDN `<script>` タグを通じてグローバルスコープにマウントされます:

- `Chart.js` → `window.Chart`、`task_history.ts` の折れ線グラフに使用
- `SortableJS` → `window.Sortable`、`task_statuses.ts` のステージカードのドラッグ&ドロップソートに使用
- `mermaid` → `window.mermaid`、`task_structure.ts` のタスクグラフ可視化に使用、ESM 動的インポート経由

このファイルにはランタイムコードは含まれず、TypeScript コンパイル段階でのみ作用します。
