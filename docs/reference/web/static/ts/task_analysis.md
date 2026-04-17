# task_analysis.ts

管理图分析信息的加载与分析面板的渲染。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `analysisData` | `Record<string, any>` | 分析数据，从后端拉取 |
| `analysisRev` | `number` | 上次拉取的版本号，用于增量拉取（`known_rev`） |

## 函数

### `loadAnalysis()`

异步从 `GET /api/pull_analysis?known_rev=N` 拉取分析数据。若服务端数据未变化（`body.data === null`），返回 `false`；否则更新 `analysisData` 和 `analysisRev`，返回 `true`。

---

### `renderAnalysisInfo()`

将分析数据渲染到 `#analysis-info` 容器。

若数据为空，显示占位文字「暂无分析信息」。

**展示字段：**

| `analysisData` 字段 | 显示标签 | 说明 |
|--------------------|---------|------|
| `class_name` | 结构类型 | TaskGraph 的拓扑类名（如 TaskChain、TaskLoop 等） |
| `isDAG` | 是否 DAG | 布尔值，显示「是（无环）」或「否（存在环）」并带颜色标记 |
| `schedule_mode` | 调度模式 | `eager` 或 `staged` |
| `layers_dict` | 层级数量 | `Object.keys(layers_dict).length` 即层数 |

`isDAG` 为 `true` 时文字带 `ok`（绿色）样式，为 `false` 时带 `warn`（橙色）样式。
