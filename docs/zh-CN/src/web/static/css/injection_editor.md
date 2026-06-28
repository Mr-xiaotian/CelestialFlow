# injection_editor.css

> 📅 最后更新日期: 2026/06/28

负责任务注入页右侧编辑器的样式定义，包括 JSON 输入区域、校验消息、操作按钮组。


## 编辑器容器 (`.injection-editor-card`)

- 采用纵向 flex 布局，固定间距 `gap: 1rem`。

## 编辑器头部 (`.editor-header`)

- **布局**: `flex` 左右分布，左侧为说明文字 + 当前节点信息，右侧为操作按钮组。
- `.editor-node-meta`: 允许在窄宽度下收缩（`min-width: 0`）。
- `.editor-caption`: "当前节点"标题上方的小型说明文字，`0.75rem`，灰调（`--carbon-500`）。

## 当前节点信息 (`.editor-node-row`)

- 节点名与右侧"已编辑"标签的行布局，支持 `flex-wrap: wrap`。
- `.current-node-name`: 当前选中节点名称，`1rem`，`font-weight: 600`。

## 按钮样式 (`.btn-small`, `.btn-select`, `.btn-clear`)

| 选择器 | 用途 | 背景色 | 文字色 |
|--------|------|--------|--------|
| `.btn-small` | 通用小按钮 | — | — |
| `.btn-select` | 校验/格式化按钮 | `--cornflower-50`（浅）/ `--cornflower-700`（深） | `--cornflower-700`（浅）/ `--carbon-100`（深） |
| `.btn-clear` | 清空草稿按钮 | `--carbon-100`（浅）/ `--carbon-600`（深） | `--carbon-700`（浅）/ `--carbon-100`（深） |

- **禁用态**: `opacity: 0.6`，`cursor: not-allowed`。

## JSON 输入区 (`.json-input-section`)

- **JSON 头部 (`.json-header`)**: 标签与"填入终止符模板"按钮左右分布。
- **JSON 标签 (`.json-label`)**: `0.75rem`，`font-weight: 500`。
- **模板按钮 (`.example-btn`)**: 无背景文本按钮，`color: --cornflower-500`，悬停加深。
- **JSON 编辑框 (`.json-textarea`)**:
  - 等宽字体（`Monaco, Menlo, monospace`），`min-height: 20rem`，支持垂直拉伸。
  - 聚焦时边框变为 `--cornflower-400`。
  - 禁用态：`--carbon-50` 背景，`--carbon-400` 文字。

## 校验消息 (`.validation-message`)

| 状态 | CSS 类 | 颜色 |
|------|--------|------|
| 成功 | `.validation-success` | `--jade-600`（浅）/ `--jade-400`（深） |
| 失败 | `.validation-error` | `--crimson-600`（浅）/ `--crimson-400`（深） |
| 中性 | `.validation-neutral` | `--carbon-500`（浅）/ `--carbon-400`（深） |

- `min-height: 1.25rem`，`font-size: 0.75rem`，位于 JSON 编辑框下方。

## 编辑器底部按钮组 (`.editor-actions`)

- `flex` 布局，`gap: 0.75rem`，`flex-wrap: wrap`。

## 关联模块

- 交互逻辑由 `injection.ts` 中的 `renderCurrentNodeEditor()`、`validateCurrentDraft()`、`formatCurrentDraft()` 等函数驱动。
