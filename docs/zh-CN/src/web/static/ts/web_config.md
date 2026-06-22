# web_config.ts

> 📅 最后更新日期: 2026/06/22

管理 Web 前端的配置加载、归一化、保存和应用。配置采用**分组结构**（`global`、`dashboard`、`errors`、`injection`），同时兼容旧版扁平格式的自动迁移。

> ⚠️ **已变更**: 配置结构已从旧版扁平 `WebConfig` 重构为分组格式。新增 `LegacyWebConfig` 兼容类型、`isGroupedWebConfig()` 检测函数和 `normalizeDashboardLayout()` 布局归一化函数。

## 类型定义

### 当前分组配置

```typescript
type WebGlobalConfig = {
  theme: "light" | "dark";
  autoRefreshEnabled: boolean;
  refreshInterval: number;
  language: Lang;
};

type WebDashboardConfig = {
  historyLimit: number;
  showStructureEdgeDelta: boolean;
  useTotalPendingInStatus: boolean;
  layout: DashboardLayout;
};

type WebErrorsConfig = {
  pageSize: number;
  sortOrder: "newest" | "oldest";
  jumpToInjectionAfterRetry: boolean;
};

type WebInjectionConfig = {
  showInjectableOnly: boolean;
};

type WebConfig = {
  global: WebGlobalConfig;
  dashboard: WebDashboardConfig;
  errors: WebErrorsConfig;
  injection: WebInjectionConfig;
};
```

### 旧版兼容类型

```typescript
type LegacyWebConfig = {
  theme?: "light" | "dark";
  autoRefreshEnabled?: boolean;
  refreshInterval?: number;
  language?: Lang;
  historyLimit?: number;
  showStructureEdgeDelta?: boolean;
  useTotalPendingInStatus?: boolean;
  errorPageSize?: number;
  errorSortOrder?: "newest" | "oldest";
  dashboard?: Partial<DashboardLayout>;
};
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `webConfig` | `WebConfig` | 当前运行时的配置对象，模块加载时由 `DEFAULT_WEB_CONFIG` 初始化 |
| `saveConfigPending` | `boolean` | 是否还有新的配置变更等待落盘 |
| `saveConfigPromise` | `Promise<boolean> \| null` | 当前正在执行的保存队列 Promise |
| `PANEL_SELECTOR_MAP` | `Record<DashboardColumnKey, string>` | 面板键到 CSS 选择器的映射 |
| `CARD_TEMPLATES` | `Record<string, string>` | 卡片 ID 到 HTML 模板的映射（mermaid, analysis, status, progress, summary） |
| `CARD_META` | `Record<string, string>` | 卡片 ID 到 i18n 标签键的映射 |
| `ALL_CARD_IDS` | `string[]` | 由 `Object.keys(CARD_TEMPLATES)` 自动生成的标准卡片 ID 列表 |
| `DEFAULT_WEB_CONFIG` | `WebConfig` | 默认配置模板，用于初始化和降级兜底 |

## 函数

### `loadWebConfig(): Promise<void>`

异步从 `GET /api/pull_config` 加载配置。失败时自动回退到默认配置。

---

### `saveWebConfig(): Promise<boolean>`

将当前 `webConfig` 通过 `POST /api/push_config` 持久化。带**防并发**机制：若已有保存进行中，复用同一个 Promise。

---

### `performSaveWebConfig(): Promise<boolean>`

执行实际的 POST 请求，将当前 `webConfig` 快照推送到后端。并发控制由 `saveWebConfig()` 负责。

---

### `isGroupedWebConfig(config: unknown): boolean`

检测配置对象是否为新的分组格式（源码中通过判断是否存在 `global`、`errors` 或 `injection` 子对象来识别）。

---

### `normalizeWebConfig(rawConfig?: Partial<WebConfig> | LegacyWebConfig | null): WebConfig`

将后端返回的原始配置（可能为旧版扁平格式或缺失字段）与 `DEFAULT_WEB_CONFIG` 深层合并。

- 自动检测并迁移旧版扁平配置（`LegacyWebConfig`）到新分组格式。
- 确保 `dashboard.layout` 的完整性。

---

### `normalizeDashboardLayout(layout?: Partial<DashboardLayout>): DashboardLayout`

确保仪表盘布局包含所有三栏键（`left`、`middle`、`right`），缺失时用空数组填充。

---

### `applyConfig(): void`

将 `webConfig` 中的各项设置同步到页面：

1. **语言**: 应用 `global.language` 并更新全页 `data-i18n` 元素。
2. **主题**: 根据 `global.theme` 切换 `dark-theme` 类。
3. **参数同步**: 将刷新率、历史长度、每页条数、增量开关等同步到对应的 DOM 控件。
4. **布局**: 调用 `applyDashboardLayout()` 重排卡片。

---

### `ensureAllCards(): void`

模块加载时立即执行，遍历 `CARD_TEMPLATES` 将所有卡片 DOM 节点创建并注入 `#card-pool` 容器。会检查是否已存在对应类名元素以避免重复创建。

---

### `applyDashboardLayout(): void`

核心布局逻辑：通过 DOM 操作（`appendChild`）实现卡片在三栏面板间的动态移动。严格遵循配置数组中的顺序。

## 默认配置参考

```typescript
const DEFAULT_WEB_CONFIG: WebConfig = {
  global: {
    theme: "light",
    autoRefreshEnabled: true,
    refreshInterval: 5000,
    language: "zh-CN",
  },
  dashboard: {
    historyLimit: 20,
    showStructureEdgeDelta: false,
    useTotalPendingInStatus: false,
    layout: {
      left: ["mermaid", "analysis"],
      middle: ["status"],
      right: ["progress", "summary"],
    },
  },
  errors: {
    pageSize: 50,
    sortOrder: "newest",
    jumpToInjectionAfterRetry: true,
  },
  injection: {
    showInjectableOnly: true,
  },
};
```

## 使用示例

```typescript
// 读取当前配置
console.log("主题:", webConfig.global.theme);
console.log("刷新间隔:", webConfig.global.refreshInterval);
console.log("历史长度:", webConfig.dashboard.historyLimit);
console.log("错误每页:", webConfig.errors.pageSize);
console.log("注入页仅显示可注入:", webConfig.injection.showInjectableOnly);

// 修改配置并保存
webConfig.global.theme = "dark";
webConfig.dashboard.historyLimit = 50;
applyConfig();  // 立即应用到页面
const saved = await saveWebConfig();  // 持久化到后端

// 旧版扁平配置自动迁移
const legacy = { theme: "dark", refreshInterval: 3000, historyLimit: 10 };
const normalized = normalizeWebConfig(legacy);
// 自动迁移为 { global: { theme: "dark", ... }, dashboard: { historyLimit: 10, ... }, ... }
```
