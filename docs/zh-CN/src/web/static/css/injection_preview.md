# injection_preview.css

> 📅 最后更新日期: 2026/06/22

负责任务注入页底部草稿预览区、提交按钮、状态消息和加载动画的样式定义。


## 草稿预览卡片 (`.draft-card`)

- 纵向 flex 布局，`gap: 0.75rem`，`margin-bottom: 1rem`。
- 作为所有已编辑草稿的汇总展示区域。

## 草稿预览区 (`.draft-preview`)

- **只读样式**: `margin: 0`，`padding: 1rem`，无输入状态。
- **等宽字体**: `Monaco, Menlo, monospace`，`font-size: 0.75rem`。
- **背景**: 浅色模式 `--carbon-50`，深色模式 `--carbon-800`。
- **溢出**: `overflow: auto`，支持长内容滚动。
- **最小高度**: `min-height: 12rem`。

## 空态占位 (`.empty-placeholder`)

- 当无草稿时显示，等宽字体样式。

## 提交区块 (`.submit-section`)

- `flex` 布局，左右分布（状态提示 + 提交按钮），`gap: 1rem`，`margin-top: auto`。

## 状态消息 (`.status-message`)

- `flex` 布局，`align-items: center`，`font-weight: 500`。

| CSS 类 | 说明 | 颜色 |
|--------|------|------|
| `.status-success` | 提交成功 | `--jade-600`（浅）/ `--jade-400`（深） |
| `.status-error` | 提交失败 | `--crimson-600`（浅）/ `--crimson-400`（深） |

- **状态图标 (`.status-icon`)**: `1.25rem`，右边距 `0.5rem`，为 SVG 内联图标预留。

## 提交按钮 (`.btn-submit`)

- **基础样式**: 蓝色填充（`--cornflower-500`），白色文字，圆角 `0.5rem`，带阴影。
- **悬停效果**: 背景加深（`--cornflower-600`），轻微上移 `-1px`。
- **禁用态**: `--carbon-400` 背景，`cursor: not-allowed`，无阴影无位移。
- **深色模式**: 背景 `--cornflower-600`，禁用态 `--carbon-500`。

## 加载指示器 (`.spinner`)

```css
.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--frost-0);
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: injection-spin 1s linear infinite;
}
```

- 提交中动态插入到提交按钮内部，白色圆环 + 透明顶部的旋转效果。

## 旋转动画 (`@keyframes injection-spin`)

```css
@keyframes injection-spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

## 关联模块

- 草稿预览由 `injection.ts` 中的 `renderDraftList()` 动态渲染。
- 提交交互由 `handleSubmit()` 驱动（按钮加载态切换、状态消息显示）。
- 提交按钮可用性由 `updateSubmitButtonAvailability()` 控制。
