# errors.ts

> 📅 最后更新日期: 2026/05/23

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
