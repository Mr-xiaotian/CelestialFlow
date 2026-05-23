# dashboard_analysis.ts

> 📅 最后更新日期: 2026/05/23

管理图分析信息的加载与分析面板的渲染。提供对 TaskGraph 拓扑结构的深度洞察，如环检测、层级分析等。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `analysisData` | `Record<string, any>` | 分析数据，包含图结构类型、DAG 状态等 |
| `analysisRev` | `number` | 数据版本号，用于增量拉取判断 |

## 函数

### `loadAnalysis()`

异步从 `GET /api/pull_analysis?known_rev=N` 拉取分析数据。

---

### `renderAnalysisInfo()`

将分析数据渲染到 `#analysis-info` 容器。若数据为空，则显示“暂无分析信息”。

**展示字段：**

| 显示标签 | 对应字段 | 说明 |
|---------|---------|------|
| `结构类型` | `class_name` | TaskGraph 具体的 Python 类名 |
| `是否 DAG` | `isDAG` | 是否为有向无环图，非 DAG 时带黄色警告样式 |
| `调度模式` | `schedule_mode` | `eager` 或 `staged` |
| `层级数量` | `layers_dict` | 图的拓扑分层深度 |

## 数据流

```
GET /api/pull_analysis
  └─ loadAnalysis() -> 更新 analysisData
        └─ renderAnalysisInfo() -> UI 列表展示
```
