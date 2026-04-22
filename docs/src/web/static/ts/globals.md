# globals.d.ts

TypeScript 全局类型声明文件，为通过 CDN `<script>` 标签引入的第三方库提供类型声明，避免编译报错。

## 声明内容

```ts
declare const Chart: any;    // Chart.js — 折线图
declare const Sortable: any; // SortableJS — 拖拽排序

interface Window {
  mermaid: any; // Mermaid — 流程图渲染
}
```

## 说明

这三个库均通过 `index.html` 中的 CDN `<script>` 标签挂载到全局：

- `Chart.js` → `window.Chart`，用于 `task_history.ts` 中的折线图
- `SortableJS` → `window.Sortable`，用于 `task_statuses.ts` 中节点卡片拖拽排序
- `mermaid` → `window.mermaid`，用于 `task_structure.ts` 中的任务图可视化，通过 ESM 动态导入

此文件不包含运行时代码，仅作用于 TypeScript 编译阶段。
