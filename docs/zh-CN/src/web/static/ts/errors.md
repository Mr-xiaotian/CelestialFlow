# errors.ts

> 📅 最后更新日期: 2026/06/18

管理错误日志的分页拉取、关键词搜索、节点过滤、排序切换、表格渲染以及任务重注入功能。

> ⚠️ **已变更**: 错误记录字段已重构（`event_id` 为数字、新增 `error_type`/`error_message`/`task_json`/`result_json`）。新增排序切换、重注入（retry）交互列。

## 类型定义

```typescript
type ErrorData = {
  ts: number;      // 错误发生的时间戳，单位为秒
  stage: string;         // 错误发生的节点/阶段名称，用于节点筛选
  event_id: number;      // 失败事件的唯一标识 ID，全局唯一
  error_type: string;    // 错误的分类类型，用于区分不同类别的错误
  error_message: string; // 错误的具体描述信息，是错误的详细文本内容
  task_json: unknown;    // 触发该错误的任务数据，同时用于展示与重试回填
  result_json: unknown;  // 成功结果或失败时的占位结果
};
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `errors` | `ErrorData[]` | 当前页的错误记录列表 |
| `currentPage` | `number` | 当前显示的页码，从 1 开始 |
| `pageSize` | `number` | 每页显示的记录数，由 `webConfig` 同步 |
| `errorSortOrder` | `"newest" \| "oldest"` | 错误日志排序方向，默认 `"newest"` |
| `totalPages` | `number` | 后端计算的总页数 |
| `errorsRev` | `number` | 数据版本号，初始化 `-1`，用于增量拉取 |
| `lastQueryKey` | `string` | 上次查询的缓存键，用于判断筛选条件是否变化 |
| `errorsRequestSeq` | `number` | 请求序列号，防止旧请求覆盖新结果 |

## DOM 元素引用

| 变量 | DOM 选择器 | 说明 |
|------|-----------|------|
| `searchInput` | `#error-search` | 搜索关键词输入框 |
| `nodeFilter` | `#node-filter` | 节点筛选下拉框 |
| `errorSortSelect` | `#error-sort-order` | 排序方式下拉框 |
| `errorsTableBody` | `#errors-table tbody` | 错误表格 tbody |
| `paginationContainer` | `#pager-container` | 分页控件容器 |

## 函数

### `buildErrorsQueryKey(page, pageSizeValue, node, keyword, sortOrder): string`

构建错误查询的缓存键字符串。参数含 `sortOrder`（新旧），与 `lastQueryKey` 配合判断筛选条件是否变化。

---

### `loadErrors(forceReload?: boolean): Promise<boolean>`

异步拉取错误日志数据。

- **查询参数**: `known_rev`, `page`, `page_size`, `node`, `keyword`, `sort_order`
- **竞态保护**: 使用 `errorsRequestSeq` 确保旧请求的结果不会覆盖新请求。
- **强制重载**: `forceReload=true` 或筛选条件变化时忽略 `known_rev` 增量机制。
- **API 端点**: `GET /api/pull_errors?{params}`

---

### `renderErrors(): void`

将 `errors` 数据渲染到 `#errors-table` 表格。

**表格列（共 7 列）：**

| # | 列名 (i18n key) | 说明 |
|---|----------------|------|
| 1 | `#` | 全局展示序号（基于页码计算） |
| 2 | `errors.colId` | 事件 ID（`event_id`） |
| 3 | `errors.colMessage` | 错误信息（`error_type(error_message)`，截断 `format_repr` 50 字符，悬停显示完整） |
| 4 | `errors.colNode` | 节点名称（`stage`） |
| 5 | `errors.colTask` | 任务数据（`task_json` 截断显示） |
| 6 | `errors.colTime` | 发生时间（`ts`，`formatTimestamp` 格式化） |
| 7 | `errors.colRetry` | 重注入操作：当 `task_json` 存在且非占位符时为 `.retry-link`（可重试），否则 `.retry-disabled`（不可用） |

> 第 7 列（重注入）：当 `task_json` 存在且非占位符时，点击/键盘触发调用 `preloadInjectionDraftFromError(stage, task_json, jumpToInjectionAfterRetry)`，可跳转至注入页预填任务数据。

---

### `goToErrorsPage(nextPage: number): Promise<void>`

分页跳转逻辑，将页码限制在 `[1, totalPages]` 范围内后触发 `loadErrors(true)` 重新拉取。

---

### `buildPageList(current: number, total: number): Array<number | string>`

生成分页页码列表，包含首尾页、当前页及前后 2 页，自动插入省略号 `"…"`。

---

### `renderPaginationControls(totalPages: number): void`

渲染分页控件（上一页/下一页按钮 + 数字页码序列）。总页数 ≤ 1 时不渲染。

---

### `populateNodeFilter(statuses: Record<string, NodeStatus>): void`

根据仪表盘的节点状态，动态更新错误页的"按节点筛选"下拉框。尽量保留用户当前筛选条件。

---

## 事件绑定（模块级自动执行）

| 目标元素 | 事件 | 行为 |
|----------|------|------|
| `searchInput` | `input` | 重置到第 1 页，强制重载，渲染表格 |
| `nodeFilter` | `change` | 重置到第 1 页，强制重载，渲染表格 |
| `errorSortSelect` | `change` | 更新 `errorSortOrder` 和 `webConfig`，重置到第 1 页，重载并保存配置 |

## 使用示例

```typescript
// 模拟错误记录
const mockErrors: ErrorData[] = [
  { ts: 1745400100, stage: "StageA", event_id: 1001, error_type: "TimeoutError", error_message: "Connection timeout", task_json: { id: 1 }, result_json: null },
  { ts: 1745400050, stage: "StageB", event_id: 1002, error_type: "ValueError", error_message: "Invalid value", task_json: "task_data", result_json: null },
];

// errors = mockErrors;
// currentPage = 1;
// totalPages = 5;
// renderErrors();        // 渲染表格
// renderPaginationControls(5); // 渲染分页

// 跳转到第 3 页
// await goToErrorsPage(3);

// 从其他标签页跳转到错误日志并自动过滤
// switchToErrorsTab("StageA");
```

## 数据流

```mermaid
flowchart LR
    subgraph "main.ts"
        RA[refreshAll]
    end
    subgraph "errors.ts"
        LE[loadErrors]
        QK[buildErrorsQueryKey]
        RE[renderErrors]
        RP[renderPaginationControls]
    end
    subgraph "API"
        API[/api/pull_errors]
    end
    subgraph "DOM"
        TB[#errors-table]
        PG[#pager-container]
    end

    RA --> LE
    LE --> QK
    LE --> API
    API --> LE
    LE --> RE
    RE --> TB
    RE --> RP
    RP --> PG
```
