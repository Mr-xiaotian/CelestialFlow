# dashboard_history.css

> 📅 最后更新日期: 2026/06/22

负责节点指标历史图（Chart.js）上方的控制区域样式，包括指标切换按钮组。


## 布局设计 (`.progress-card-header`)

- **结构**: 采用 `flex` 布局，左侧显示卡片标题，右侧显示指标切换器。
- **自适应**: 开启 `flex-wrap: wrap`，在窄屏下自动换行。

## 指标切换器 (`.metric-indicators`)

- **容器**: `flex` 布局，`flex-wrap: wrap`，居中排列，`gap: 1rem`。
- **切换按钮 (`.metric-dot`)**:
  - 每个按钮包含一个颜色圆点（`.dot`）和一个文字标签（`.label`）。
  - **默认态**: `opacity: 0.55`，弱化未选中的指标。
  - **悬停态**: `opacity: 0.8`。
  - **激活态 (`.active`)**: `opacity: 1`，浅灰背景（`--carbon-100`），深色模式下为 `--carbon-700`。
  - **趋势指标 (`.dot.delta`)**: 空心圆（`background: transparent`，仅边框着色），用于区分增量类指标与累计类指标。
- **分隔线 (`.metric-sep`)**: `1px` 宽的竖线，用于分隔累计指标与趋势指标组。

## 关联模块

- 实际的折线图由 `dashboard_history.ts` 配合 Chart.js 渲染在 canvas 中，其内部颜色（文字、轴线）是在 TS 代码中通过 CSS 变量读取并设置给 Chart.js 实例的。
- 指标切换由 `initHistoryMetricSwitcher()` 自动绑定（模块级执行）。
