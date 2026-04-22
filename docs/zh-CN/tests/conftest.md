# conftest.py 测试配置说明

> 📅 最后更新日期: 2026/04/22

## 测试目标

`conftest.py` 是 pytest 的本地插件文件，负责在测试会话开始前加载项目级的环境变量配置，确保所有测试用例共享一致的外部服务连接参数（如 Redis、CelestialTree、Reporter 等）。

## 测试范围

- **环境初始化**：在 pytest 收集测试之前自动执行。
- **配置加载**：通过 `python-dotenv` 加载项目根目录下的 `.env` 文件。
- **零侵入设计**：不包含任何 fixture 定义或钩子函数，保持最小化职责。

## 依赖

| 依赖包 | 用途 |
|--------|------|
| `python-dotenv` | 从 `.env` 文件加载环境变量 |

## 可能的问题与注意事项

### 1. `.env` 文件缺失
如果项目根目录缺少 `.env` 文件，`load_dotenv()` 会静默跳过，不会报错。这意味着依赖环境变量的测试（如 `demo_stages.py` 中的 Redis 测试）可能会因为配置为空而失败或跳过。

**建议**：在 CI/CD 环境中通过环境变量直接注入，不依赖 `.env` 文件。

### 2. 环境变量污染
`load_dotenv()` 默认不会覆盖已存在的环境变量（`override=False`）。如果宿主机器已定义了同名变量（如 `REDIS_HOST`），实际使用的值可能与 `.env` 文件中的不一致。

**排查方式**：
```bash
pytest tests/ --collect-only -v
# 检查环境变量实际值
python -c "import os; print(os.getenv('REDIS_HOST'))"
```

### 3. 与 uv 虚拟环境的兼容性
在 Windows 上使用 `uv run` 时，若虚拟环境损坏可能导致 `dotenv` 加载失败。此时应检查 `.venv` 完整性，或直接使用 `python -m pytest` 运行。

## 运行方式

此文件无需手动运行，pytest 会自动加载：
```bash
pytest tests/
```

## 相关文件

- `.env`：环境变量定义文件
- `tests/demo_stages.py`：依赖环境变量最多的演示测试
