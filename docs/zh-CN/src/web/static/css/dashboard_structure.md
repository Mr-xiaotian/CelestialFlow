# dashboard_structure.css

> 📅 最后更新日期: 2026/05/23

负责任务结构图（Mermaid.js 渲染内容）的容器布局及主题适配。

## 容器布局 (`#mermaid-container`)

- **对齐方式**: 使用 `flex` 布局实现内容水平和垂直居中。
- **滚动支持**: 开启 `overflow-x: auto`，确保在大规模复杂图结构下，用户可以横向滚动查看完整拓扑。

## Mermaid 主题适配

由于 Mermaid 渲染出的 SVG 内部样式较难通过常规 CSS 覆盖，本文件主要针对暗黑模式（`.dark-theme`）进行了关键样式的强制覆盖：

- **箭头颜色 (`.arrowMarkerPath`)**: 在暗黑模式下将箭头填充色设为 `--carbon-200`，增强连线可见度。
- **节点文字 (`span`)**: 强制修改节点内部文本颜色为 `--carbon-300`，确保在深色背景节点下的可读性。

## 关联模块

- 具体的节点背景色、边框色和连线样式（`classDef`）是在 `dashboard_structure.ts` 中根据当前主题动态生成的 Mermaid 代码中定义的，不在此 CSS 文件中。
