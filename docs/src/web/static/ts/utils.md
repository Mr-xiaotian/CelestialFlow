# utils.ts

通用工具函数集合，供所有其他前端模块共享使用。

## 函数列表

### `renderLocalTime(timestamp)`

将 Unix 时间戳（秒）转换为本地时间字符串。

```ts
renderLocalTime(1700000000) // → "2023/11/15 上午10:13:20"（依本地区域而定）
```

---

### `formatLargeNumber(n)`

将大数格式化为模糊科学计数法 HTML；小于 10000 的数直接返回字符串。

```ts
formatLargeNumber(1234567890) // → "~1.23×10<sup>9</sup>"
formatLargeNumber(999)        // → "999"
```

---

### `formatWithDelta(value, delta, deltaClass, negClass)`

格式化数值及其增量，增量以彩色小字显示。

- `deltaClass`: 正增量的 CSS 类名
- `negClass`: 负增量的 CSS 类名

```ts
formatWithDelta(100, 5, "text-delta-success", "text-delta-success")
// → '100<small class="text-delta-success" style="margin-left: 4px;">+5</small>'
formatWithDelta(100, 0, ...)   // → '100'
```

返回 HTML 字符串，直接插入 `innerHTML`。

---

### `getColor(index)`

按索引循环返回预定义的 9 种十六进制颜色，用于折线图各节点线条着色。

```ts
getColor(0) // → "#3b82f6"（蓝）
getColor(9) // → "#3b82f6"（循环）
```

---

### `extractProgressData(nodeHistories)`

从节点历史数据中提取图表用的 `{x, y}` 点序列。

- **输入**: `Record<string, NodeHistory>` — 节点名 → 历史记录数组
- **输出**: `Record<string, Array<{x: number, y: number}>>` — 节点名 → 坐标点数组
  - `x`: Unix 时间戳（秒）
  - `y`: 该时刻已处理任务数

---

### `isMobile()`

检测当前设备是否为移动端（基于 User-Agent）。返回 `boolean`。用于在移动端禁用拖拽排序功能。

---

### `validateJSON(text)`

验证字符串是否为合法 JSON。

- 空字符串视为合法（返回 `true`，隐藏错误提示）
- 解析失败时调用 `showError("json-error", ...)` 显示提示，返回 `false`

---

### `escapeHtml(str)`

转义 HTML 特殊字符（`&`, `<`, `>`, `"`），防止 XSS。

```ts
escapeHtml('<script>') // → "&lt;script&gt;"
```

---

### `toggleDarkTheme()`

切换 `document.body` 的 `dark-theme` CSS 类。返回切换后是否为暗色模式（`boolean`）。

---

### `switchToErrorsTab(nodeFilter?)`

切换到「错误日志」标签页，并可选地将节点筛选器设置为指定节点。不传或传空字符串则显示全部错误。

---

### `formatDuration(seconds)`

将秒数格式化为 `HH:MM:SS` 或 `MM:SS` 字符串。

```ts
formatDuration(90)    // → "01:30"
formatDuration(3661)  // → "01:01:01"
formatDuration(-5)    // → "00:00"
```

---

### `formatTimestamp(timestamp)`

将 Unix 时间戳（秒）格式化为 `YYYY-MM-DD HH:MM:SS` 字符串。

```ts
formatTimestamp(1700000000) // → "2023-11-15 10:13:20"
```

