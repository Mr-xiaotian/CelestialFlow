# tests/runtime/test_config.py

> 📅 最后更新日期: 2026/10/30

## 作用
验证 `celestialflow.runtime.ReportConfig` 的构造校验与地址规范化：默认地址回退、首尾空白与末尾斜杠的清理、以及非字符串/空串/非法协议等非法输入是否通过 `ConfigurationError` 拒绝；同时验证配置对象不可变。

## 核心测试对象
- `ReportConfig`: 冻结的 dataclass（`frozen=True, slots=True`），唯一字段为 `url`，构造时在 `__post_init__` 中完成校验与规范化。
- `DEFAULT_REPORT_URL`: 未显式指定地址时使用的默认上报地址（`http://127.0.0.1:5005`），由 `celestialflow.runtime` 包再导出。
- `ConfigurationError`: 非法地址统一抛出的自定义配置异常。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestReportConfig` | 6 | 默认地址、空白与末尾斜杠规范化、空串拒绝、非 `http`/`https` 协议拒绝、非字符串拒绝、对象冻结 |

## 关键测试场景

### `TestReportConfig`
1. **默认地址** (`test_default_url`): 无参构造的 `ReportConfig().url == DEFAULT_REPORT_URL`。
2. **规范化为去斜杠地址** (`test_strips_whitespace_and_trailing_slash`): `ReportConfig(url=" http://127.0.0.1:9000/ ")` 的 `url` 为 `"http://127.0.0.1:9000"`，避免与上报端点拼接出双斜杠。
3. **拒绝空白串** (`test_rejects_empty_url`): `url="   "` 去除空白后为空，抛 `ConfigurationError`。
4. **拒绝非 HTTP 协议** (`test_rejects_non_http_scheme`): `url="ftp://127.0.0.1:9000"` 抛 `ConfigurationError`。
5. **拒绝非字符串** (`test_rejects_non_string_url`): `url=5005` 抛 `ConfigurationError`。
6. **不可变性** (`test_is_frozen`): 构造后对 `url` 赋值抛 `AttributeError`。

## 测试重点
- **启动前校验**: 地址在 `ReportConfig` 构造阶段即完成校验，非法配置会在运行期资源启动之前失败。
- **规范化**: 首尾空白被 `strip()`、末尾斜杠被 `rstrip("/")` 去除，保证端点拼接路径稳定。
- **显式启用语义**: 上报开启与否由是否向运行入口传入 `ReportConfig` 决定；`ReportConfig` 本身不再是「开关 + 地址」的组合配置。
- **失败模式明确**: 所有非法地址都以 `ConfigurationError` 拒绝，而非静默回退到默认值。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_config.py -v

# 仅运行默认地址与规范化用例
pytest tests/runtime/test_config.py -k "default_url or strips_whitespace" -v

# 仅运行非法输入与冻结相关用例
pytest tests/runtime/test_config.py -k "rejects or frozen" -v
```

## 重要细节
- 实现中 `url` 经 `urlsplit` 校验：协议必须是 `http` / `https`，且必须存在 `netloc`（如 `http://` 这类缺少主机的地址同样被拒绝）；测试用例通过 `ftp://` 覆盖协议非法分支。
- 因为 `slots=True` 且 `frozen=True`，实例既不能动态添加属性，也不能在构造后改写 `url`。
- 全部用例为纯内存构造，无文件/网络副作用。

## 注意事项
- 相关实现位于 `src/celestialflow/runtime/core_config.py`，公开符号由 `src/celestialflow/runtime/__init__.py` 再导出。
- 宿主项目 `pyproject.toml` 不再参与上报配置读取，配置必须由调用方显式传入。
