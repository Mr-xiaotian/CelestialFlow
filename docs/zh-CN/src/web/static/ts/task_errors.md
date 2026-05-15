# task_errors.ts

> 📅 最后更新日期: 2026/05/15

管理错误日志数据的加载、服务端分页/过滤和渲染。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `errors` | `any[]` | 当前页的错误记录数组，从后端拉取 |
| `currentPage` | `number` | 当前页码，默认 1 |
| `pageSize` | `number` | 每页条数，固定为 10 |
| `totalPages` | `number` | 总页数，从后端返回 |
| `errorsRev` | `number` | 上次拉取的版本号，用于增量拉取（`known_rev`） |
| `lastQueryKey` | `string` | 上次查询的缓存键，用于判断筛选条件是否变化 |
| `errorsRequestSeq` | `number` | 请求序列号，防止旧请求覆盖新结果 |

## DOM 元素引用

| 变量 | 选择器 | 说明 |
|------|--------|------|
| `searchInput` | `#error-search` | 关键词搜索框 |
| `nodeFilter` | `#node-filter` | 节点筛选下拉框 |
| `errorsTableBody` | `#errors-table tbody` | 错误表格体 |
| `paginationContainer` | `#pager-container` | 分页控件容器 |

## 函数

### `buildErrorsQueryKey(page, pageSize, node, keyword)`

将分页和筛选参数组合为缓存键字符串（`page|pageSize|node|keyword`），用于检测查询条件是否变化。

---

### `loadErrors(forceReload?)`

异步从 `GET /api/pull_errors` 拉取错误数据，支持服务端分页和过滤。

**请求参数：**

| 参数 | 说明 |
|------|------|
| `known_rev` | 版本号，筛选条件变化或 `forceReload` 时重置为 -1 |
| `page` | 当前页码 |
| `page_size` | 每页条数 |
| `node` | 节点筛选值 |
| `keyword` | 搜索关键词 |

**竞态保护：** 通过 `errorsRequestSeq` 递增序列号，响应到达时校验序列号是否匹配，丢弃过期响应。

---

### `renderErrors()`

渲染错误表格。表格列：序号、错误 id、错误信息、节点、任务、时间。空数据时显示占位提示。

---

### `goToErrorsPage(nextPage)`

跳转到指定页码，调用 `loadErrors(true)` 强制重新加载并重新渲染。

---

### `buildPageList(current, total)`

生成智能页码数组，包含首尾页、当前页及其前后 2 页，中间缺口用 `"…"` 填充。

---

### `renderPaginationControls(totalPages)`

渲染分页控件，含「上一页」/「下一页」按钮和数字页码。单页时不显示控件。

---

### `populateNodeFilter(statuses)`

从 `statuses`（`Record<string, NodeStatus>`）中读取节点名填充下拉筛选器，尽量保留用户当前选中的节点。由 `main.ts` 在 `statusesChanged` 时调用。

## 事件监听

- `searchInput` 的 `input` 事件 → 重置到第1页，强制重新加载并重新渲染
- `nodeFilter` 的 `change` 事件 → 重置到第1页，强制重新加载并重新渲染

## 错误记录字段

| 字段 | 说明 |
|------|------|
| `error_id` | 错误 ID（整数） |
| `error_repr` | 错误信息字符串 |
| `stage` | 所属节点 tag |
| `task_repr` | 任务内容字符串 |
| `ts` | 错误时间戳（Unix 秒） |
