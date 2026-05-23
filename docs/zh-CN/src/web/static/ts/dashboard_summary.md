# dashboard_summary.ts

> 📅 最后更新日期: 2026/05/23

管理全局汇总统计数据的加载与渲染。为了减少通信量，大部分统计项改为前端基于节点状态实时聚合，后端仅提供图级剩余时间估算。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `summaryData` | `SummaryData` | 汇总数据，目前仅包含 `total_remain` |
| `summaryRev` | `number` | 上次拉取的版本号，用于增量拉取 |

## 函数

### `loadSummary()`

异步从 `GET /api/pull_summary?known_rev=N` 拉取汇总数据。

---

### `renderSummary()`

基于 `nodeStatuses` 的最新快照，前端聚合计算各项总量，并结合 `summaryData.total_remain` 渲染到汇总面板。

**前端聚合项：**
- `总成功任务`: 所有节点 `tasks_succeeded` 之和
- `总等待任务`: 所有节点 `tasks_pending` 之和
- `总错误任务`: 所有节点 `tasks_failed` 之和（大于 0 时可点击跳转至错误日志页）
- `总重复任务`: 所有节点 `tasks_duplicated` 之和
- `活动节点`: 处于运行状态（`status === 1`）的节点总数

**后端估算项：**
- `总剩余时间`: 后端根据图结构和当前各节点速率计算的全局剩余时间估算值

## 数据流

```
1. loadStatuses() -> 更新 nodeStatuses
2. loadSummary()  -> 更新 summaryData.total_remain
3. renderSummary() -> 前端聚合 + 后端估算 -> UI 展示
```
