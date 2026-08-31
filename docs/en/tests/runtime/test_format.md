# Format Utility Tests (test_format.py)

> 📅 Last Updated: 2026/08/12

## Purpose
Validates the `format_repr` and `format_table` formatting functions in `celestialflow.runtime.util_format`, ensuring correctness of string truncation representation and table rendering output.

## Core Test Objects
- `format_repr`: Truncates overly long strings using the "first 2/3 + ... + last 1/3" rule, and escapes special characters.
- `format_table`: Renders 2D data as a bordered ASCII table, with support for custom row/column names, fill values, and alignment.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goal |
|--------|--------|---------|
| `TestUtilFormat` | 9 | `format_repr` (no truncation / truncation / boundary / escaping); `format_table` (empty data / basic / custom names / fill values / alignment) |

## Key Test Scenarios

### `format_repr` — String Truncation Representation
1. **No truncation**: Short text is returned as-is; no processing when the length does not exceed the truncation threshold.
2. **Truncation**: Overly long text is truncated using the first 2/3 + `...` + last 1/3 rule, with the total length not exceeding `max_len + 3`.
3. **Boundary**: The first/last characters are correctly preserved at the minimum truncation length (`max_len=3`).
4. **Escaping**: Special characters (`\n`, `\`, etc.) are correctly escaped into visible form.

### `format_table` — Table Rendering
1. **Empty data**: An empty list returns the prompt `"表格数据为空！"` ("Table data is empty!").
2. **Basic table**: 2D data is automatically rendered as a numbered table with default column names A, B, C, ...
3. **Custom names**: Supports `row_names` and `column_names` parameters to customize row/column labels.
4. **Fill values**: When row lengths are inconsistent, `fill_value` is used to pad missing cells.
5. **Alignment**: Supports `align="left"` and `align="right"` to control column alignment.

## How to Run

```bash
# Run all
pytest tests/runtime/test_format.py -v

# Run format_repr tests only
pytest tests/runtime/test_format.py -k "repr" -v

# Run format_table tests only
pytest tests/runtime/test_format.py -k "table" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestUtilFormat` | < 0.1s (pure string operations) |

## Important Details
- The `format_repr` truncation algorithm keeps the first 2/3 of the characters, followed by `...`, then the last 1/3 of the characters.
- In `format_table`, the first column is fixed as the `#` row-number column and is mutually exclusive with `row_names`.
- Column alignment is implemented by controlling the direction of inner padding in the header and data.

## Notes
- The test code is located at `tests/runtime/test_format.py`, and the corresponding implementation is at `src/celestialflow/runtime/util_format.py`.
