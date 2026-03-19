# task_statuses.ts

管理各节点运行状态数据的加载与仪表盘状态卡片的渲染。

## 类型定义

```ts
type NodeStatus = {
  status: number;            // 0=未运行, 1=运行中, 2=已停止
  tasks_processed: number;   // 已处理任务数
  tasks_pending: number;     // 等待中任务数
  tasks_successed: number;   // 累计成功数
  add_tasks_successed: number; // 本周期新增成功数
  add_tasks_pending: number;
  tasks_failed: number;
  add_tasks_failed: number;
  tasks_duplicated: number;
  add_tasks_duplicated: number;
  stage_mode: string;        // serial / thread
  execution_mode: string;    // serial / thread / process / async
  start_time: number;        // Unix 时间戳（秒）
  elapsed_time: number;      // 已运行秒数
  remaining_time: number;    // 预计剩余秒数
  task_avg_time: string;     // 平均任务耗时字符串
};
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `nodeStatuses` | `Record<string, NodeStatus>` | 所有节点的当前状态 |
| `previousNodeStatusesJSON` | `string` | 上次快照，供变化检测 |
| `draggingNodeName` | `string \| null` | 当前正在拖动的节点名，渲染时跳过 |

## 函数

### `loadStatuses()`

异步从 `GET /api/pull_status` 拉取节点状态，更新 `nodeStatuses`。

---

### `initSortableDashboard()`

初始化节点卡片的拖拽排序（Sortable.js）。移动端设备跳过初始化。

拖动期间记录 `draggingNodeName`，防止 `renderDashboard()` 重绘被拖动的卡片导致位置跳动。

---

### `renderDashboard()`

遍历 `nodeStatuses`，为每个节点生成状态卡片并插入 `#dashboard-grid`。

**卡片内容：**
- 节点名称 + 状态徽章（未运行 / 运行中 / 已停止）
- 统计数据：已成功、等待中、错误数（可点击跳转）、重复数、节点模式、运行模式
- 开始时间
- 任务完成率进度条（含已用/剩余时间、平均耗时、百分比）

错误数字带 `error-clickable` 样式，点击后调用 `jumpToErrorsTab(nodeName)` 跳转并预设筛选。

---

### `jumpToErrorsTab(nodeName)`

切换到「错误日志」标签页，并将节点筛选器设置为指定节点，触发 `change` 事件刷新列表。

## 徽章状态映射

| `status` 值 | CSS 类 | 文字 |
|-------------|--------|------|
| `0` | `badge-inactive` | 未运行 |
| `1` | `badge-running` | 运行中 |
| `2` | `badge-completed` | 已停止 |
