# Subagent: Tests

> 覆盖 `tests/` 目录下所有测试文件的中文文档。

## 文件清单

### 根目录 (2 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/__init__.py` | `docs/zh-CN/tests/__init__.md` |
| 2 | `tests/conftest.py` | `docs/zh-CN/tests/conftest.md` |

### runtime (9 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/runtime/__init__.py` | `docs/zh-CN/tests/runtime/__init__.md` |
| 2 | `tests/runtime/test_dispatch.py` | `docs/zh-CN/tests/runtime/test_dispatch.md` |
| 3 | `tests/runtime/test_envelope.py` | `docs/zh-CN/tests/runtime/test_envelope.md` |
| 4 | `tests/runtime/test_errors.py` | `docs/zh-CN/tests/runtime/test_errors.md` |
| 5 | `tests/runtime/test_estimators.py` | `docs/zh-CN/tests/runtime/test_estimators.md` |
| 6 | `tests/runtime/test_hash.py` | `docs/zh-CN/tests/runtime/test_hash.md` |
| 7 | `tests/runtime/test_metrics.py` | `docs/zh-CN/tests/runtime/test_metrics.md` |
| 8 | `tests/runtime/test_queue.py` | `docs/zh-CN/tests/runtime/test_queue.md` |
| 9 | `tests/runtime/test_types.py` | `docs/zh-CN/tests/runtime/test_types.md` |

### graph (5 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/graph/__init__.py` | `docs/zh-CN/tests/graph/__init__.md` |
| 2 | `tests/graph/test_analysis.py` | `docs/zh-CN/tests/graph/test_analysis.md` |
| 3 | `tests/graph/test_graph.py` | `docs/zh-CN/tests/graph/test_graph.md` |
| 4 | `tests/graph/test_serialize.py` | `docs/zh-CN/tests/graph/test_serialize.md` |
| 5 | `tests/graph/test_structure.py` | `docs/zh-CN/tests/graph/test_structure.md` |

### funnel (3 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/funnel/__init__.py` | `docs/zh-CN/tests/funnel/__init__.md` |
| 2 | `tests/funnel/test_inlet.py` | `docs/zh-CN/tests/funnel/test_inlet.md` |
| 3 | `tests/funnel/test_spout.py` | `docs/zh-CN/tests/funnel/test_spout.md` |

### stage (4 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/stage/__init__.py` | `docs/zh-CN/tests/stage/__init__.md` |
| 2 | `tests/stage/test_executor.py` | `docs/zh-CN/tests/stage/test_executor.md` |
| 3 | `tests/stage/test_stage.py` | `docs/zh-CN/tests/stage/test_stage.md` |
| 4 | `tests/stage/test_stages.py` | `docs/zh-CN/tests/stage/test_stages.md` |

### observability (3 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/observability/__init__.py` | `docs/zh-CN/tests/observability/__init__.md` |
| 2 | `tests/observability/test_observer.py` | `docs/zh-CN/tests/observability/test_observer.md` |
| 3 | `tests/observability/test_reporter_injection.py` | `docs/zh-CN/tests/observability/test_reporter_injection.md` |

### persistence (5 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/persistence/__init__.py` | `docs/zh-CN/tests/persistence/__init__.md` |
| 2 | `tests/persistence/test_fail.py` | `docs/zh-CN/tests/persistence/test_fail.md` |
| 3 | `tests/persistence/test_jsonl.py` | `docs/zh-CN/tests/persistence/test_jsonl.md` |
| 4 | `tests/persistence/test_log.py` | `docs/zh-CN/tests/persistence/test_log.md` |
| 5 | `tests/persistence/test_success.py` | `docs/zh-CN/tests/persistence/test_success.md` |

### utils (2 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/utils/test_clone.py` | `docs/zh-CN/tests/utils/test_clone.md` |
| 2 | `tests/utils/test_format.py` | `docs/zh-CN/tests/utils/test_format.md` |

### web (3 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `tests/web/__init__.py` | `docs/zh-CN/tests/web/__init__.md` |
| 2 | `tests/web/conftest.py` | `docs/zh-CN/tests/web/conftest.md` |
| 3 | `tests/web/test_server.py` | `docs/zh-CN/tests/web/test_server.md` |

## 区域特化陷阱（高频错误）

| 陷阱 | 典型表现 | 排查方法 |
|------|---------|---------|
| 🔴 遗漏测试类/函数 | 源码新增了 `TestTaskGraphFinalize`、`TestTaskGraphRuntimeSnapshot`、`TestObjectToHash`、`CelestialFlowTimeoutError` 测试，文档未提及 | `grep "class Test"` 对照文档中的测试覆盖列表 |
| 🔴 文件名错误 | 文档写 `test_reporter.py` → 实际为 `test_observer.py` + `test_reporter_injection.py`；文档写 `test_routes.py` → 实际为 `conftest.py` + `test_server.py` | `find_path` 列出实际文件名 |
| 🟠 测试类名引用错误 | `TestTaskQueue` → `TestTaskInQueue`/`TestTaskOutQueue` | grep 实际类名 |
| 🟠 函数名引用错误 | `calc_global_remain_equal_pred` → `calc_global_pending`、`create_mock_stage_runtime` → `make_stage` | grep 源码中的 fixture/辅助函数名 |
| 🟡 fixture 描述错误 | conftest.py 遗漏 `wait_until()`/`assert_stays_true()` 辅助函数 | 读取 conftest.py 完整内容 |
| 🟡 测试实现描述错误 | 文档说用 mock 队列 → 实际用 `TaskGraph` | 阅读测试代码的实际实现路径 |
| 🟢 遗漏 `__init__.py` 对应文档 | `tests/utils/` 缺少 `__init__.md` | 检查每个子目录是否有 `__init__.py` 以及对应的 `__init__.md` |

### 区域差异化写作规则

**测试文档通用规则：**
- **不要逐行复述测试代码。** 重点说明：测试覆盖目标、关键场景、断言意图。
- 使用示例用 `pytest -k "pattern" -v` 格式，**不要用 `python` 代码块**。
- 用 ` ```bash ` 包裹 pytest 命令。

**`__init__.py` → `__init__.md`：**
- 根 `tests/__init__.md`：列出全部测试子包的覆盖范围。
- 子包 `__init__.md`：说明本子包的测试目标（如 `tests/runtime/__init__.md` → "覆盖 runtime 模块的核心组件"）。

**`conftest.py` → `conftest.md`：**
- 说明提供的 fixture 及其用途（输入参数、返回值、使用场景）。
- **不需要提供运行方式。**

**`test_*.py` → `test_*.md`：**
- 用**表格**总结测试覆盖矩阵（测试类/函数 | 覆盖目标 | 关键断言）。
- 用 `flowchart` 展示测试依赖关系（如 fixture 依赖链）。
- 选择性运行示例：
  ```bash
  # 运行该文件全部测试
  pytest tests/runtime/test_queue.py -v

  # 运行特定测试类
  pytest tests/runtime/test_errors.py::TestCelestialFlowError -v

  # 按关键字匹配
  pytest tests/graph/ -k "serialize" -v
  ```
