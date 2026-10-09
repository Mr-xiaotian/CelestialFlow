# tests/runtime/test_config.py

> 📅 最后更新日期: 2026/10/09

## 作用
验证 `celestialflow.runtime.util_config` 中的 `load_report_url_from_pyproject` 与 `load_if_report_from_pyproject` 两个函数，确保它们能从项目级 `pyproject.toml` 的 `[tool.celestialflow]` 节正确读取上报地址与上报开关，并在配置缺失或非法时回退到默认值 / 抛出 `ConfigurationError`。

## 核心测试对象
- `load_report_url_from_pyproject()`: 读取 `report_url`；未配置或没有 `pyproject.toml` 时返回 `DEFAULT_REPORT_URL`（`http://127.0.0.1:5005`）。
- `load_if_report_from_pyproject()`: 读取 `if_report`；未配置或没有 `pyproject.toml` 时返回 `False`；配置为非布尔时抛出 `ConfigurationError`。
- `DEFAULT_REPORT_URL`: 上报地址的默认常量，作为无配置时的回退值。

## 测试辅助
- `tmp_path` + `monkeypatch.chdir`: 在临时目录写入 `pyproject.toml` 后再调用被测函数，隔离对真实工作目录的依赖。

## 关键测试场景

### `load_report_url_from_pyproject`
1. **读取已配置地址** (`test_load_report_url_reads_report_url`): `pyproject.toml` 配置 `report_url = "http://127.0.0.1:9000"` 时返回该地址。
2. **未配置时的默认值** (`test_load_report_url_defaults_when_absent`): 仅有 `log_level` 而无 `report_url` 时返回 `DEFAULT_REPORT_URL`。
3. **无 `pyproject.toml`** (`test_load_report_url_defaults_without_pyproject`): 空目录下返回 `DEFAULT_REPORT_URL`。

### `load_if_report_from_pyproject`
1. **读取已配置开关** (`test_load_if_report_reads_true`): `if_report = true` 时返回 `True`。
2. **未配置时默认关闭** (`test_load_if_report_defaults_to_false`): 仅配置 `report_url` 而无 `if_report` 时返回 `False`（开关与地址解耦）。
3. **无 `pyproject.toml`** (`test_load_if_report_returns_false_without_pyproject`): 空目录下返回 `False`。
4. **非布尔配置抛错** (`test_load_if_report_rejects_non_boolean`): `if_report = "yes"` 时抛出 `ConfigurationError`。

## 测试重点
- **默认回退**: 上报地址与开关在配置缺失时都有明确的默认值。
- **开关解耦**: `report_url` 的存在不会隐式启用上报；`if_report` 必须显式为 `true`。
- **非法输入**: `if_report` 非布尔时通过 `ConfigurationError` 拒绝，而非静默忽略。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_config.py -v

# 仅运行上报地址相关测试
pytest tests/runtime/test_config.py -k "report_url" -v

# 仅运行上报开关相关测试
pytest tests/runtime/test_config.py -k "if_report" -v
```

## 注意事项
- 相关实现位于 `src/celestialflow/runtime/util_config.py`。
- 所有用例均通过 `monkeypatch.chdir` 切换工作目录，测试快速且无真实网络/文件副作用。