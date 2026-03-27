# task_errors.ts

管理错误日志数据的加载、过滤、分页和渲染。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `errors` | `any[]` | 错误记录数组，从后端拉取 |
| `errorsOffset` | `number` | 已同步的错误条数，用于增量拉取 |
| `currentPage` | `number` | 当前页码，默认 1 |
| `pageSize` | `number` | 每页条数，固定为 10 |

## 函数

### `loadErrors()`

异步从 `GET /api/pull_errors?offset=N` 拉取错误列表增量，更新 `errors`。

- 若 `data.total < errorsOffset`（服务端重启后 error_store 已清空），全量重新同步
- 新增条目 append 到 `errors` 末尾，返回 `true`；无新数据返回 `false`

---

### `renderErrors()`

渲染错误表格，支持节点过滤和关键词搜索，按时间戳降序排列。

**过滤规则：**
- 节点筛选：匹配 `e.stage === filter`
- 关键词搜索：模糊匹配 `e.error_repr` 或 `e.task_repr`（不区分大小写）

表格列：错误 id、错误信息、节点、任务、时间。

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

- `searchInput` 的 `input` 事件 → 重置到第1页并重新渲染
- `nodeFilter` 的 `change` 事件 → 重置到第1页并重新渲染

## 错误记录字段

| 字段 | 说明 |
|------|------|
| `error_id` | 错误 ID（整数） |
| `error_repr` | 错误信息字符串 |
| `stage` | 所属节点 tag |
| `task_repr` | 任务内容字符串 |
| `ts` | 错误时间戳（Unix 秒） |
