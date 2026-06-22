# Subagent: Runtime + Graph

> 覆盖 `src/celestialflow/runtime/` 和 `src/celestialflow/graph/` 的中文文档。
>
> 开始工作前，请先阅读同目录下的 `_subagent-base.md`、`_subagent-audit.md`、`_subagent-writing.md`，再结合本文件和主 agent 提供的文件清单执行审计。

## 文件清单

> 具体的代码→文档对照清单由主 agent 在委派时提供。子代理以主 agent 提供的清单为准。

## 区域特化陷阱（高频错误）

本区域最常见的 doc-code mismatch 模式：

| 陷阱 | 典型表现 | 排查方法 |
|------|---------|---------|
| 🔴 函数/方法重命名 | `get_graph_summary` → `get_status_snapshot`、`change_id` → 不存在、`calc_global_remain_equal_pred` → `calc_global_pending` | grep 源码 `def ` 与文档函数名交叉比对 |
| 🔴 参数签名重构 | 参数数量、名称、默认值变更 | 逐方法对比 `__init__` 和公开方法签名 |
| 🔴 `__all__` 过期 | `__init__.py` 新增导出但文档未列出 | 读取 `__init__.py` 末尾的 `__all__` |
| 🟠 虚构内部方法 | 文档写了 `_check_and_mark_duplicate_task` 但源码为内联实现 | 确认文档中的每个方法名在源码中确实以 `def` 定义 |
| 🟡 类型字段虚构 | 文档为 `PersistedErrorRecord` 写了不存在的字段 | 对照 dataclass/NamedTuple 的字段列表 |
| 🟡 异常用途描述错误 | `GraphManagedError`/`UnconsumedError` 描述与实际抛出场景不符 | 追踪异常的 raise 位置和上下文 |

### 区域差异化写作规则

- **`__init__.py` → `__init__.md`**：列出全部 `__all__` 导出符号，按子模块（dispatch/envelope/queue/metrics/errors/hash/types/estimators/constant）分组。包根入口需有完整的包导入使用示例。
- **`core_*.py` → `core_*.md`**：重点写核心对象的职责、构造参数、关键方法、数据流、状态转换。用 Mermaid `classDiagram` 展示类关系，`stateDiagram` 展示状态转换，`flowchart` 展示数据流。
- **`util_errors.py` → `util_errors.md`**：用 Mermaid `classDiagram` 展示异常继承树，逐异常说明触发条件和含义。
- **`util_estimators.py` → `util_estimators.md`**：逐函数说明计算公式、参数、返回值含义。注意函数签名是否包含虚构参数。
- **`util_types.py` → `util_types.md`**：逐 dataclass/NamedTuple 说明字段和用途，确认字段列表与源码完全一致。
- **`util_hash.py` → `util_hash.md`**：说明哈希算法的选择和用途。
- **`util_constant.py` → `util_constant.md`**：列出常量和枚举，说明其使用场景。
- **`core_graph.py`**：重点关注 `TaskGraph` 的构造、`set_stages`、生命周期管理、状态快照。用 `flowchart` 展示 graph → stages → nodes 的层级关系。
- **`core_structure.py`**：重点关注预定义图结构的构造方式（6 种结构模式），每种结构需要一个 `flowchart` 图展示拓扑。
- **`util_analysis.py`**：说明图分析函数（如拓扑排序、环检测）的输入输出。
- **`util_serialize.py`**：说明图结构序列化和反序列化的格式和流程。
