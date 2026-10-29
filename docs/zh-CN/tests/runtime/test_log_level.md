# tests/runtime/test_log_level.py

> 📅 最后更新日期: 2026/10/30

## 作用
验证 `celestialflow.runtime.util_log_level.normalize_log_level` 的输入规范化与错误分支：级别名大小写不敏感、忽略首尾空白；未知级别与非字符串输入分别抛出 `InvalidOptionError` 与 `ConfigurationError`。

## 核心测试对象
- `normalize_log_level(log_level)`: 校验并规范化日志级别，返回 `LEVEL_DICT` 中的大写键名；非字符串抛 `ConfigurationError`，不在允许集合内抛 `InvalidOptionError`。
- `DEFAULT_LOG_LEVEL`: 运行入口未显式指定日志级别时使用的默认值（`"INFO"`），定义在同一模块中，供 `run` / `restore_db` 等入口作为参数默认值。
- `InvalidOptionError`: 继承 `ConfigurationError`，携带 `field` / `value` / `allowed`，允许集合来自 `LEVEL_DICT` 的键：`TRACE`、`DEBUG`、`SUCCESS`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestNormalizeLogLevel` | 3 | 大小写与空白规范化、未知级别拒绝、非字符串拒绝 |

## 关键测试场景

### `TestNormalizeLogLevel`
1. **规范化** (`test_uppercases_and_strips`): `normalize_log_level(" error ")` 返回 `"ERROR"`，说明 `strip().upper()` 生效。
2. **拒绝未知级别** (`test_rejects_unknown_level`): `normalize_log_level("VERBOSE")` 抛 `InvalidOptionError`。
3. **拒绝非字符串** (`test_rejects_non_string`): `normalize_log_level(30)` 抛 `ConfigurationError`（类型检查先于取值检查）。

## 测试重点
- **输入容错**: 大小写与首尾空白不影响合法级别的解析。
- **错误分层**: 类型错误走 `ConfigurationError`，取值错误走更具体的 `InvalidOptionError`，调用方可按粒度捕获。
- **允许集合单一来源**: 合法级别由 `LEVEL_DICT` 的键决定，避免测试与实现各自维护一份列表。

## 使用示例

```python
from celestialflow.runtime.util_errors import ConfigurationError, InvalidOptionError
from celestialflow.runtime.util_log_level import DEFAULT_LOG_LEVEL, normalize_log_level

print(DEFAULT_LOG_LEVEL)                 # INFO
print(normalize_log_level(" debug "))    # DEBUG

try:
    normalize_log_level("VERBOSE")
except InvalidOptionError as error:
    print(error.field)    # log level
    print(error.allowed)  # 允许的级别元组

try:
    normalize_log_level(30)  # type: ignore[arg-type]
except ConfigurationError as error:
    print(error)  # log level must be a string, got 30.
```

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_log_level.py -v

# 仅运行规范化用例
pytest tests/runtime/test_log_level.py -k "uppercases" -v

# 仅运行错误分支用例
pytest tests/runtime/test_log_level.py -k "rejects" -v
```

## 重要细节
- `normalize_log_level` 先用 `isinstance` 严格判断字符串，因此整数、`None` 等输入不会进入级别比较分支。
- 返回值一定是 `LEVEL_DICT` 中的大写键名，调用方可直接用于日志过滤器的级别设置。
- 全部用例为纯内存计算，无 I/O 副作用。

## 注意事项
- 相关实现位于 `src/celestialflow/runtime/util_log_level.py`；`util_*` 属于运行入口内部工具，不从 `celestialflow.runtime` 包再导出。
- 本文件未对 `DEFAULT_LOG_LEVEL` 单独设断言，默认值由需要日志级别的运行入口在参数默认值中体现。
