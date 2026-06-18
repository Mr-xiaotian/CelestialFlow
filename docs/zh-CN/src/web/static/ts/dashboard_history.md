# dashboard_history.ts

> 📅 最后更新日期: 2026/06/18

管理节点多指标历史数据的维护与折线图的初始化、重绘。历史数据完全在前端通过状态快照累积，不依赖独立的后端 API。

## 类型定义

```typescript
/** 历史图支持切换展示的指标字段键 */
type HistoryMetricKey =
  | "tasks_processed"
  | "tasks_succeeded"
  | "tasks_failed"
  | "tasks_duplicated"
  | "tasks_pending"
  | "total_tasks_pending"
  | "delta_tasks_processed"
  | "delta_tasks_succeeded"
  | "delta_tasks_failed"
  | "delta_tasks_duplicated";

/** 单个节点在某一时刻的历史采样点 */
type NodeHistoryPoint = {
  timestamp: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  tasks_duplicated: number;
  tasks_pending: number;
  total_tasks_pending: number;
};

  type NodeHistory = NodeHistoryPoint[];

type ThemeColors = {
  text: string;   // 坐标轴与图例文字颜色
  grid: string;   // 网格线颜色
  border: string; // 坐标轴边框颜色
};
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | 各节点本地维护的历史数据序列 |
| `progressChart` | `ChartInstance \| null` | Chart.js 折线图实例 |
| `hiddenNodes` | `Set<string>` | 用户在图例中手动隐藏的节点集合（仅页面生命周期内保留，**不持久化**） |
| `currentHistoryMetric` | `HistoryMetricKey` | 当前图表展示的指标，默认为 `"tasks_processed"` |
| `metricDots` | `NodeListOf<HTMLLabelElement>` | 所有 `.metric-dot` 标签元素，用于切换指标显示 |

## 辅助函数

### `getColor(index: number): string`

根据索引从 CSS 变量读取预定义主题色，用于区分不同节点的折线。共 9 色循环取模。

| Index | CSS 变量 | 说明 |
|-------|---------|------|
| 0 | `--cornflower-500` | 矢车菊蓝 |
| 1 | `--jade-500` | 翡翠绿 |
| 2 | `--marigold-500` | 万寿菊黄 |
| 3 | `--crimson-500` | 深红 |
| 4 | `--violet-500` | 紫罗兰 |
| 5 | `--rose-500` | 玫瑰红 |
| 6 | `--jade-400` | 翡翠绿（浅） |
| 7 | `--sky-500` | 天蓝 |
| 8 | `--amber-500` | 琥珀橙 |

### `getHistoryMetricLabelKey(metric: HistoryMetricKey): string`

将 `HistoryMetricKey` 映射为国际化翻译 key。

| 输入 | 输出 |
|------|------|
| `tasks_processed` | `chart.metric.processed` |
| `tasks_succeeded` | `chart.metric.succeeded` |
| `tasks_failed` | `chart.metric.failed` |
| `tasks_duplicated` | `chart.metric.duplicated` |
| `tasks_pending` | `chart.metric.pending` |
| `total_tasks_pending` | `chart.metric.pendingGlobal` |
| `delta_tasks_processed` | `chart.metric.deltaProcessed` |
| `delta_tasks_succeeded` | `chart.metric.deltaSucceeded` |
| `delta_tasks_failed` | `chart.metric.deltaFailed` |
| `delta_tasks_duplicated` | `chart.metric.deltaDuplicated` |

### `updateHistoryMetricButtons(): void`

遍历 `metricDots`，根据 `currentHistoryMetric` 为匹配的 `<label>` 添加 `.active` 类，其余移除。

### `updateChartAxisLabels(): void`

更新折线图 X/Y 轴标题文本，分别映射为当前语言的"时间"和对应指标名。

---

## 核心逻辑函数

### `initChart(): void`

初始化（或重建）Chart.js 折线图实例。

- 若已有实例，先调用 `destroy()` 销毁
- 调用 `getChartThemeColors()` 读取当前主题的文字色、网格色和轴线色
- 配置图例点击事件：切换节点显示/隐藏并同步到 `hiddenNodes` Set
- **禁用动画**（`animation: false`）以提升实时刷新性能
- 交互模式为 `index`，`intersect: false`

### `updateChartTheme(): void`

更新折线图的颜色方案（文字色、网格线色、轴线色），主题切换后调用，无需重建实例。

### `updateChartData(): void`

根据 `currentHistoryMetric` 调用 `extractProgressData()` 将 `nodeHistories` 中的对应指标数据写入折线图并刷新。会同步 `legendItem.hidden` 确保图例渲染与 `hiddenNodes` 一致。

### `appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses?): boolean`

核心逻辑：根据最新状态快照追加历史点。

- **重置检测**：若节点 `start_time` 变化（重启）或 `tasks_processed` 回退（回滚），则清空该节点历史。
- **去重**：若时间戳相同则更新最后一个点，否则追加新点。
- **裁剪**：所有修改都受 `getCurrentHistoryLimit()` 约束。
- **返回值**: `boolean` — 历史数据是否发生了变化。

### `extractProgressData(histories, metric): Record<string, Array<{x: number; y: number}>>`

将本地维护的 `nodeHistories` 映射转换为 Chart.js 兼容的 `{x, y}` 坐标点数组。

- **累计模式**: 直接读取采样点原始字段值。
- **增量模式（delta）**: 当 `metric` 以 `delta_` 开头时，计算相邻采样点差值/时间差得到每秒速率。第一个点强制 `y = 0`。

### `trimNodeHistories(): boolean`

根据 `webConfig.dashboard.historyLimit` 裁剪前端本地维护的历史点数量。返回布尔值表示历史数据是否发生变化。

### `getCurrentHistoryLimit(): number`

获取当前历史曲线保留点数限制。优先使用 `webConfig.dashboard.historyLimit`，无效时默认返回 `20`。

### `getChartThemeColors(): ThemeColors`

从 CSS 变量读取当前主题（深色/浅色）下图表文字、网格线和边框颜色。

| 主题 | 文字色 | 网格色 | 边框色 |
|------|--------|--------|--------|
| 浅色 | `--carbon-900` | `--carbon-200` | `--carbon-300` |
| 深色 | `--carbon-200` | `--carbon-600` | `--carbon-500` |

---

## 指标切换器（模块级自动执行）

```typescript
function initHistoryMetricSwitcher() { ... }
initHistoryMetricSwitcher(); // 模块级立即执行
```

`initHistoryMetricSwitcher()` 在模块作用域中自动调用，**不由 `main.ts` 主动调用**。它负责：

1. 同步 `metricDots` 按钮激活样式
2. 绑定点击事件，切换 `currentHistoryMetric` 后更新轴标题并重绘

## 数据流

```mermaid
flowchart LR
    subgraph "dashboard_statuses.ts"
        LS[loadStatuses]
    end
    subgraph "dashboard_history.ts"
        AS[appendStatusSnapshotToHistory]
        NH[nodeHistories]
        EC[extractProgressData]
        UC[updateChartData]
        CH[Chart.js 实例]
    end
    LS -->|timestamp + statuses| AS
    AS --> NH
    NH --> EC
    EC -->|{x, y} 坐标| UC
    UC --> CH
```

## 使用示例

```typescript
// 手动构造历史数据并渲染
const mockHistory: Record<string, NodeHistory> = {
  "Processor": [
    { timestamp: 1000, tasks_processed: 10, tasks_succeeded: 9, tasks_failed: 1, tasks_duplicated: 0, tasks_pending: 90, total_tasks_pending: 120 },
    { timestamp: 1005, tasks_processed: 25, tasks_succeeded: 23, tasks_failed: 1, tasks_duplicated: 1, tasks_pending: 75, total_tasks_pending: 105 },
  ],
};

// nodeHistories = mockHistory;
// currentHistoryMetric = "tasks_succeeded";
// updateChartData();  // 渲染到折线图

// 主题切换后更新图表颜色
// updateChartTheme();

// 手动裁剪历史数据
// webConfig.dashboard.historyLimit = 10;
// if (trimNodeHistories()) updateChartData();
```
