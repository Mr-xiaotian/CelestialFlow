# Format Utility Tests (test_format.py)

> 📅 Last Updated: 2026/05/23

## Purpose
Validates the general formatting utilities in `celestialflow.utils.util_format`, ensuring data can be displayed in a readable and aesthetically pleasing way during terminal output, logging, and report generation.

## Core Test Targets
- `format_repr`: Intelligent string truncation and escaping utility.
- `format_table`: Character-terminal table generation utility.

## Key Test Flow
1. **String truncation (format_repr)**:
   - Validates that short strings remain unchanged.
   - Validates that long strings are truncated to `prefix...suffix` format, with total length meeting expectations.
   - Validates that special characters (newlines, backslashes) are correctly escaped to prevent breaking log format.
2. **Table formatting (format_table)**:
   - **Basic functionality**: Validates that a 2D list is converted to a bordered character table with automatically generated row and column indices.
   - **Custom configuration**: Validates rendering with custom row names, column names, and different alignment modes (left/right).
   - **Fault tolerance**: Validates that irregular nested lists (inconsistent column counts) are aligned via `fill_value`, and empty data returns a friendly prompt.

## Test Focus
- **Boundary alignment**: Ensures table borders remain aligned with content of varying lengths.
- **Escape safety**: Ensures characters like `\n` do not produce actual line breaks in repr mode.
- **Memory safety**: Test cases use small-scale data to ensure formatting logic does not cause performance issues due to recursion or complex loops.

## How to Run

```bash
# Run all
pytest tests/utils/test_format.py -v

# Run string truncation tests only
pytest tests/utils/test_format.py -k "repr" -v

# Run table formatting tests only
pytest tests/utils/test_format.py -k "table" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestFormatUtils` | ~0.1s (pure string processing) |

## Important Details
- The table formatting algorithm automatically calculates the maximum width of each column.
- `test_format_repr_truncation` validates the proportional distribution of the truncation logic.

## Notes
- These utilities are primarily used for CLI tooling and internal debug logging.
- Related implementation is in `src/celestialflow/utils/util_format.py`.
