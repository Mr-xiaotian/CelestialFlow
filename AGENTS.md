# Agents

## 环境

- uv: 0.10.6
- Python: 3.14.3

## 规范

### 关于 `core_*` 文件与 `util_*` 文件

- 在模块级 `__init__.py` 中只能导出 `core_*` 开头的文件。
- 以 `core_*` 代码为主, 如果 `util_*` 代码与前者冲突, 优先修改 `util_*` 代码。

### 修改完文件

- 执行 `uv run ruff check --fix .` 与 `uv run pyright .` 检查并修复代码格式与类型错误。
- 如果修改对象是代码, 为代码添加或者更新reST风格的doc-string, 并保持与代码逻辑一致。