# utils.ts

> 📅 最后更新日期: 2026/05/23

包含 Web 前端通用的格式化工具、UI 辅助逻辑、DOM 操作封装及环境检测函数。

## 数值与时间格式化

### `formatLargeNumber(n)`
将大数转换为易读格式。
- `< 10,000,000`: 使用千分位逗号分隔。
- `>= 10,000,000`: 转换为 HTML 科学计数法（如 `~1.23×10⁹`）。

### `formatWithDelta(value, delta, ...)`
格式化带有增量的数值。若增量非零，则在主数值后追加带颜色的 `+N` 或 `-N` 小字。

### `formatDuration(seconds)`
将秒数格式化为 `HH:MM:SS` 或 `MM:SS` 字符串。

### `renderLocalTime(timestamp)`
将 Unix 时间戳转换为本地化日期时间字符串。

---

## UI 与 路由辅助

### `switchToErrorsTab(nodeFilter?)`
全局路由跳转函数。
- 切换当前 Tab 至“错误日志”。
- 若传入 `nodeFilter`，则自动填充错误筛选下拉框并触发一次查询。

### `toggleDarkTheme()`
在 `body` 元素上切换 `dark-theme` 类，返回切换后的布尔状态。

### `showSettingsSaveStatus(messageKey)`
在设置面板底部显示限时的状态提示（如“保存成功”），支持国际化 key 映射。

---

## 历史数据处理

### `extractProgressData(nodeHistories, metric)`
将本地维护的 `nodeHistories` 映射转换为 Chart.js 兼容的 `{x, y}` 坐标点数组。
- `metric` 参数决定了提取哪个指标（如 `tasks_succeeded`, `tasks_failed` 等）。

---

## 安全与工具

### `escapeHtml(str)`
基础的 HTML 转义函数，防止动态插入文本时的 XSS 风险。

### `isMobile()`
基于 UserAgent 的简单移动端检测，用于禁用拖拽排序等交互。
