# task_structure.ts

管理任务图结构数据的加载与 Mermaid 流程图的按需渲染。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `structureData` | `any[]` | 任务图根节点数组，从后端拉取 |
| `previousStructureDataJSON` | `string` | 上次快照，供变化检测 |

## 函数

### `loadStructure()`

异步从 `GET /api/pull_structure` 拉取图结构数组，更新 `structureData`。

---

### `getNodeId(node)`

将节点名中的非单词字符替换为 `_`，生成 Mermaid 兼容的节点 ID。

---

### `getShapeWrappedLabel(label, shape)`

根据形状类型生成 Mermaid 节点标签语法。

| `shape` 值 | Mermaid 语法 | 用途 |
|-----------|-------------|------|
| `box`（默认）| `[label]` | 普通矩形节点 |
| `round` | `(label)` | 圆角矩形 |
| `circle` | `((label))` | 圆形 |
| `rhombus` | `{{label}}` | 菱形（Router 节点） |
| `subgraph` | `[[label]]` | 子程序框（Splitter 节点） |
| `parallelogram` | `[/label/]` | 平行四边形（Redis 传输节点） |
| `db` | `[(label)]` | 数据库圆柱 |
| `hex` | `{{{label}}}` | 六边形 |
| `arrow` | `>label]` | 箭头形 |

---

### `renderMermaidStructure()`

从 `structureData` 和 `nodeStatuses` 构建 Mermaid 代码并渲染到 DOM。

**流程：**

1. 遍历 `structureData`（DFS `walk()`）：
   - 根据 `func_name` 确定节点形状（`_split` → subgraph，`_route` → rhombus，`_transport/_source/_ack` → parallelogram）
   - 根据 `nodeStatuses[tag].status` 确定节点样式类（`greenNode` / `greyNode` / `whiteNode`）
   - 收集所有边（去重 Set）
2. 根据当前主题选择 `classDef` 颜色方案
3. 生成 `graph TD` Mermaid 代码
4. 创建新 `<div>` 替换旧 `#mermaid-container`，调用 `window.mermaid.run()` 渲染

**节点状态颜色：**

| `status` | 样式类 | 含义 |
|----------|--------|------|
| `1` | `greenNode` | 运行中 |
| `2` | `greyNode` | 已停止 |
| 无数据 | `whiteNode` | 未启动 |
