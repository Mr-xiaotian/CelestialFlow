# dashboard_structure.ts

> 📅 最后更新日期: 2026/05/23

管理任务图结构数据的加载与 Mermaid 流程图的可视化渲染，支持基于节点状态的实时着色和边增量显示。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `structureData` | `any[]` | 任务图根节点数组（有向图结构） |
| `structureRev` | `number` | 上次拉取的版本号，用于增量拉取 |

## 函数

### `loadStructure()`

异步从 `GET /api/pull_structure?known_rev=N` 拉取图结构。

---

### `getNodeId(node)`

生成 Mermaid 兼容的节点 ID（替换非单词字符为 `_`）。

---

### `getShapeWrappedLabel(label, shape)`

根据节点的功能类型（`func_name`）生成对应的 Mermaid 形状语法。

| 功能类型 | Mermaid 形状 | 样式 |
|---------|-------------|------|
| `_split` | `[[label]]` | 子程序框 |
| `_route` | `{{label}}` | 菱形（决策） |
| `_transport` / `_source` / `_ack` | `[/label/]` | 平行四边形 (IO) |
| 其他 | `[label]` | 普通矩形 |

---

### `renderMermaidStructure(statuses)`

构建 Mermaid 流程图代码并调用 `mermaid.run()` 渲染。

**主要特性：**
- **动态着色**：根据 `statuses` 中的 `status` 码自动应用颜色类（绿色=运行中，灰色=已停止，白色=未启动）。
- **主题适配**：自动识别 `dark-theme` 类，切换 Mermaid 的 `classDef` 颜色方案。
- **边增量显示**：若 `webConfig.showStructureEdgeDelta` 为开启状态，且上一轮状态有成功任务增量，则在边（Edge）上显示 `|+N|` 标签。

## 节点状态颜色映射

| `status` | 样式类 | 含义 |
|----------|--------|------|
| `1` | `greenNode` | 运行中 |
| `2` | `greyNode` | 已停止 |
| 无/其他 | `whiteNode` | 未启动/未知 |
```

## 数据流

```
1. loadStructure() -> 更新 structureData
2. renderMermaidStructure(nodeStatuses) 
     └─ 遍历结构生成 Mermaid 代码
     └─ 应用 classDef 样式
     └─ mermaid.run() -> 渲染 SVG
```

## 使用示例

### Mermaid 结构图渲染的调用示例

以下示例展示如何在浏览器控制台中手动触发结构图渲染：

```typescript
// 1. 模拟从后端获取的结构数据
const mockStructure = [
    {
        tag: "DataLoader",
        func_name: "load_data",
        children: ["Preprocessor"],
    },
    {
        tag: "Preprocessor",
        func_name: "clean_data",
        children: ["Analyzer", "Validator"],
    },
    {
        tag: "Analyzer",
        func_name: "analyze",
        children: ["Exporter"],
    },
    {
        tag: "Validator",
        func_name: "validate",
        children: ["Exporter"],
    },
    {
        tag: "Exporter",
        func_name: "export",
        children: [],
    },
];

// 2. 模拟节点状态着色数据
const mockStatuses: Record<string, NodeStatus> = {
    DataLoader: { status: 2 } as NodeStatus,   // 已停止
    Preprocessor: { status: 1 } as NodeStatus,  // 运行中
    Analyzer: { status: 1 } as NodeStatus,      // 运行中
    Validator: { status: 0 } as NodeStatus,     // 未启动
    Exporter: { status: 0 } as NodeStatus,      // 未启动
};

// 3. 生成 Mermaid 兼容的节点 ID
// getNodeId("DataLoader") -> "DataLoader"
// getNodeId("my-node") -> "my_node"

// 4. 获取节点形状
// 根据 func_name 决定形状：
// - "_split" -> [[label]] (子程序框)
// - "_route" -> {{label}} (菱形)
// - "_transport"|"_source"|"_ack" -> [/label/] (平行四边形)
// - 其他 -> [label] (普通矩形)
function getNodeShape(funcName: string, label: string): string {
    if (funcName === "_split") return `[[${label}]]`;
    if (funcName === "_route") return `{{${label}}}`;
    if (["_transport", "_source", "_ack"].includes(funcName)) return `[/${label}/]`;
    return `[${label}]`;
}

// 5. 手动调用渲染
// renderMermaidStructure(mockStatuses);
// 这会在 .mermaid-card 容器中生成类似以下的 Mermaid 代码：
//
// ```mermaid
// flowchart LR
//   DataLoader["DataLoader"]
//   Preprocessor["Preprocessor"]
//   Analyzer["Analyze"]
//   Validator["Validator"]
//   Exporter["Exporter"]
//   DataLoader --> Preprocessor
//   Preprocessor --> Analyzer
//   Preprocessor --> Validator
//   Analyzer --> Exporter
//   Validator --> Exporter
//   classDef greenNode fill:#4caf50,stroke:#2e7d32
//   classDef greyNode fill:#9e9e9e,stroke:#616161
//   classDef whiteNode fill:#ffffff,stroke:#ccc
//   class Preprocessor greenNode
//   class Analyzer greenNode
//   class DataLoader greyNode
//   class Validator whiteNode
//   class Exporter whiteNode
// ```

// 6. 检查 Mermaid 是否已正确渲染
function checkMermaidRendered(): boolean {
    const svg = document.querySelector(".mermaid-card svg");
    return svg !== null;
}

console.log(`Mermaid 已渲染: ${checkMermaidRendered()}`);
```
