# index.html

> 📅 最后更新日期: 2026/05/23

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
css/injection.css           ← 任务注入页样式
```
