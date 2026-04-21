# demo/__init__.py 说明

## 目标

将 `demo/` 目录标识为 Python 包，支持以 `from demo.xxx import ...` 的方式导入演示模块。

## 内容

当前文件为空（`0` 字节），仅作为包标记存在。

## 可能出现的问题

1. **与 tests/examples 的命名冲突**：若 `demo/` 和 `tests/examples/` 中存放了同名文件（如 `demo_executor.py`），Python 的导入系统可能根据 `sys.path` 顺序解析到错误的模块。
2. **包内相对导入限制**：由于 `demo/` 不在项目根目录的默认 Python 路径中，直接运行子模块时可能遇到 `ModuleNotFoundError`。

## 运行方式

无需直接运行。若需将 demo 作为包导入，确保项目根目录在 `PYTHONPATH` 中：
```bash
set PYTHONPATH=D:\Project\CelestialFlow;%PYTHONPATH%
python -c "from demo import demo_executor"
```
