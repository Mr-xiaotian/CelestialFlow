# web_config.ts

> 📅 最后更新日期: 2026/05/23

管理 Web 前端的配置加载、归一化、保存和应用。包含主题、语言、轮询频率、历史长度、分页大小及仪表盘布局。

## 类型定义

```ts
type WebConfig = {
    theme: "light" | "dark";         // 界面主题
    refreshInterval: number;          // 全局轮询刷新间隔（毫秒）
    historyLimit: number;             // 前端本地维护的历史记录长度
    language: Lang;                   // 界面语言（zh-CN, en, ja）
    errorPageSize: number;            // 错误日志每页显示条数
    showStructureEdgeDelta: boolean;  // 是否在结构图边上显示成功任务增量
    dashboard: {                      // 仪表盘布局配置
        left: string[];
        middle: string[];
        right: string[];
    };
};
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `webConfig` | `WebConfig \| null` | 当前运行时的配置对象 |
| `DEFAULT_WEB_CONFIG` | `WebConfig` | 默认配置模板，用于初始化和降级兜底 |

## 函数

### `loadWebConfig()`

异步从 `GET /api/pull_config` 加载配置。

- **鲁棒性**: 若请求失败（如后端未响应或网络异常），会捕获异常并自动调用 `normalizeWebConfig()` 使用默认配置启动，确保页面基本可用。

---

### `saveWebConfig()`

将当前 `webConfig` 对象 POST 到 `/api/push_config`。后端会将其持久化到 `web/config.json`。

---

### `normalizeWebConfig(rawConfig?)`

将后端返回的原始配置（可能缺失字段）与 `DEFAULT_WEB_CONFIG` 合并。

- 确保 `dashboard` 结构的完整性。
- 提供深层合并逻辑。

---

### `applyConfig()`

将 `webConfig` 中的各项设置同步到页面：

1. **语言**: 应用 `language` 并更新全页 `data-i18n` 元素。
2. **主题**: 切换 `dark-theme` 类。
3. **参数同步**: 将刷新率、历史长度、每页条数、增量开关同步到对应的 DOM 控件（如 Select/Checkbox）。
4. **布局**: 调用 `applyDashboardLayout()` 重排卡片。

---

### `applyDashboardLayout()`

核心布局逻辑：通过 DOM 操作（`appendChild`）实现卡片在三栏面板间的动态移动。

- **动态显隐**: 仅配置中存在的卡片才会设为 `display: block`。
- **顺序控制**: 严格遵循配置数组中的顺序进行插入。

## 默认配置参考

```json
{
    "theme": "light",
    "refreshInterval": 5000,
    "historyLimit": 20,
    "language": "zh-CN",
    "errorPageSize": 50,
    "showStructureEdgeDelta": false,
    "dashboard": {
        "left": ["mermaid", "analysis"],
        "middle": ["status"],
        "right": ["progress", "summary"]
    }
}
```
