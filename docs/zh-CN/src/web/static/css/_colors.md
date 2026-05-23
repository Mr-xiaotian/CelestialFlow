# _colors.css

> 📅 最后更新日期: 2026/05/23

定义了 Web UI 使用的全局色彩系统变量，基于 CSS Variables (`:root`) 实现，方便统一管理和主题切换。

## 色彩体系

项目采用多色阶设计，每个色系包含从 50 到 900 的多个色阶。

### 核心色系

- **霜白 (Frost)**: `--frost-0` (#ffffff)。用于背景和纯白元素。
- **碳黑 (Carbon)**: `--carbon-50` ~ `--carbon-900`。用于文字、边框、阴影和暗色模式背景。
- **翡翠绿 (Jade)**: `--jade-50` ~ `--jade-900`。用于成功状态、进度条和正面反馈。
- **深红 (Crimson)**: `--crimson-50` ~ `--crimson-900`。用于错误状态、异常报警和负面反馈。
- **金盏菊黄 (Marigold)**: `--marigold-50` ~ `--marigold-900`。用于重复任务、警告和中性状态。
- **矢车菊蓝 (Cornflower)**: `--cornflower-50` ~ `--cornflower-900`。用于运行中状态、链接和主要动作按钮。

### 辅助色系

- **琥珀橙 (Amber)**: `--amber-50` ~ `--amber-900`。
- **玫瑰红 (Rose)**: `--rose-50` ~ `--rose-900`。
- **紫罗兰 (Violet)**: `--violet-50` ~ `--violet-900`。
- **天蓝 (Sky)**: `--sky-50` ~ `--sky-900`。

## 使用方式

在其他 CSS 文件中通过 `var()` 函数引用：

```css
.example {
  color: var(--carbon-900);
  background-color: var(--jade-50);
  border: 1px solid var(--cornflower-500);
}
```

## 设计规范

- **文字颜色**: 默认使用 `--carbon-900` (浅色模式) 或 `--carbon-200` (深色模式)。
- **边框颜色**: 常用 `--carbon-200` 或 `--carbon-300`。
- **状态色**:
  - 成功: `Jade`
  - 错误: `Crimson`
  - 重复: `Marigold`
  - 运行: `Cornflower`
  - 等待/停止: `Carbon`
