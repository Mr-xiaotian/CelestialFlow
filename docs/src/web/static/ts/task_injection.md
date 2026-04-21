# task_injection.ts

任务注入页面的逻辑，支持选择节点、输入任务数据（JSON 文本或文件上传）并提交到后端。

## 类型定义

```ts
type SelectedNode = { name: string; type: string; status?: number };
```

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `selectedNodes` | `SelectedNode[]` | 当前已选节点列表 |
| `currentInputMethod` | `string` | 当前输入方式：`"json"` 或 `"file"` |
| `uploadedFile` | `{name, content} \| null` | 已上传的 JSON 文件内容 |

## 函数

### `setupEventListeners()`

绑定页面事件：搜索框输入、JSON 文本框实时校验、文件选择、提交按钮。

---

### `renderNodeList(searchTerm?)`

渲染节点选择列表。

- 依据 `searchTerm` 过滤节点名
- 从 `nodeStatuses` 读取节点状态并渲染徽章
- 状态为 `2`（已停止）的节点禁止点击（`disabled-node` 样式）

---

### `selectNode(nodeName)` / `removeNode(nodeName)`

切换节点选中状态（再次点击已选节点取消选中），并调用 `updateSelectedNodes()` 刷新已选列表 UI。

---

### `selectAllNodes()`

全选所有 `status !== 2` 的节点（已停止节点除外）。

---

### `clearSelection()`

清空所有已选节点。

---

### `switchInputMethod(method)`

切换输入方式（`"json"` / `"file"`），更新对应区域的显示/隐藏和按钮激活状态。

---

### `fillTermination()`

在 JSON 文本框中填入预定义终止信号 `["TERMINATION_SIGNAL"]`，方便用户快速注入终止信号。

---

### `handleFileUpload(e)`

处理文件上传：仅接受 `.json` 格式，读取并验证 JSON 合法性，保存到 `uploadedFile`。

---

### `handleSubmit()`

提交任务注入。

1. 校验已选节点（至少一个）
2. 根据输入方式解析任务数据
3. 为每个选定节点依次 POST `/api/push_injection_tasks`，并行完成后显示成功提示
4. 调用 `clearForm()` 重置表单

---

### 辅助函数

| 函数 | 说明 |
|------|------|
| `showError(elementId, message)` | 显示错误提示文字 |
| `hideError(elementId)` | 隐藏错误提示 |
| `showStatus(message, isSuccess)` | 显示操作结果提示（3秒后自动隐藏） |
| `setButtonLoading(loading)` | 切换提交按钮的加载状态 |
| `clearForm()` | 重置所有选择、输入和错误提示 |

## 任务注入请求体

```json
{
    "node": "stage_tag",
    "task_datas": [...],
    "timestamp": "2024-01-01T00:00:00.000Z"
}
```

POST 到 `POST /api/push_injection_tasks`，服务端存入 `injection_tasks` 队列，由 `TaskReporter` 通过 `GET /api/pull_task_injection` 定期拉取并注入 `TaskGraph`。
