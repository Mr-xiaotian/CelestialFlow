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
```

## 数据流

```
1. 页面交互 -> 选中节点 + 输入数据
2. 点击提交 -> validateJSON() 校验
3. 后端请求 -> POST /api/push_injection_tasks
4. UI 反馈 -> 展示注入成功/失败状态
```

## 使用示例

### 任务注入的数据格式和使用示例

以下示例展示任务注入功能的典型操作流程和数据结构：

```typescript
// 1. 模拟选中的目标节点
const selectedNodes = [
    { tag: "StageA", name: "数据加载" },
    { tag: "StageB", name: "数据处理" },
];

// 2. 任务注入请求的数据格式
// POST /api/push_injection_tasks
const injectionPayload = {
    node: "StageA",              // 目标节点标签
    task_datas: [                // 任务数据列表
        { id: 101, content: "file_a.csv" },
        { id: 102, content: "file_b.csv" },
        { id: 103, content: "file_c.csv" },
    ],
    timestamp: "2026-05-24T10:30:00",  // ISO 格式时间戳
};

// 3. 通过 fetch API 手动提交注入
async function injectTasks(node: string, taskDatas: any[]) {
    const res = await fetch("/api/push_injection_tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            node,
            task_datas: taskDatas,
            timestamp: new Date().toISOString(),
        }),
    });
    return res.json();
}

// 4. 验证 JSON 数据的合法性
function validateJSON(str: string): { valid: boolean; data?: any; error?: string } {
    try {
        const data = JSON.parse(str);
        if (!Array.isArray(data)) {
            return { valid: false, error: "数据必须是 JSON 数组格式" };
        }
        return { valid: true, data };
    } catch (e) {
        return { valid: false, error: "JSON 格式不合法" };
    }
}

// 5. 使用 validateJSON 校验输入
const validInput = '[{"id":1}, {"id":2}]';
const invalidInput = '{invalid json}';

console.log(validateJSON(validInput));
// { valid: true, data: [{ id: 1 }, { id: 2 }] }

console.log(validateJSON(invalidInput));
// { valid: false, error: "JSON 格式不合法" }

// 6. 批量向多个节点注入
async function injectToMultipleNodes(nodes: string[], taskDatas: any[]) {
    const results = await Promise.allSettled(
        nodes.map(node => injectTasks(node, taskDatas))
    );
    
    const successCount = results.filter(r => r.status === "fulfilled").length;
    const failCount = results.filter(r => r.status === "rejected").length;
    
    console.log(`注入完成: ${successCount} 成功, ${failCount} 失败`);
    return results;
}

// 7. 终止信号注入
// 通过 fillTermination() 在输入框中填入终止信号
const terminationPayload = ["TERMINATION_SIGNAL"];
// 后端收到此信号后会终止对应节点的任务处理
```
