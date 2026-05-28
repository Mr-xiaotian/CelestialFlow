# dashboard_analysis.ts

> 📅 最后更新日期: 2026/05/28

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
| `结构类型` | `className` | TaskGraph 具体的 Python 类名 |
| `是否 DAG` | `isDAG` | 是否为有向无环图，非 DAG 时带黄色警告样式 |
| `调度模式` | `scheduleMode` | `eager` 或 `staged` |
| `层级数量` | `layersDict` | 图的拓扑分层深度 |

## 数据流

```
GET /api/pull_analysis
  └─ loadAnalysis() -> 更新 analysisData
        └─ renderAnalysisInfo() -> UI 列表展示
```

## 使用示例

### 分析数据结构和渲染调用链条

以下是分析数据在 TypeScript 端的结构和渲染流程示例：

```typescript
// 分析数据的典型结构（来自后端 GET /api/pull_analysis）
// 注意：后端返回蛇形字段，前端接收后转为驼峰命名
const analysisPayload = {
    analysis: {
        className: "TaskGraph",
        isDAG: true,
        scheduleMode: "eager",
        layersDict: {0: ["StageA"], 1: ["StageB", "StageC"], 2: ["StageD"]},
    }
};

// 这些数据通过以下链条被处理和渲染：

// 1. loadAnalysis() 拉取并更新全局变量
// analysisData 结构：Record<string, any>
// 例如：{ className, isDAG, scheduleMode, layersDict }

// 2. renderAnalysisInfo() 将其渲染到 #analysis-info 容器
//    实际渲染逻辑（示意）：
function renderAnalysisInfoExample(data: Record<string, any>) {
    const container = document.getElementById("analysis-info");
    if (!container) return;

    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = "<p>暂无分析信息</p>";
        return;
    }

    container.innerHTML = `
        <div class="analysis-item">
            <span class="analysis-label">结构类型</span>
            <span class="analysis-value">${escapeHtml(data.className || "-")}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">是否 DAG</span>
            <span class="analysis-value ${data.isDAG ? '' : 'warning'}">
                ${data.isDAG ? "是（无环）" : "否（存在环）"}
            </span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">调度模式</span>
            <span class="analysis-value">${escapeHtml(data.scheduleMode || "-")}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">层级数量</span>
            <span class="analysis-value">
                ${data.layersDict ? Object.keys(data.layersDict).length : 0}
            </span>
        </div>
    `;
}

// 3. 完整的调用链条
async function fullAnalysisFlow() {
    // 调用 fetch 拉取数据
    const res = await fetch("/api/pull_analysis?known_rev=0");
    const data = await res.json();

    // 更新全局缓存
    // analysisData = data; (由 loadAnalysis 内部维护)
    // analysisRev = data.rev ?? 0;

    // 触发渲染
    renderAnalysisInfoExample(data);
}
```
