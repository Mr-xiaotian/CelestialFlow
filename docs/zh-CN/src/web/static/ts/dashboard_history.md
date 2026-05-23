# dashboard_history.ts

> 📅 最后更新日期: 2026/05/24

管理节点多指标历史数据的维护与折线图的初始化、重绘。历史数据完全在前端通过状态快照累积。

## 类型定义

```ts
/** 历史图支持切换展示的指标字段键 */
type HistoryMetricKey =
  | "tasks_processed"
  | "tasks_succeeded"
  | "tasks_failed"
  | "tasks_duplicated"
  | "tasks_pending";

/** 单个节点在某一时刻的历史采样点 */
type NodeHistoryPoint = {
  timestamp: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  tasks_duplicated: number;
  tasks_pending: number;
};

type NodeHistory = NodeHistoryPoint[];
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | 各节点本地维护的历史数据序列 |
| `progressChart` | `any` | Chart.js 实例 |
| `hiddenNodes` | `Set<string>` | 折线图中已隐藏的节点集合，持久化至 localStorage |
| `currentHistoryMetric` | `HistoryMetricKey` | 当前图表展示的指标，默认为 `tasks_processed` |
| `historyMetricButtons` | `NodeListOf<HTMLButtonElement>` | 所有 `.history-metric-btn` 按钮 |

## 辅助函数

### `getColor(index)`

根据索引返回预定义的主题色（从 CSS 变量中读取），用于区分不同节点的折线。

| Index | CSS 变量 | 说明 |
|-------|---------|------|
| 0 | `--cornflower-500` | 矢车菊蓝 |
| 1 | `--jade-500` | 翡翠绿 |
| 2 | `--marigold-500` | 万寿菊黄 |
| 3 | `--crimson-500` | 深红 |
| 4 | `--violet-500` | 紫罗兰 |
| 5+ | 循环取模，共 9 色池 | — |

### `getHistoryMetricLabelKey(metric)`

将 `HistoryMetricKey` 映射为国际化翻译 key。

| 输入 | 输出 |
|------|------|
| `tasks_processed` | `chart.metric.processed` |
| `tasks_succeeded` | `chart.metric.succeeded` |
| `tasks_failed` | `chart.metric.failed` |
| `tasks_duplicated` | `chart.metric.duplicated` |
| `tasks_pending` | `chart.metric.pending` |

### `updateHistoryMetricButtons()`

遍历 `historyMetricButtons`，根据 `currentHistoryMetric` 为匹配的按钮添加 `.active` 类，其余移除。

### `updateChartAxisLabels()`

更新折线图 X/Y 轴标题文本，分别映射为当前语言的"时间"和对应指标名。

---

## 核心逻辑函数

### `initChart()`

初始化（或重建）Chart.js 折线图实例。

- 若已有实例，先调用 `destroy()` 销毁
- 调用 `getChartThemeColors()` 读取当前主题的文字色、网格色和轴线色
- 配置图例点击事件：切换节点显示/隐藏并同步到 localStorage
- **不使用 `animation`，禁用过渡动画以提升实时刷新性能**

### `updateChartTheme()`

更新折线图的颜色方案（文字色、网格线色、轴线色），主题切换后调用，无需重建实例。

### `updateChartData()`

根据 `currentHistoryMetric` 将 `nodeHistories` 中的对应指标数据写入折线图并刷新。

### `appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses)`

核心逻辑：根据最新状态快照追加历史点。

- **重置检测**：若节点 `start_time` 变化（重启）或 `tasks_processed` 回退（回滚），则清空该节点历史。
- **去重**：若时间戳相同则更新最后一个点，否则追加新点。
- 所有修改都受 `getCurrentHistoryLimit()` 约束裁剪。

### `extractProgressData(nodeHistories, metric)`

将本地维护的 `nodeHistories` 映射转换为 Chart.js 兼容的 `{x, y}` 坐标点数组。
- `metric` 参数决定了提取哪个指标（如 `tasks_succeeded`, `tasks_failed` 等）。

### `trimNodeHistories()`

根据 `webConfig.historyLimit` 裁剪前端本地维护的历史点数量，确保性能。返回布尔值表示历史数据是否发生变化。

### `getCurrentHistoryLimit()`

获取当前历史曲线保留点数限制。优先使用 `webConfig?.historyLimit`，无效时默认返回 `20`。

### `getChartThemeColors()`

从 CSS 变量读取当前主题（深色/浅色）下图表文字、网格线和边框颜色。

| 主题 | 文字色 | 网格色 | 边框色 |
|------|--------|--------|--------|
| 浅色 | `--carbon-900` | `--carbon-200` | `--carbon-300` |
| 深色 | `--carbon-200` | `--carbon-600` | `--carbon-500` |

---

## 指标切换器（模块级自动执行）

```ts
function initHistoryMetricSwitcher() { ... }
initHistoryMetricSwitcher(); // 模块级立即执行
```

`initHistoryMetricSwitcher()` 在 `dashboard_history.ts` 文件顶部模块作用域中自动调用，**不由 `main.ts` 主动调用**。它负责：
1. 同步按钮激活样式
2. 绑定点击事件，切换 `currentHistoryMetric` 后更新轴标题并重绘

## 数据流

```
GET /api/pull_status
  └─ { timestamp, data: { node: NodeStatus } }
        └─ appendStatusSnapshotToHistory() -> nodeHistories
              └─ updateChartData(currentHistoryMetric) -> Chart.js 重绘
```
