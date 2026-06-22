# Subagent: Tests

> 覆盖 `tests/` 目录下所有测试文件的中文文档。
>
> 开始工作前，请先阅读同目录下的 `_subagent-base.md`、`_subagent-audit.md`、`_subagent-writing.md`，再结合本文件和主 agent 提供的文件清单执行审计。

## 文件清单

> 具体的代码→文档对照清单由主 agent 在委派时提供。子代理以主 agent 提供的清单为准。

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
