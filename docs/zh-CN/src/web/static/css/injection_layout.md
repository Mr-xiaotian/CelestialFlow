# injection_layout.css

> 📅 最后更新日期: 2026/06/22

负责任务注入页的搜索筛选、双栏布局以及响应式断点样式。


## 双栏布局 (`.card-grid`)

```css
.card-grid {
  display: grid;
  grid-template-columns: minmax(18rem, 22rem) minmax(0, 1fr);
  gap: 1.5rem;
}
```

- 左侧节点列表固定 18–22rem，右侧编辑器自适应剩余宽度。

## 搜索筛选

- **搜索容器 (`.search-container`)**: 相对定位，用于承载搜索图标。
- **搜索输入框 (`.search-input`)**:
  - 左侧内边距 `2.5rem` 为搜索图标留空间。
  - 聚焦时边框色切换为 `--cornflower-400`。
  - 深色模式：`--carbon-700` 背景。
- **搜索图标 (`.search-icon`)**: 绝对定位在输入框左侧，`1rem`，`color: --carbon-400`。

## 可注入节点开关 (`.injectable-toggle`)

- `flex` 布局，`gap: 0.5rem`，`font-size: 0.75rem`。
- 位于搜索框下方、节点列表上方。

## 响应式 (`@media (max-width: 2048px)`)

在窄屏（≤2048px）下：
- `.card-grid` 切换为单列（`grid-template-columns: 1fr`）。
- `.node-list` 取消 `max-height` 限制。
- `.editor-header` 和 `.submit-section` 切换为纵向堆叠。
- `.editor-actions` 切换为纵向排列。

## 关联模块

- 布局结构由 `injection.ts` 中的 `renderInjectionPage()` 动态填充。
- 搜索和筛选事件由 `setupEventListeners()` 绑定。
