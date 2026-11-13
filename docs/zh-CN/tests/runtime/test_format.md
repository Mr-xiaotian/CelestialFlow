# tests/runtime/test_format.py

> 📅 最后更新日期: 2026/11/13

## 作用
验证 `celestialflow.runtime.util_format` 中的 `format_repr` 和 `format_table` 两个格式化函数，确保字符串截断表示和表格渲染输出的正确性。

## 核心测试对象
- `format_repr`: 将超长字符串按"首 2/3 + ... + 尾 1/3"规则截断，并转义特殊字符。
- `format_table`: 将二维数据渲染为带边框的 ASCII 表格，支持自定义行列名称、填充值和对齐方式。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestUtilFormat` | 9 | `format_repr`（不截断/截断/边界/转义）；`format_table`（空数据/基本/自定义名称/填充值/对齐方式） |

## 关键测试场景

### `format_repr` — 字符串截断表示
1. **不截断**: 短文本原样返回，不超过截断长度时不处理。
2. **截断**: 超长文本按首 2/3 + `...` + 尾 1/3 规则截断；本用例 `max_len=30` 时结果为 33 个字符（`20 + 3 + 10`）。
3. **边界**: 最小截断长度（`max_len=3`）下正确保留首尾字符。
4. **转义**: 特殊字符（`\n`、`\` 等）被正确转义为可见形式。

### `format_table` — 表格渲染
1. **空数据**: 空列表返回 `"表格数据为空！"` 提示。
2. **基本表格**: 二维数据自动生成带序号的表格，列名默认 A、B、C...
3. **自定义名称**: 支持 `row_names` 和 `column_names` 参数定制行列标签。
4. **填充值**: 行长度不一致时用 `fill_value` 补齐缺失单元格。
5. **对齐方式**: 支持 `align="left"` 和 `align="right"` 控制列对齐。

## 运行方式

```bash
# 全部执行
uv run pytest tests/runtime/test_format.py -v

# 仅运行 format_repr 测试
uv run pytest tests/runtime/test_format.py -k "repr" -v

# 仅运行 format_table 测试
uv run pytest tests/runtime/test_format.py -k "table" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestUtilFormat` | < 0.1s（纯字符串操作） |

## 重要细节
- `format_repr` 的截断算法为：`segment_len = max(1, max_length // 3)`，取前 `2 * segment_len` 字符、`...`、后 `segment_len` 字符；`max_length <= 0` 或文本未超长时原样返回。
- 转义先于截断执行：反斜杠与换行分别变为 `\\`、`\n` 字面量，因此截断长度按转义后的字符串计算。
- `format_table` 首列固定为行号列（表头由 `index_header` 指定，默认 `#`），默认填入行索引，可用 `row_names` 覆盖该列的标签。
- `format_table` 的 `align` 还支持 `"center"`（实现中的第三种对齐函数），但测试只覆盖 `"left"` 与 `"right"`。
- 列对齐通过控制表头和数据中内边距的方向实现。

## 注意事项
- 测试代码位于 `tests/runtime/test_format.py`，对应实现位于 `src/celestialflow/runtime/util_format.py`。
- 同模块的 `cluster_by_value_sorted` 不在本测试文件覆盖范围内。
