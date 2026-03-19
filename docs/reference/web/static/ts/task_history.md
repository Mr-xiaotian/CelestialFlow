# task_history.ts

管理节点任务处理历史数据的加载与折线图的初始化、更新。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | 各节点历史数据，从后端拉取 |
| `progressChart` | `any` | Chart.js 实例 |
| `hiddenNodes` | `Set<string>` | 折线图中已隐藏的节点集合，持久化至 localStorage 及后端配置 |
| `previousNodeHistoriesJSON` | `string` | 上一次数据快照，供 `main.ts` 做变化检测 |

## 类型定义

```ts
type NodeHistory = Array<{ timestamp: number; tasks_processed: number }>;
```

## 函数

### `loadHistories()`

异步从 `GET /api/pull_history` 拉取历史数据，更新 `nodeHistories`。

> 注意：此函数**不**更新 `previousNodeHistoriesJSON`，变化比较由 `main.ts` 的 `refreshAll()` 负责。

---

### `initChart()`

初始化（或重建）Chart.js 折线图实例。

- 若已有实例，先调用 `destroy()` 销毁
- 根据当前主题（`dark-theme` CSS 类）设置文字色、网格色和轴线色
- 配置图例点击事件：点击图例项可切换节点显示/隐藏，并同步保存到 localStorage 和后端配置

**主题切换时需要重建图实例**，因此 `main.ts` 在主题切换后依次调用 `initChart()` 和 `updateChartData()`。

---

### `updateChartData()`

将 `nodeHistories` 数据写入折线图并刷新。

1. 调用 `extractProgressData(nodeHistories)` 转换为 `{x, y}` 坐标点
2. 为每个节点生成 dataset，颜色由 `getColor(index)` 分配，`hidden` 状态由 `hiddenNodes` 决定
3. 用第一个节点的时间戳序列生成 X 轴 labels（本地时间字符串）
4. 调用 `progressChart.update()` 重绘

## 数据流

```
/api/pull_history
  └─ { "node_tag": [{timestamp, tasks_processed}, ...], ... }
        └─ loadHistories() → nodeHistories
              └─ extractProgressData() → {x, y}[] per node
                    └─ updateChartData() → Chart.js 重绘
```
