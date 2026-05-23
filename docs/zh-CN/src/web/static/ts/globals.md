# globals.d.ts

> 📅 最后更新日期: 2026/05/23

TypeScript 全局类型声明文件，为通过 CDN `<script>` 标签引入的第三方库及一些全局函数提供基础声明。

## 声明内容

```ts
declare const Chart: any;    // Chart.js — 历史指标走向图
declare const Sortable: any; // SortableJS — 节点卡片拖拽排序

interface Window {
  mermaid: any; // Mermaid — 任务结构图渲染
}
```

## 说明

- `Chart.js` → 用于 `dashboard_history.ts` 中的多指标折线图。
- `SortableJS` → 用于 `dashboard_statuses.ts` 中节点卡片的自由拖拽排序。
- `mermaid` → 用于 `dashboard_structure.ts` 中的有向图可视化，通过 ESM 模块动态加载后挂载。

此文件确保 TypeScript 编译器能够识别非模块化加载的外部依赖。
