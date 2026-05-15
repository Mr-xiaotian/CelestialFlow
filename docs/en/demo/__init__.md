# demo/__init__.py Documentation

> 📅 Last Updated: 2026/04/22

## Purpose

Marks the `demo/` directory as a Python package, enabling imports like `from demo.xxx import ...` for demo modules.

## Contents

The file is currently empty (0 bytes) and exists solely as a package marker.

## Potential Issues

1. **Naming conflicts with tests/examples**: If `demo/` and `tests/examples/` contain files with the same name (e.g., `demo_executor.py`), Python's import system may resolve to the wrong module depending on `sys.path` order.
2. **Intra-package relative import limitations**: Since `demo/` is not on the default Python path relative to the project root, running submodules directly may cause `ModuleNotFoundError`.

## How to Run

No direct execution needed. To import demo as a package, ensure the project root is in `PYTHONPATH`:
```bash
set PYTHONPATH=D:\Project\CelestialFlow;%PYTHONPATH%
python -c "from demo import demo_executor"
```
