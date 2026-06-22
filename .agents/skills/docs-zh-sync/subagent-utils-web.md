# Subagent: Utils + Web (Python, Routes, Templates)

> 覆盖 `src/celestialflow/__init__.py`、`utils/`、`web/` 下除 `static/` 外的所有文件。
>
> 开始工作前，请先阅读同目录下的 `_subagent-base.md`、`_subagent-audit.md`、`_subagent-writing.md`，再结合本文件和主 agent 提供的文件清单执行审计。

## 文件清单

> 具体的代码→文档对照清单由主 agent 在委派时提供。子代理以主 agent 提供的清单为准。

## 区域特化陷阱（高频错误）

| 陷阱 | 典型表现 | 排查方法 |
|------|---------|---------|
| 🔴 虚构 API 端点 | 文档列 `/api/pull_summary`、`/api/push_summary` 等不存在的路由 | grep 源码中的 `@router.get`/`@router.post` 注册 |
| 🔴 模型结构重构未同步 | `TaskInjectionModel` 从字段模式改为 `RootModel[dict]`、`WebConfigModel` 从平铺改为嵌套分组（`global`/`dashboard`/`errors`/`injection`） | 关注 Pydantic 类的继承变化（`BaseModel` vs `RootModel`） |
| 🔴 模型字段过期 | `StructureModel.items` → `structure`、`ErrorData.error_repr` → `error_type`/`error_message` | 逐字段对照 Pydantic model 定义 |
| 🟠 缺失参数 | `normalize_errors_query`/`paginate_errors` 新增 `sort_order` 参数 | 逐函数签名对照 |
| 🟠 返回类型错误 | `pull_task_injection` 返回 `list[dict]` → `dict[str, list[Any]]` | 关注路由函数的返回类型注解和实际返回结构 |
| 🟡 实现逻辑描述错误 | 注入"追加"→"覆盖"、克隆用 `deepcopy`→构造新实例 | 阅读源码中实际操作 |
| 🟡 虚构属性/字段 | `clone_executor` 的 `unpack_task_args` 字段 | grep 属性赋值/定义位置 |
| 🟢 虚构功能 | 文档提到"文件上传"等，源码无对应路由或处理 | grep 全量核对 |

### 区域差异化写作规则

- **`src/celestialflow/__init__.py`**：列出完整 `__all__` 列表，按子模块分组。提供完整的包导入示例（包括 top-level import 和子模块 import）。
- **`utils/__init__.py`**：列出工具模块的全部导出符号。
- **`util_*.py`**：逐函数说明用途、参数、返回值。建议用表格（函数名 | 用途 | 关键参数 | 返回值）。
- **`core_server.py`**：用 `flowchart` 展示服务器启动流程。用 `sequenceDiagram` 展示请求处理管线（路由 → 中间件 → 处理器）。重点说明 FastAPI app 的创建、路由注册、中间件配置。
- **`util_models.py`**：用表格列出所有 Pydantic 模型的字段、类型、默认值、用途。**注意区分 `BaseModel` 和 `RootModel`**。用 `classDiagram` 展示模型继承关系。
- **`util_config.py`**：说明配置加载、验证、默认值机制。注意配置的嵌套访问方式。
- **`util_error.py`**：说明错误查询、过滤、排序、分页的函数签名和参数。注意新增的 `sort_order` 参数。
- **`util_cal.py`**：说明计算相关工具函数。
- **`routes/pull_routes.py`**：用表格列出所有 GET 端点（路径 | 参数 | 返回模型 | 用途）。确保**端点列表与源码完全一致**。
- **`routes/push_routes.py`**：用表格列出所有 POST/PUT 端点（路径 | 请求体模型 | 用途）。说明注入的覆盖语义（非追加）。
- **`templates/index.html`**：用 `flowchart` 展示页面区域划分（dashboard/summary/history/structure/statuses/errors/injection）。说明引用的 TS 模块和 CSS 文件。
