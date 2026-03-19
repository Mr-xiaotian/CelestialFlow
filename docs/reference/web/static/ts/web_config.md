# web_config.ts

管理 Web 前端的配置加载、保存和应用，包括主题、刷新间隔和仪表盘布局。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `webConfig` | `any` | 当前配置对象，从后端加载 |
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | 三栏面板的 CSS 选择器映射 |

## 函数

### `loadWebConfig()`

异步从 `GET /api/pull_config` 加载配置，赋值给 `webConfig`。

- 成功返回 `true`，失败返回 `false`
- 失败时在控制台打印警告，不抛出异常

---

### `saveWebConfig()`

异步将当前 `webConfig` POST 到 `/api/push_config` 保存至后端。

- 成功返回 `true`，失败返回 `false`

---

### `applyConfig()`

将 `webConfig` 中的设置应用到 UI：

1. **主题**: 根据 `webConfig.theme` 切换 `dark-theme` CSS 类和按钮文字
2. **刷新间隔**: 更新 `refreshRate` 和下拉框选中值（含边界保护）
3. **隐藏节点**: 同步 `hiddenNodes` Set 及 localStorage
4. **仪表盘布局**: 调用 `applyDashboardLayout()`

---

### `applyDashboardLayout()`

根据 `webConfig.dashboard` 和 `webConfig.cards` 配置动态排列仪表盘中的各卡片。

**流程：**

1. 收集所有已知卡片 key（配置中 + DOM 中存在的），定位对应 `.{key}-card` DOM 元素
2. 先隐藏所有已知卡片
3. 按 `left` / `middle` / `right` 顺序，将卡片 `appendChild` 到对应栏位，设为可见，并更新标题
4. 兜底隐藏未被任何栏位接收的卡片

> 通过 `appendChild` 实现移动，支持任意栏位 + 任意顺序组合配置。

## 配置结构

```json
{
    "theme": "light",
    "refreshInterval": 5000,
    "dashboard": {
        "left": ["mermaid", "topology"],
        "middle": ["status"],
        "right": ["progress", "summary"]
    },
    "hiddenNodes": [],
    "cards": {
        "mermaid": { "title": "任务结构图" },
        "topology": { "title": "图拓扑信息" },
        "status": { "title": "节点运行状态" },
        "progress": { "title": "节点完成走向" },
        "summary": { "title": "总体状态摘要" }
    }
}
```

配置持久化在后端 `web/config.json`，前端修改后通过 `saveWebConfig()` 同步。
