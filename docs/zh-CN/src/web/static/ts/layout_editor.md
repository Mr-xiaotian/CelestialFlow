# 卡片布局编辑器 — `layout_editor`

> 📅 最后更新日期: 2026/05/28

## 作用

`layout_editor.ts` 是仪表盘**卡片布局编辑器**的前端模块。它在一个悬浮窗口（overlay）中提供拖拽式界面，让用户可以自由调整仪表盘左、中、右三栏各自包含哪些卡片，并将结果持久化到 `config.json`。

编辑器使用 [SortableJS](https://sortablejs.github.io/Sortable/) 实现跨区域的拖拽排序，支持在三栏和"未使用卡片池"之间相互拖移。

---

## 核心常量

### `DEFAULT_LAYOUT`

默认的三栏卡片布局配置，定义了系统出厂时的卡片分配方案：

```javascript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis"],
  middle: ["status"],
  right:  ["progress", "summary"],
};
```

| 栏位 | 默认卡片 | 说明 |
|------|----------|------|
| `left` | mermaid, analysis | 图渲染 + 拓扑分析 |
| `middle` | status | 节点状态表格 |
| `right` | progress, summary | 进度 + 全局汇总 |

---

## 核心函数

### `renderCard(cardId: string): HTMLElement`

创建一张可拖拽的卡片 DOM 元素。

| 参数 | 类型 | 说明 |
|------|------|------|
| `cardId` | `string` | 卡片标识符（如 `"mermaid"`、`"status"`） |

**返回：** 一个带有 `.layout-card` CSS 类、存储了 `data-card-id` 属性和拖拽手柄的 `<div>` 元素。

```html
<div class="layout-card" data-card-id="mermaid">
  <span class="layout-card-name">图渲染</span>
  <span class="layout-card-handle" aria-hidden="true">⠿</span>
</div>
```

卡片名称通过 `CARD_META[cardId]` 查找本地化显示名，找不到时回退到原始 `cardId`。

---

### `openLayoutEditor()`

打开布局编辑器并渲染当前布局。

**流程：**

```
┌──────────────────────────────────┐
│  1. 显示 overlay                 │
│  2. 读取 webConfig.dashboard     │
│     （不存在则用 DEFAULT_LAYOUT）│
│  3. 保存一份副本到 originalLayout│
│  4. 渲染左/中/右三栏             │
│  5. 渲染未使用卡片池             │
│  6. 调用 initSortable() 启用拖拽│
└──────────────────────────────────┘
```

未使用卡片池包含 `ALL_CARD_IDS` 中未被三栏引用的所有卡片。

---

### `closeLayoutEditor(restore: boolean = true)`

关闭布局编辑器。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `restore` | `boolean` | `true` | 是否恢复原始布局。`true` 时撤销所有未保存的拖拽修改；`false` 时保留当前内存状态 |

**行为：**
- `restore=true`（默认）：用 `originalLayout` 覆盖 `webConfig.dashboard`，并调用 `applyConfig()` 刷新仪表盘。这是点击关闭按钮或点击遮罩时的行为。
- `restore=false`：隐藏 overlay 但不恢复数据。这是保存成功后调用的行为。

---

### `initSortable()`

初始化 SortableJS，在四个放置区域启用跨区域拖拽。

**涉及的区域：**

| ID | 说明 |
|----|------|
| `layout-dropzone-left` | 左栏放置区 |
| `layout-dropzone-middle` | 中栏放置区 |
| `layout-dropzone-right` | 右栏放置区 |
| `layout-dropzone-unused` | 未使用卡片池 |

**SortableJS 配置：**

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `group` | `"dashboard-layout"` | 共享组名，四个区域可互拖 |
| `animation` | `150` | 拖拽动画时长（ms） |
| `ghostClass` | `"dragging"` | 拖拽时的占位 CSS 类 |
| `dragClass` | `"dragging"` | 拖拽时卡片本身的 CSS 类 |

---

### `syncLayout()`

将 DOM 中当前的三栏卡片顺序同步回 `webConfig.dashboard`。

**流程：**
1. 遍历 `left`、`middle`、`right` 三个放置区
2. 从每个区域的 `.layout-card` 元素读取 `data-card-id`
3. 按顺序数组写入 `webConfig.dashboard`

> 此函数**不持久化**，仅更新内存结构。持久化由 `saveLayout()` 调用。

---

### `saveLayout()`

保存布局并刷新仪表盘。

**流程：**

```
┌───────────────────────────────────┐
│  1. syncLayout()                  │
│  2. await saveWebConfig()         │
│     ├─ 成功 → applyConfig()       │
│     │         closeLayoutEditor(false)
│     └─ 失败 → 显示保存失败提示    │
└───────────────────────────────────┘
```

`saveWebConfig()` 将 `webConfig` 通过 `POST /api/push_config` 持久化到 `config.json`。

---

### `resetLayout()`

将布局重置为 `DEFAULT_LAYOUT`。

**流程：**

1. 将 `webConfig.dashboard` 重置为 `DEFAULT_LAYOUT` 的深拷贝
2. 清空并重新渲染左中右三栏（按默认卡片顺序）
3. 清空并重新计算未使用卡片池
4. 重新调用 `initSortable()` 绑定拖拽

> 此操作**不自动保存**，用户仍需点击保存按钮才会持久化。

---

## 事件绑定

模块在 `DOMContentLoaded` 时绑定以下事件：

| 目标元素 | 事件 | 处理函数 |
|----------|------|----------|
| `#open-layout-editor` | `click` | `openLayoutEditor()` |
| `#layout-editor-close` | `click` | `closeLayoutEditor()`（恢复） |
| `#layout-editor-overlay` | `click` | 点击遮罩外层时 `closeLayoutEditor()`（恢复） |
| `#layout-save-btn` | `click` | `saveLayout()` |
| `#layout-reset-btn` | `click` | `resetLayout()` |

---

## 使用示例

### HTML 结构

布局编辑器依赖以下 DOM 结构：

```html
<!-- 触发按钮 -->
<button id="open-layout-editor">编辑布局</button>

<!-- 遮罩层 -->
<div id="layout-editor-overlay" class="hidden">
  <div class="layout-editor-panel">
    <h2>卡片布局</h2>

    <!-- 三栏放置区 -->
    <div id="layout-dropzone-left"></div>
    <div id="layout-dropzone-middle"></div>
    <div id="layout-dropzone-right"></div>

    <!-- 未使用卡片池 -->
    <div id="layout-dropzone-unused"></div>

    <!-- 操作按钮 -->
    <button id="layout-save-btn">保存</button>
    <button id="layout-reset-btn">重置</button>
    <button id="layout-editor-close">关闭</button>
  </div>
</div>
```

### 自定义默认布局

修改 `DEFAULT_LAYOUT` 常量即可改变出厂布局：

```typescript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis", "custom-card"],
  middle: ["status", "errors"],
  right:  ["progress"],
};
```
