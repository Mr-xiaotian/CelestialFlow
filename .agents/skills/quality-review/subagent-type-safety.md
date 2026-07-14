# Subagent: Type Safety

> 检查方向：类型标注完整性、`Any` 逃逸、`type: ignore` 必要性、类型收窄。

## 检查清单

逐文件审查时，按以下清单逐项排查：

### 1. 类型标注覆盖率
- 所有公开方法的参数和返回值是否有完整类型标注？
- 私有方法（`_xxx`）的关键参数是否遗漏标注？
- 类属性是否有 Class-level type annotations？

### 2. `Any` 逃逸
- 是否存在不必要的 `Any` 标注（可以用更具体的类型替换）？
- `dict[str, Any]` 是否可以用 `TypedDict` 或 dataclass 替代？
- 泛型容器（`list`、`dict`、`tuple`）的元素类型是否已标注？

### 3. `type: ignore` 与 `# pyright: ignore`
- 每个 `type: ignore` 注释是否**必要**？能否通过改进类型标注消除？
- 是否存在可以删除的、已过时的 ignore 注释？

### 4. 类型收窄
- `isinstance` 检查后的分支中是否正确利用了类型收窄？
- `Optional[T]` 类型的值在使用前是否做了 `None` 检查？
- Union 类型（`T1 | T2`）是否在分支中被正确区分？

### 5. 泛型使用
- 是否正确使用了泛型（`TaskStage[T, R]`、`TaskExecutor[T, R]`）？
- 泛型参数是否在继承/实例化时被具体化，而非保留为 `Any`？
- 自定义泛型类/函数的 TypeVar 约束是否合理？

### 6. 协议与结构化子类型
- `Protocol` 类的使用是否一致？
- 是否存在应该用 Protocol 但用了 ABC 的情况（或反之）？

---

## 区域特化提示

| 区域 | 重点关注 |
|------|---------|
| `stage/` | 泛型 `[T, R]` 是否被正确传播？`kwargs: Any` 是否能收窄？ |
| `runtime/` | `TaskEnvelope`、`TaskMetrics` 等数据类的字段类型是否完整？ |
