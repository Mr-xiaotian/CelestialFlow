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
```

## 数据流

```
1. loadStatuses() -> 更新 nodeStatuses
2. loadSummary()  -> 更新 summaryData.total_remain
3. renderSummary() -> 前端聚合 + 后端估算 -> UI 展示
```

## 使用示例

### 摘要数据的格式示例

以下示例展示汇总数据的前端聚合逻辑和数据结构：

```typescript
// 模拟从后端获取的摘要数据
// GET /api/pull_summary 返回的结构
const summaryResponse = {
    summary: {
        total_remain: 125.5,  // 后端估算的全局剩余时间（秒）
    },
    // 其他统计在前端基于 nodeStatuses 实时聚合
};

// 模拟节点状态快照（前端用于聚合计算）
const nodeStatuses: Record<string, NodeStatus> = {
    "StageA": {
        status: 1,
        tasks_succeeded: 1200,
        tasks_pending: 50,
        tasks_failed: 10,
        tasks_duplicated: 5,
    } as NodeStatus,
    "StageB": {
        status: 1,
        tasks_succeeded: 800,
        tasks_pending: 30,
        tasks_failed: 3,
        tasks_duplicated: 2,
    } as NodeStatus,
    "StageC": {
        status: 0,  // 未运行，不计入活动节点
        tasks_succeeded: 0,
        tasks_pending: 0,
        tasks_failed: 0,
        tasks_duplicated: 0,
    } as NodeStatus,
};

// renderSummary() 内部执行的前端聚合逻辑（示意）
function computeSummary(statuses: Record<string, NodeStatus>, totalRemain: number) {
    let totalSucceeded = 0;
    let totalPending = 0;
    let totalFailed = 0;
    let totalDuplicated = 0;
    let activeNodes = 0;

    for (const [tag, status] of Object.entries(statuses)) {
        totalSucceeded += status.tasks_succeeded || 0;
        totalPending += status.tasks_pending || 0;
        totalFailed += status.tasks_failed || 0;
        totalDuplicated += status.tasks_duplicated || 0;
        if (status.status === 1) activeNodes++;
    }

    return {
        totalSucceeded,     // 2000
        totalPending,       // 80
        totalFailed,        // 13
        totalDuplicated,    // 7
        activeNodes,        // 2
        totalRemain,        // 125.5s（来自后端）
    };
}

const summary = computeSummary(nodeStatuses, 125.5);
console.log("摘要统计:", summary);
// 输出：
// {
//   totalSucceeded: 2000,
//   totalPending: 80,
//   totalFailed: 13,
//   totalDuplicated: 7,
//   activeNodes: 2,
//   totalRemain: 125.5
// }

// 渲染为 HTML（renderSummary 内部逻辑示意）
function renderSummaryHtml(summary: ReturnType<typeof computeSummary>): string {
    return `
        <div class="summary-grid">
            <div class="summary-item">
                <span class="summary-label">总成功任务</span>
                <span class="summary-value success">${formatLargeNumber(summary.totalSucceeded)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">总等待任务</span>
                <span class="summary-value pending">${formatLargeNumber(summary.totalPending)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">总错误任务</span>
                <span class="summary-value error">${formatLargeNumber(summary.totalFailed)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">总重复任务</span>
                <span class="summary-value duplicate">${formatLargeNumber(summary.totalDuplicated)}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">活动节点</span>
                <span class="summary-value">${summary.activeNodes}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">总剩余时间</span>
                <span class="summary-value">${formatDuration(summary.totalRemain)}</span>
            </div>
        </div>
    `;
}
```
