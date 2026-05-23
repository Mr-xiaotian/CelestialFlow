# dashboard_history.ts

> 📅 最后更新日期: 2026/05/23

管理节点多指标历史数据的维护与折线图的初始化、重绘。历史数据现在完全在前端通过状态快照累积。

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

## 函数

### `initChart()`

初始化（或重建）Chart.js 折线图实例。

- 若已有实例，先调用 `destroy()` 销毁
- 根据当前主题设置文字色、网格色和轴线色
- 配置图例点击事件：切换节点显示/隐藏并同步到 localStorage

---

### `updateChartTheme()`

更新折线图的颜色方案（文字色、网格线色、轴线色），主题切换后调用。

---

### `updateChartData()`

根据 `currentHistoryMetric` 将 `nodeHistories` 中的对应指标数据写入折线图并刷新。

---

### `appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses)`

核心逻辑：根据最新状态快照追加历史点。

- **重置检测**：若节点 `start_time` 变化或 `tasks_processed` 回退，则清空该节点历史。
- **去重**：若时间戳相同则更新最后一个点，否则追加新点。

---

### `trimNodeHistories()`

根据 `webConfig.historyLimit` 裁剪前端本地维护的历史点数量，确保性能。

---

### `initHistoryMetricSwitcher()`

初始化卡片标题右侧的指标切换按钮组（完成/成功/错误/重复/等待），绑定点击事件触发图表重绘。

## 数据流

```
GET /api/pull_status 
  └─ { timestamp, data: { node: NodeStatus } }
        └─ appendStatusSnapshotToHistory() -> nodeHistories
              └─ updateChartData(currentHistoryMetric) -> Chart.js 重绘
```
