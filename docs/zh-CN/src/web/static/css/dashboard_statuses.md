# dashboard_statuses.css

> 📅 最后更新日期: 2026/06/22

负责仪表盘节点状态卡片的布局与样式定义，包括统计网格、四段式进度条以及基于节点状态的动态边框色。


## 布局结构

### 统计网格 (`.stat-grid`)
- 使用 `grid` 布局，固定为两列。
- 用于展示成功、等待、错误、重复等核心指标。

### 节点卡片 (`.node-card`)
- 采用圆角卡片设计（`border-radius: 1rem`）。
- **状态边框**: 左侧设有 3px 宽的状态条，颜色根据节点运行状态动态变化：
  - `.status-running`: 使用 `--cornflower-400` (蓝色)，表示正在运行。
  - `.status-stopped`: 使用 `--carbon-400` (灰色)，表示已停止。
  - 默认: 使用 `--carbon-300`，表示未启动。

## 进度条渲染 (`.progress-bar`)

进度条由四个分段（`.progress-segment`）组成，分别对应不同的任务状态颜色：

| 类名 | 对应指标 | 浅色模式颜色 | 深色模式颜色 |
|------|----------|--------------|--------------|
| `.seg-success` | 成功 | `--jade-400` | `--jade-700` |
| `.seg-error` | 错误 | `--crimson-400` | `--crimson-700` |
| `.seg-duplicate` | 重复 | `--marigold-400` | `--marigold-700` |
| `.seg-pending` | 等待 | `--carbon-300` | `--carbon-600` |

## 时间估算区域 (`.time-estimate`)

- 使用等宽字体（`monospace`）确保对齐。
- `.elapsed` 系列类名用于为已运行时间的各个位分段着色（成功、错误、重复）。

## 交互效果

- **点击反馈**:
  - `.error-clickable`: 错误数值项显示手型光标（`pointer`），暗示可点击跳转。

## 响应式设计

- 在宽度小于 `2048px` 时，`#dashboard-grid` 切换为单列布局。
- 自动处理长标题的换行逻辑。
