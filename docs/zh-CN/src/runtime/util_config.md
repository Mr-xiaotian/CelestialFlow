# src/celestialflow/runtime/util_config.py

> 📅 最后更新日期: 2026/10/09

`runtime/util_config.py` 提供运行时配置加载功能，用于从项目级 `pyproject.toml` 的 `[tool.celestialflow]` 节读取日志级别、上报地址与上报开关。

## 默认常量

### DEFAULT_REPORT_URL

`report_url` 未配置时使用的默认上报地址 `"http://127.0.0.1:5005"`。

## 主要函数

### load_log_level_from_pyproject

```python
def load_log_level_from_pyproject() -> str: ...
```

从项目级 `pyproject.toml` 的 `[tool.celestialflow]` 节读取 `log_level`。

- 从当前工作目录开始向上搜索 `pyproject.toml`
- 未找到时返回 `"INFO"`
- 找到但值为非法级别时抛出 `InvalidOptionError`
- 解析失败（TOML 格式错误）则继续向上搜索

返回大写字符串（如 `"INFO"`、`"DEBUG"`），使用 `util_constant.LEVEL_DICT` 进行合法性校验。

### load_report_url_from_pyproject

```python
def load_report_url_from_pyproject() -> str: ...
```

从项目级 `pyproject.toml` 的 `[tool.celestialflow]` 节读取 `report_url`。

- 从当前工作目录开始向上搜索 `pyproject.toml`
- 未找到对应配置时返回默认地址 `DEFAULT_REPORT_URL`
- 解析失败（TOML 格式错误）则继续向上搜索

### load_if_report_from_pyproject

```python
def load_if_report_from_pyproject() -> bool: ...
```

从项目级 `pyproject.toml` 的 `[tool.celestialflow]` 节读取 `if_report`。

- 从当前工作目录开始向上搜索 `pyproject.toml`
- 未配置时返回 `False`
- 上报开关与上报地址解耦：只有显式配置为 `true` 时才启用上报，`report_url` 的存在本身不再触发上报
- 配置值不是布尔时抛出 `ConfigurationError`
- 解析失败（TOML 格式错误）则继续向上搜索

## 使用示例

```python
from celestialflow.runtime.util_config import (
    DEFAULT_REPORT_URL,
    load_log_level_from_pyproject,
    load_report_url_from_pyproject,
    load_if_report_from_pyproject,
)

# 读取配置中的日志级别
level = load_log_level_from_pyproject()
print(f"当前日志级别: {level}")

# 上报地址与开关
url = load_report_url_from_pyproject()
if_report = load_if_report_from_pyproject()
print(f"上报地址: {url}（默认 {DEFAULT_REPORT_URL}），是否启用: {if_report}")
```

## 注意事项

- 仅支持 TOML 格式的配置文件
- 日志级别合法值由 `util_constant.LEVEL_DICT` 定义，包括 `TRACE`/`DEBUG`/`SUCCESS`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`