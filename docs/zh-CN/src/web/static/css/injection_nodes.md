# injection_nodes.css

> 📅 最后更新日期: 2026/06/22

负责任务注入页左侧节点浏览列表的样式定义，包括节点项、选中态、禁用态和"已编辑"标签。


## 节点列表容器 (`.node-list`)

- 纵向 flex 布局，`gap: 0.5rem`。
- `max-height: 30rem`，超出时纵向滚动（`overflow-y: auto`）。

## 节点项 (`.node-item`)

- **布局**: `flex` 左右分布（节点信息 + 右侧标签），`gap: 0.75rem`。
- **基础样式**: 圆角 `0.75rem`，边框 `1px solid --carbon-200`。
- **悬停效果**: 背景变浅（`--carbon-50`），边框变蓝（`--cornflower-300`），轻微上移 `-1px`。
- **深色模式**: 背景 `--carbon-700`，悬停时 `--carbon-600`。

| CSS 类 | 说明 |
|--------|------|
| `.node-item` | 基础节点项样式 |
| `.node-item.active-node` | 当前选中节点：蓝色边框（`--cornflower-500`）+ 浅蓝背景（`--cornflower-50`） |
| `.disabled-node` | 不可注入节点：`opacity: 0.55`，`cursor: not-allowed`，`pointer-events: none` |

## 节点信息区域 (`.node-info`)

- `min-width: 0`，`flex: 1`，允许文本在窄空间下收缩。

## 节点名称 (`.node-name`)

- `font-weight: 600`，`word-break: break-all`。
- 浅色模式 `--carbon-800`，深色模式 `--carbon-100`。

## "已编辑"标签 (`.node-side-tag`)

- `inline-flex`，`flex-shrink: 0`。
- 胶囊形（`border-radius: 999px`），小型内边距。
- 浅色模式：蓝底（`--cornflower-100`）+ 蓝字（`--cornflower-700`）。
- 深色模式：深蓝底（`--cornflower-800`）+ 浅蓝字（`--cornflower-100`）。

## 关联模块

- 节点列表由 `injection.ts` 中的 `renderNodeList()` 动态渲染。
- 选中逻辑由 `selectNode()` 驱动，通过切换 `.active-node` 类实现高亮。
- "仅显示可注入节点"开关过滤逻辑参考 `isInjectableNode()`。
