# Formatting Utility Tests (test_format.py)

> Last Updated: 2026/05/23

## Purpose
Validates the general formatting helpers in `celestialflow.utils.util_format`, ensuring data is displayed in a readable and polished way in terminal output, logs, and reports.

## Key Test Objects
- `format_repr`: Smart string truncation and escaping helper.
- `format_table`: Text-terminal table generator.

## Key Test Flow
1. **String truncation (`format_repr`)**:
   - Verifies that short strings stay unchanged.
   - Verifies that long strings are truncated into a `prefix...suffix` form and the total length matches expectations.
   - Verifies that special characters such as newlines and backslashes are escaped correctly so log formatting is not broken.
2. **Table formatting (`format_table`)**:
   - **Basic behavior**: Verifies that a two-dimensional list becomes a bordered text table with automatic row and column indexes.
   - **Custom configuration**: Verifies rendering with custom row names, custom column names, and different alignments such as `left` and `right`.
   - **Fault tolerance**: Verifies that ragged nested lists are padded with `fill_value` and that empty input returns a friendly message.

## Test Focus
- **Border alignment**: Ensures table borders stay aligned with content of different widths.
- **Escape safety**: Ensures characters like `\\n` do not create real line breaks in repr mode.
- **Memory safety**: Uses small test data so formatting logic does not run into recursive or looping performance issues.

## How to Run

```bash
# Run all tests
pytest tests/utils/test_format.py -v

# Run string-truncation tests only
pytest tests/utils/test_format.py -k "repr" -v

# Run table-formatting tests only
pytest tests/utils/test_format.py -k "table" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestFormatUtils` | ~0.1s (pure string processing) |

## Important Details
- The table formatter automatically computes the maximum width for each column.
- `test_format_repr_truncation` verifies the proportional split used by the truncation logic.

## Notes
- These helpers are mainly used by the CLI toolchain and internal debugging logs.
- Related implementation: `src/celestialflow/utils/util_format.py`.

