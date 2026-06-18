# index.html

> 📅 最后更新日期: 2026/06/18

Web UI 的 Jinja2 模板文件，定义了监控系统的完整页面结构。

## 整体布局

页面分为三个主要区域：

```
<header>  — 顶部控制栏（设置面板、主题切换）
<main>
  ├─ .tabs           — 标签页导航（仪表盘 / 错误日志 / 任务注入）
  ├─ #dashboard      — 仪表盘（三栏布局）
  ├─ #errors         — 错误日志
  └─ #task-injection  — 任务注入
```

## Header 控制栏

| 元素 | ID / Class | 说明 |
|------|-----------|------|
| 设置按钮 | `#settings-btn` | 点击打开设置面板，带 a11y 属性 |
| 设置面板 | `#settings-panel` | 包含刷新、历史、语言、分页、增量开关等设置 |
| 界面语言 | `#language-select` | 支持中、英、日三语切换 |
| 结构图增量 | `#structure-edge-delta` | 开关，控制 Mermaid 图边上是否显示成功数增量 |
| 主题切换 | `#theme-toggle` | 圆角胶囊按钮，切换明暗模式 |

## Dashboard 三栏结构

### 左栏 `.left-panel`

| 卡片 | Class | 说明 |
|------|-------|------|
| 任务结构图 | `.mermaid-card` | Mermaid 流程图，支持节点着色和边增量 |
| 图分析信息 | `.analysis-card` | 拓扑结构洞察信息 |

### 中栏 `.middle-panel`

| 卡片 | Class | 说明 |
|------|-------|------|
| 节点运行状态 | `.status-card` | 动态节点卡片，含进度条和实时增量统计 |

### 右栏 `.right-panel`

| 卡片 | Class | 说明 |
|------|-------|------|
| 节点指标走向 | `.progress-card` | 支持指标切换（完成/成功/错误/重复/等待）的历史折线图 |
| 总体状态摘要 | `.summary-card` | 全局 6 格统计看板 |

## 外部依赖（CDN）

| 库 | 版本 | 用途 |
|----|------|------|
| Chart.js | latest | 折线图绘制 |
| SortableJS | latest | 节点卡片拖拽排序 |
| Mermaid | `^10` (ESM) | 任务图可视化渲染 |

## JS 脚本加载顺序

脚本按依赖关系顺序加载：

```html
i18n.js               ← 国际化支持
utils.js              ← 通用工具函数
web_config.js         ← 配置管理逻辑
dashboard_statuses.js ← 节点状态管理
dashboard_structure.js← 结构图渲染
errors.js             ← 错误日志分页
dashboard_analysis.js ← 拓扑分析展示
dashboard_summary.js  ← 汇总统计
dashboard_history.js  ← 历史图表
injection.js          ← 任务注入逻辑
main.js               ← 全局入口与轮询协调
layout_editor.js      ← 卡片布局编辑器（依赖 web_config 的 CARD_TEMPLATES、PANEL_SELECTOR_MAP 及 applyDashboardLayout）
```

## CSS 样式引用

```html
css/_colors.css             ← 颜色变量定义
css/base.css                ← 全局基础样式与设置面板
css/dashboard.css           ← 仪表盘布局与 Tab 容器
css/dashboard_structure.css  ← 结构图专属样式
css/dashboard_analysis.css   ← 分析卡片专属样式
css/dashboard_statuses.css   ← 节点卡片专属样式
css/dashboard_summary.css    ← 汇总面板专属样式
css/dashboard_history.css    ← 历史图专属样式
css/errors.css              ← 错误日志页样式
css/injection_layout.css     ← 注入页布局样式
css/injection_nodes.css      ← 注入页节点列表样式
css/injection_editor.css     ← 注入页编辑器样式
css/injection_preview.css    ← 注入页预览样式
```

## 卡片布局编辑器模态窗 (`#layout-editor-overlay`)

悬浮模态窗（默认 `.overlay.hidden` 隐藏），支持拖拽排序三栏仪表盘卡片。

- **遮罩层**: `#layout-editor-overlay` / `.overlay` — 全屏半透明黑色背景，`z-index: 200`
- **编辑器主体**: `#layout-editor` / `.layout-editor` — 圆角卡片容器，`max-width: 700px`
- **三栏放置区**: 左中右三个 drop zone（`#layout-dropzone-left`、`#layout-dropzone-middle`、`#layout-dropzone-right`），基于 SortableJS 实现拖拽
- **未使用池**: `#layout-dropzone-unused` — 横向 drop zone，容纳被移出三栏的卡片
- **底部按钮**: 保存（`#layout-save-btn`）和重置默认（`#layout-reset-btn`）
- 通过设置面板中的 `.btn-layout-editor` 按钮打开；点击 `#layout-editor-close` 或遮罩外部关闭
- 保存时调用 `applyDashboardLayout()` 立即生效，再调用 `saveWebConfig()` 持久化到后端

## 使用示例

### 通过浏览器访问

启动 Web 服务器后，在浏览器地址栏访问：

```
http://127.0.0.1:5000
```

启动命令：

```bash
# 命令行启动（默认 0.0.0.0:5000）
celestialflow-web

# 或在 Python 中启动
python -c "from celestialflow import TaskWebServer; TaskWebServer(host='127.0.0.1', port=5000).start_server()"
```

浏览器打开后可见三个标签页：
- **仪表盘 (Dashboard)**: 实时显示任务图的结构图、节点运行状态、指标走向和总体摘要
- **错误日志 (Errors)**: 分页查看和搜索错误记录
- **任务注入 (Task Injection)**: 向指定节点注入新任务

### 修改模板示例

`index.html` 使用 Jinja2 模板引擎，可以通过自定义模板变量或直接修改 HTML 来自定义界面。

#### 修改页面标题

编辑 `index.html` 找到 `<title>` 标签：

```html
<!-- 原内容 -->
<title>任务图监控系统</title>

<!-- 修改为自定义标题 -->
<title>我的任务监控</title>
```

#### 调整仪表盘布局

模板中硬编码了三栏结构（left-panel / middle-panel / right-panel），可以通过修改对应的卡片容器排序：

```html
<!-- 将结构图和分析信息互换位置 -->
<div class="left-panel">
  <div class="analysis-card"><!-- 分析面板 --></div>
  <div class="mermaid-card"><!-- 结构图 --></div>
</div>
```

#### 通过配置动态控制

运行时的卡片布局实际由 `WebConfig.dashboard` 控制，在 `web_config.ts` 中修改默认值或通过后端 `config.json` 调整：

```json
{
    "dashboard": {
        "left": ["status"],
        "middle": ["mermaid"],
        "right": ["summary", "progress"]
    }
}
```

#### 添加自定义 CSS

将自定义样式文件放入 `web/static/css/` 目录，并在 `index.html` 中引入：

```html
<link rel="stylesheet" href="static/css/custom.css">
```
