# errors.ts

> 📅 最后更新日期: 2026/05/28

管理错误日志的分页拉取、关键词搜索、节点过滤及表格渲染。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `errors` | `any[]` | 当前页的错误记录列表 |
| `currentPage` | `number` | 当前显示的页码，从 1 开始 |
| `pageSize` | `number` | 每页显示的记录数，由 `webConfig` 同步 |
| `totalPages` | `number` | 后端计算的总页数 |
| `errorsRev` | `number` | 数据版本号，用于增量拉取判断 |

## 函数

### `buildErrorsQueryKey(page, pageSizeValue, node, keyword)`

构建错误查询的缓存键字符串，用于判断筛选条件是否发生变化以决定是否强制重新拉取。

- **参数**: 当前页码、每页大小、节点筛选条件、搜索关键词
- **返回值**: 由 `|` 分隔的组合字符串，如 `"1|10|StageA|timeout"`
- 与 `lastQueryKey` 配合使用实现查询缓存对比

---

### `buildPageList(current, total)`

生成分页页码列表，包含首尾页、当前页及前后页，自动在跳页处插入省略号（`…`）。

- **参数**: `current` 当前页码，`total` 总页数
- **返回值**: `Array<number | string>`，数字页码或省略号字符串
- 用于 `renderPaginationControls()` 内部生成页码导航

---

### `loadErrors(forceReload)`

异步拉取错误日志数据。支持基于 `known_rev` 的增量拉取。

- **参数**: `forceReload` (可选) - 为 `true` 时强制忽略缓存重新拉取（如搜索条件变化时）。
- **查询参数**: `page`, `page_size`, `node` (节点过滤), `keyword` (模糊搜索)。
- **竞态保护**: 使用 `errorsRequestSeq` 确保旧请求的结果不会覆盖新请求。

---

### `renderErrors()`

将 `errors` 数据渲染到 `#errors-table` 表格，并调用 `renderPaginationControls()` 更新分页条。

**表格列：**
1. 序号 (基于页码计算)
2. 错误 ID
3. 错误信息 (超出长度显示省略号，悬停显示全称)
4. 节点 (节点 Tag)
5. 任务 (任务表示)
6. 时间 (本地格式化时间)

---

### `goToErrorsPage(nextPage)`

分页跳转逻辑，触发 `loadErrors(true)` 重新拉取特定页数据。

---

### `populateNodeFilter(statuses)`

根据仪表盘的节点状态，动态更新错误页的“按节点筛选”下拉框。

---

### `renderPaginationControls(totalPages)`

渲染分页控件，包括上一页/下一页按钮及带有省略号的数字页码序列。

## 交互特性

- **搜索联动**: 搜索框输入或节点筛选切换时，会重置 `currentPage` 并强制刷新。
- **响应式支持**: 在小屏设备下，错误表格会自动转换为卡片式布局（通过 `errors.css` 媒体查询实现）。
- **外部跳转**: 支持通过全局函数 `switchToErrorsTab(node?)`（定义于 `utils.ts`）从仪表盘卡片一键跳转并自动填充筛选条件。

## 使用示例

### 错误数据的格式和处理示例

以下示例展示错误日志的数据结构以及如何在浏览器控制台中手动操作：

```typescript
// 1. 错误记录的数据结构（来自后端）
const errorRecord = {
    ts: 1745400000,           // 时间戳（秒）
    error_id: "err_001",     // 错误 ID
    error_repr: "Connection timeout after 30s",  // 错误描述
    error: {                  // 原始错误对象
        type: "TimeoutError",
        message: "Connection timeout after 30s",
        stack: "...",
    },
    stage: "DataLoader",     // 所属节点
    task_repr: "file_123.json", // 任务标识
};

// 2. 模拟一批错误数据
const mockErrors = [
    { ts: 1745400100, error_id: "E001", error_repr: "连接超时", stage: "StageA", task_repr: "task_1", error: {} },
    { ts: 1745400050, error_id: "E002", error_repr: "内存不足", stage: "StageB", task_repr: "task_5", error: {} },
    { ts: 1745400000, error_id: "E003", error_repr: "文件未找到", stage: "StageA", task_repr: "task_2", error: {} },
    { ts: 1745399950, error_id: "E004", error_repr: "权限不足", stage: "StageC", task_repr: "task_3", error: {} },
];

// 3. 手动调用错误渲染
// 使用全局变量：
// errors = mockErrors;
// currentPage = 1;
// renderErrors();
// 这会渲染 #errors-table 表格，列包括：序号、错误ID、错误信息、节点、任务、时间

// 4. 分页跳转
// goToErrorsPage(2);  // 跳到第 2 页，触发 loadErrors(true)

// 5. 使用 URL 参数手动拉取错误
async function fetchErrorsManually(page: number, pageSize: number, node?: string, keyword?: string) {
    const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
    });
    if (node) params.set("node", node);
    if (keyword) params.set("keyword", keyword);

    const res = await fetch(`/api/pull_errors?${params}`);
    const data = await res.json();
    return data;
}

// 示例：获取 StageA 的前 5 条错误
// fetchErrorsManually(1, 5, "StageA").then(data => console.log(data));

// 6. 渲染分页控件
// renderPaginationControls(totalPages);
// 示例：总页数 5 时生成：< 1 2 3 4 5 >

// 7. 从其他标签页跳转到错误日志并自动过滤
// switchToErrorsTab("StageA");
// 这会：
//   - 切换到错误日志标签页
//   - 设置节点筛选下拉框为 "StageA"
//   - 触发查询
```
