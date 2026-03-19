# task_topology.ts

管理图拓扑信息的加载与拓扑面板的渲染。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `topologyData` | `Record<string, any>` | 拓扑数据，从后端拉取 |
| `previousTopologyDataJSON` | `string` | 上次快照，供变化检测 |

## 函数

### `loadTopology()`

异步从 `GET /api/pull_topology` 拉取拓扑数据，更新 `topologyData`。

---

### `renderTopologyInfo()`

将拓扑数据渲染到 `#topology-info` 容器。

若数据为空，显示占位文字「暂无拓扑信息」。

**展示字段：**

| `topologyData` 字段 | 显示标签 | 说明 |
|--------------------|---------|------|
| `class_name` | 结构类型 | TaskGraph 的拓扑类名（如 TaskChain、TaskLoop 等） |
| `isDAG` | 是否 DAG | 布尔值，显示「是（无环）」或「否（存在环）」并带颜色标记 |
| `schedule_mode` | 调度模式 | `eager` 或 `staged` |
| `layers_dict` | 层级数量 | `Object.keys(layers_dict).length` 即层数 |

`isDAG` 为 `true` 时文字带 `ok`（绿色）样式，为 `false` 时带 `warn`（橙色）样式。
