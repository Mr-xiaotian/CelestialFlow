# injection.ts

> 📅 最后更新日期: 2026/05/23

管理任务手动注入页面的逻辑，支持多节点选择、JSON 文本输入、JSON 文件上传、终止信号快速填充以及注入提交。

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `selectedNodes` | `SelectedNode[]` | 用户当前选中的注入目标节点列表 |
| `currentInputMethod` | `string` | 当前输入模式：`json` 或 `file` |
| `uploadedFile` | `object \| null` | 存储已读取的文件名和文件内容 |

## 函数

### `setupEventListeners()`

初始化页面事件绑定，采用**事件委托**模式优化动态生成的节点列表交互。

- **搜索**: `#search-input` 实时过滤。
- **校验**: `#json-textarea` 实时格式校验。
- **切换**: `.input-toggle` 切换输入模式。
- **选择**: `.button-group` 处理全选/清空。
- **提交**: `#submit-btn` 触发注入流程。

---

### `renderNodeList(searchTerm)`

根据 `nodeStatuses` 渲染可选节点列表。

- **状态过滤**: 节点显示对应状态徽章（运行中/已停止/未运行）。
- **交互限制**: 已停止的节点被设为 `disabled-node` 样式且不可选中注入。

---

### `handleSubmit()`

执行任务注入提交逻辑。

1. **获取数据**: 根据当前 `currentInputMethod` 获取文本框内容或已上传文件内容。
2. **数据校验**: 确保已选节点不为空且数据格式为有效 JSON（且必须为列表结构）。
3. **并发注入**: 为每个选中的节点分别发起 `POST /api/push_injection_tasks` 请求。
4. **反馈展示**: 在页面显示注入结果（成功/失败/部分成功）。

---

### `switchInputMethod(method)`

在 JSON 文本域和文件上传区域之间切换 UI。

---

### `handleFileUpload(e)`

处理文件选择事件，读取 `.json` 文件内容并调用 `validateJSON()` 进行预校验。

---

### `fillTermination()`

辅助函数：在 JSON 输入框中一键填入标准的任务终止信号序列。

## 数据流

```
1. 页面交互 -> 选中节点 + 输入数据
2. 点击提交 -> validateJSON() 校验
3. 后端请求 -> POST /api/push_injection_tasks
4. UI 反馈 -> 展示注入成功/失败状态
```
