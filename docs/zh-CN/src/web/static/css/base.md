# base.css

> 最后更新日期: 2026/06/18

负责系统的全局基础样式、暗黑模式切换、通用组件（卡片、选项卡、徽章）、响应式基础布局以及卡片布局编辑器模态窗样式。

## 全局基础

- **重置**: 统一盒模型（`border-box`）并设置默认字体序列。
- **背景与颜色**: 定义 body 在浅色（`--carbon-50`）和深色（`--carbon-900`）模式下的背景颜色。
- **容器**: `.container` 限制内容最大宽度为 `1200px` 并水平居中。

## 核心组件样式

### 头部与导航 (`header`)
- **控制面板 (`.control-panel`)**: 包含刷新间隔选择、设置齿轮和主题切换按钮。
- **设置面板 (`.settings-panel`)**: 采用绝对定位悬浮在齿轮下方，支持语言切换、历史限制、每页条数等配置项。

### 选项卡系统 (`.tabs`)
- 实现横向排列的页签导航，支持 `.active` 类高亮当前选中的模块（仪表盘、错误日志、任务注入）。

### 通用卡片 (`.card`)
- 具有统一的背景圆角（`1rem`）和阴影效果。
- **悬停反馈**: 悬停时会产生轻微的向上位移（`translateY(-2px)`）。

## 辅助类名

- **颜色类**: 提供 `.text-success` (绿), `.text-error` (红), `.text-pending` (灰), `.text-duplicate` (橙) 等快速着色类。
- **增量类**: `.text-delta-*` 系列用于仪表盘中显示较浅的指标变化数值。
- **隐藏**: `.hidden` 类用于在 JS 中快速控制元素的显隐。

## 模态遮罩 (`.overlay`)

- **`.overlay`**: 固定定位全屏半透明黑色遮罩（`rgba(0,0,0,0.4)`），`z-index: 200`，居中弹性布局，用于承载卡片布局编辑器等模态窗口。
- **`.overlay.hidden`**: 将遮罩设为 `display: none`，配合 JS 控制弹窗显隐。

## 卡片布局编辑器 (`.layout-editor` 系列)

卡片布局编辑器以模态窗形式悬浮于遮罩之上，支持拖拽重排三栏仪表盘卡片。主要子选择器：

| 选择器 | 说明 |
|--------|------|
| `.layout-editor` | 编辑器主容器：圆角白底卡片，`max-width: 700px`，纵向 flex 布局 |
| `.dark-theme .layout-editor` | 深色模式下使用 `--carbon-800` 背景 |
| `.layout-editor-header` | 标题栏：左右分布，标题居左、关闭按钮居右 |
| `.layout-editor-title` | 标题文字：`1.1rem`，`font-weight: 600` |
| `.layout-editor-columns` | 三栏网格布局区：`grid-template-columns: repeat(3, 1fr)`，可纵向滚动 |
| `.layout-column` | 单栏容器：纵向 flex 列 |
| `.layout-column-header` | 栏位标题：居中、下划线分隔、小号字体 |
| `.layout-column-dropzone` | 拖拽放置区：虚线边框、最小高度 `120px`、纵向 flex 排列卡片 |
| `.layout-column-dropzone.drag-over` | 拖拽悬停时高亮：蓝色边框 + 浅蓝背景 |
| `.layout-card` | 可拖拽卡片项：灰底圆角、`cursor: grab`、`user-select: none` |
| `.layout-card:hover` | 悬停浮起阴影效果 |
| `.layout-card.dragging` | 拖拽中半透明（`opacity: 0.5`） |
| `.layout-card-name` | 卡片名称文字：`0.8rem`，`font-weight: 500` |
| `.layout-card-handle` | 拖拽手柄：⠿ 字符，`color: --carbon-400` |
| `.layout-unused` | 未使用卡片池区域：位于三栏下方 |
| `.layout-unused-header` | 未使用池标题：`0.75rem`，灰色 |
| `.layout-unused .layout-column-dropzone` | 未使用池放置区：横向排列（`flex-direction: row`）、最小高度 `40px` |
| `.layout-editor-footer` | 底部按钮栏：右对齐、顶部分隔线 |
| `.btn-layout-save` | 保存按钮：蓝色填充、占 `80%` 宽度 |
| `.btn-layout-reset` | 重置按钮：灰色描边、占 `20%` 宽度 |
| `.btn-layout-editor` | 设置面板中的入口按钮：蓝色填充、圆角 |

## 响应式规则

### `@media (max-width: 2048px)`

在视口宽度 ≤ 2048px 时触发以下调整：
- `h1` 标题宽度设为 `100%`，防止长标题溢出
- `#theme-toggle` 主题切换按钮改为 `position: static`、`order: 3`，适应窄屏下的控制栏重排

## 暗黑模式适配

采用 `.dark-theme` 类作为根节点标识。在该模式下，系统会自动调整以下属性：
- 背景色与主文字颜色。
- 卡片和设置面板的背景与边框颜色。
- 表单控件（select, button）的背景与边框。
- 部分语义化文字颜色（如 pending 状态的文字色）。
