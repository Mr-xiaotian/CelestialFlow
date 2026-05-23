# dashboard_statuses.ts

> 📅 最后更新日期: 2026/05/23

管理各节点运行状态数据的加载、同步与仪表盘状态卡片的动态渲染。

## 类型定义

```ts
type NodeStatus = {
  status: number;            // 0=未运行, 1=运行中, 2=已停止
  tasks_processed: number;   // 已处理任务总数
  tasks_pending: number;     // 队列中等待的任务数
  tasks_succeeded: number;   // 成功处理的任务数
  tasks_failed: number;      // 处理失败的任务数
  tasks_duplicated: number;  // 被去重过滤的任务数
  stage_mode: string;        // 节点模式（serial/thread）
  execution_mode: string;    // 运行模式（serial/thread/async）
  start_time: number;        // Unix 时间戳（秒）
  elapsed_time: number;      // 已运行秒数
  remaining_time: number;    // 预计剩余秒数
  task_avg_time: string;     // 平均每个任务耗时文本
};
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `nodeStatuses` | `Record<string, NodeStatus>` | 所有节点的当前状态快照 |
| `lastNodeStatuses` | `Record<string, NodeStatus>` | 上一轮状态快照，用于计算增量显示 |
| `statusRev` | `number` | 上次拉取的版本号，用于增量拉取 |
| `draggingNodeName` | `string \| null` | 当前正在拖动的节点名，防止重绘闪烁 |

## 函数

### `loadStatuses()`

异步从 `GET /api/pull_status?known_rev=N` 拉取节点状态。

- 成功获取新数据后，会调用 `appendStatusSnapshotToHistory()` 同步更新前端本地维护的历史序列。

---

### `initSortableDashboard()`

初始化节点卡片的拖拽排序功能（基于 Sortable.js）。移动端会自动禁用以防冲突。

---

### `renderDashboard()`

遍历 `nodeStatuses` 为每个节点生成状态卡片。

**卡片渲染特性：**
- **实时增量**：对比 `lastNodeStatuses` 自动计算成功/失败/等待/重复任务的增量并彩色显示。
- **状态标记**：卡片左侧边框颜色反映节点状态（绿色=运行中，灰色=已停止/未运行）。
- **四段式进度条**：直观展示成功（绿）、错误（红）、重复（黄）、等待（灰）的比例。
- **时间预估**：显示已运行时间、预计剩余时间及平均任务耗时。
- **交互跳转**：点击卡片中的错误数，自动跳转至“错误日志”标签页并预设该节点过滤器。

## 卡片样式类

| 状态 | CSS 类 | 说明 |
|------|--------|------|
| 运行中 | `node-card status-running` | 边框加深，标记活跃 |
| 已停止 | `node-card status-stopped` | 灰色边框 |
| 未启动 | `node-card` | 初始状态 |
