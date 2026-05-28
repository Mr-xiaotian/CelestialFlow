# web_config.ts

> 📅 最后更新日期: 2026/05/28

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
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | 将 `left` / `middle` / `right` 面板键映射为 CSS 选择器（`.left-panel`、`.middle-panel`、`.right-panel`） |
| `CARD_TEMPLATES` | `Record<string, string>` | 以卡片 ID（mermaid, analysis, status, progress, summary）为键的 HTML 模板字符串 |
| `CARD_META` | `Record<string, string>` | 卡片 ID 到 i18n 标签键的映射（如 `mermaid` → `card.mermaid.title`） |
| `ALL_CARD_IDS` | `string[]` | 由 `Object.keys(CARD_TEMPLATES)` 自动生成，作为标准卡片 ID 列表供布局编辑器使用 |

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

### `ensureAllCards()`

模块加载时立即执行，遍历 `CARD_TEMPLATES` 将所有卡片 DOM 节点创建并注入 `#card-pool` 容器中。

- 会检查是否已存在 `.{key}-card` 类名元素以避免重复创建
- 模块级顶层执行（非函数内部），确保后续脚本在任何布局操作前都能通过 ID 找到元素

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

## 使用示例

### 配置对象的结构和读取示例

以下示例展示 `WebConfig` 配置对象的完整结构以及在浏览器控制台中如何读取和修改：

```typescript
// 1. WebConfig 的完整结构
// 参照默认配置，一个完整的配置对象包含：
const fullConfig: WebConfig = {
    theme: "light",
    refreshInterval: 5000,
    historyLimit: 20,
    language: "zh-CN",
    errorPageSize: 50,
    showStructureEdgeDelta: false,
    dashboard: {
        left: ["mermaid", "analysis"],
        middle: ["status"],
        right: ["progress", "summary"],
    },
};

// 2. 读取当前配置（在浏览器控制台中）
// 全局变量 webConfig 保存了当前运行时的配置
console.log("当前配置:", webConfig);
console.log("主题:", webConfig.theme);                   // "light" | "dark"
console.log("刷新间隔:", webConfig.refreshInterval, "ms"); // 5000
console.log("历史长度:", webConfig.historyLimit);          // 20
console.log("语言:", webConfig.language);                // "zh-CN"
console.log("错误每页条数:", webConfig.errorPageSize);     // 50
console.log("结构图增量:", webConfig.showStructureEdgeDelta); // false
console.log("仪表盘布局:", webConfig.dashboard);
// { left: [...], middle: [...], right: [...] }

// 3. 使用 normalizeWebConfig 合并配置
// 当后端返回的配置可能缺失某些字段时，用默认值补齐：
const partialConfig = {
    theme: "dark",
    refreshInterval: 3000,
};
const normalized = normalizeWebConfig(partialConfig);
console.log("归一化后:", normalized);
// {
//   theme: "dark",
//   refreshInterval: 3000,
//   historyLimit: 20,           // 默认值
//   language: "zh-CN",          // 默认值
//   errorPageSize: 50,          // 默认值
//   showStructureEdgeDelta: false, // 默认值
//   dashboard: { left: [...], middle: [...], right: [...] } // 默认布局
// }

// 4. 手动修改配置并保存
async function updateConfig() {
    // 修改配置
    webConfig.theme = "dark";
    webConfig.refreshInterval = 2000;
    webConfig.language = "en";

    // 应用配置到页面
    applyConfig();

    // 保存到后端
    const saved = await saveWebConfig();
    console.log(saved ? "配置保存成功" : "配置保存失败");
}

// 5. 动态调整仪表盘布局
function rearrangeDashboard() {
    // 将状态卡片移到左栏，结构图移到中栏
    webConfig.dashboard = {
        left: ["status"],
        middle: ["mermaid"],
        right: ["analysis", "progress", "summary"],
    };
    applyDashboardLayout();
    saveWebConfig();
}

// 6. 使用默认配置兜底启动
// 当 loadWebConfig() 失败时（如后端未响应），自动回退到默认配置：
// webConfig = normalizeWebConfig();
// 这保证了页面在任何情况下都能正常渲染
```
