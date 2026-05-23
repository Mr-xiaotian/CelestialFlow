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

## 使用示例

### 手动调用图表初始化/更新

以下示例展示如何在浏览器控制台或自定义脚本中手动操作图表：

```typescript
// 假设页面已加载完成，全局变量可用

// 1. 手动初始化图表（如果尚未初始化）
initChart();
console.log("图表已初始化");

// 2. 手动构造一条历史数据点并追加
const timestamp = Date.now() / 1000;  // 当前时间戳（秒）
const statuses: Record<string, NodeStatus> = {
    "Processor": {
        status: 1,
        tasks_processed: 150,
        tasks_succeeded: 145,
        tasks_failed: 3,
        tasks_duplicated: 2,
        tasks_pending: 10,
        stage_mode: "thread",
        execution_mode: "thread",
        start_time: timestamp - 300,
        elapsed_time: 300,
        remaining_time: 20,
        task_avg_time: "2.00s/it",
    },
    "Validator": {
        status: 1,
        tasks_processed: 80,
        tasks_succeeded: 78,
        tasks_failed: 1,
        tasks_duplicated: 1,
        tasks_pending: 5,
        stage_mode: "serial",
        execution_mode: "serial",
        start_time: timestamp - 250,
        elapsed_time: 250,
        remaining_time: 15,
        task_avg_time: "3.12s/it",
    },
};

// 3. 追加状态快照到历史序列
// appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses)
// 这会自动更新 nodeHistories 全局变量

// 4. 切换当前显示的指标
// currentHistoryMetric = "tasks_succeeded";
// updateChartData();  // 刷新图表

// 5. 切换指标（模拟点击不同的指标按钮）
function switchMetric(metric: HistoryMetricKey) {
    // currentHistoryMetric = metric;
    // updateHistoryMetricButtons();
    // updateChartData();
    console.log(`切换到指标: ${metric}`);
}

switchMetric("tasks_failed");  // 显示失败趋势
switchMetric("tasks_pending"); // 显示等待队列趋势

// 6. 手动裁剪历史数据（强制保留最后 N 条）
// webConfig.historyLimit = 10;
// const changed = trimNodeHistories();
// if (changed) updateChartData();

// 7. 在主题切换后更新图表颜色
// updateChartTheme();
```

### 构造历史数据并直接渲染

```typescript
// 直接手动构造完整的 nodeHistories 数据
const mockHistory: Record<string, NodeHistory> = {
    "Processor": [
        { timestamp: 1000, tasks_processed: 10, tasks_succeeded: 9, tasks_failed: 1, tasks_duplicated: 0, tasks_pending: 90 },
        { timestamp: 1005, tasks_processed: 25, tasks_succeeded: 23, tasks_failed: 1, tasks_duplicated: 1, tasks_pending: 75 },
        { timestamp: 1010, tasks_processed: 40, tasks_succeeded: 37, tasks_failed: 2, tasks_duplicated: 1, tasks_pending: 60 },
        { timestamp: 1015, tasks_processed: 55, tasks_succeeded: 51, tasks_failed: 2, tasks_duplicated: 2, tasks_pending: 45 },
        { timestamp: 1020, tasks_processed: 70, tasks_succeeded: 65, tasks_failed: 3, tasks_duplicated: 2, tasks_pending: 30 },
    ],
};

// nodeHistories = mockHistory;
// updateChartData();  // 渲染到折线图

// 使用 getColor 获取节点的折线颜色
// const color = getColor(0);  // 第 1 个节点，矢车菊蓝
```
