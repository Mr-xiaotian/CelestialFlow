# RuntimeConfig

> 📅 最后更新日期: 2026/08/12

`runtime/util_config.py` 提供运行时配置加载功能，目前用于从项目级配置文件中读取日志级别。

## 主要函数

### load_log_level_from_pyproject

```python
def load_log_level_from_pyproject() -> str: ...
```

从项目级 ``pyproject.toml`` 的 ``[tool.celestialflow]`` 节读取 ``log_level``。

- 从当前工作目录开始向上搜索 ``pyproject.toml``
- 未找到时返回 ``"INFO"``
- 找到但值为非法级别时抛出 ``InvalidOptionError``
- 解析失败（TOML 格式错误）则继续向上搜索

### 返回值

返回大写字符串（如 `"INFO"`、`"DEBUG"`），使用 `util_constant.LEVEL_DICT` 进行合法性校验。

## 使用示例

```python
from celestialflow.runtime.util_config import load_log_level_from_pyproject

# 读取配置中的日志级别
level = load_log_level_from_pyproject()
print(f"当前日志级别: {level}")
```

## 注意事项

- 仅支持 TOML 格式的配置文件
- 日志级别合法值由 `util_constant.LEVEL_DICT` 定义，包括 `TRACE`/`DEBUG`/`SUCCESS`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`
