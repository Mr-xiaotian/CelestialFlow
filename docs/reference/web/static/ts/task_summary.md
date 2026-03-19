# task_summary.ts

管理总体统计数据的加载与摘要面板的渲染。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `summaryData` | `Record<string, any>` | 汇总统计数据，从后端拉取 |
| `previousSummaryDataJSON` | `string` | 上次快照，供变化检测 |

## 函数

### `loadSummary()`

异步从 `GET /api/pull_summary` 拉取汇总数据，更新 `summaryData`。

---

### `renderSummary()`

将 `summaryData` 中的统计值更新到 `#summary-card` 面板中的各 DOM 元素。

**展示字段：**

| `summaryData` 字段 | DOM 元素 | 说明 |
|--------------------|---------|------|
| `total_successed` | `#total-successed` | 总成功任务数 |
| `total_pending` | `#total-pending` | 总等待任务数 |
| `total_failed` | `#total-failed` | 总错误任务数 |
| `total_duplicated` | `#total-duplicated` | 总重复任务数 |
| `total_nodes` | `#total-nodes` | 活动节点数 |
| `total_remain` | `#total-remain` | 总剩余时间（经 `formatDuration()` 格式化） |

当 `total_failed > 0` 时，为 `#total-failed` 添加 `error-clickable` 样式，点击跳转到错误日志页（不预设节点筛选）。

---

### `jumpToErrorsTabNoFilter()`

切换到「错误日志」标签页，并清除节点筛选器（显示全部错误）。
