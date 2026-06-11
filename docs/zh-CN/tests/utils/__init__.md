# utils 测试包

> 最后更新日期: 2026/06/11

## 作用
`tests/utils/` 覆盖 CelestialFlow 通用工具函数，包括图结构克隆与终端格式化输出。

## 包含的测试文件
- `test_clone.py`: 验证 `clone_executor`、`clone_stage`、`clone_graph` 的深度复制与独立性。
- `test_format.py`: 验证 `format_repr`（字符串缩略与转义）和 `format_table`（终端表格渲染）。

## 运行方式

```bash
pytest tests/utils -v
pytest tests/utils -k "clone or format" -v
```
