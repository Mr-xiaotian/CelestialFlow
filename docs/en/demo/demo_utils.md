# demo_utils.py Utility Documentation

> 📅 Last updated: 2026/04/22

## Purpose

Provides shared test functions and helper classes for the demo scripts in the `demo/` directory. The content is largely identical to `tests/test_utils.py` and serves as a dedicated utility library for demo code.

## Content Categories

### General Computation Functions
- `fibonacci` / `fibonacci_async`: Recursive Fibonacci (with exception boundaries)
- `no_op` / `sum_int` / `add_one` / `sqrt`: Basic arithmetic operations
- `square` / `add_offset` / `add_5` / `add_10`, etc.: Simulated time-consuming tasks with 1-second sleep
- `neuron_activation`: Sigmoid activation function (simulating ML inference)

### Sleep Variants
- `sleep_1` / `sleep_1_async`: Pure 1-second delay

### Arithmetic with Sleep (for demo_structure)
- `operate_sleep` / `operate_sleep_A~E`: Binary operations with 1-second delay
- `add_one_sleep`: Includes multi-condition exception boundaries (`n>30`, `n==0`, `n is None`)

### URL Processing Functions (for demo_stages)
- `generate_urls_sleep` / `log_urls_sleep` / `download_sleep` / `parse_sleep`
- `download_to_file`: Real HTTP download to local file

### Special Classes
- `RouterWrapper`: Routing wrapper for `TaskRouter` demos

## Relationship with tests/test_utils.py

The two files have nearly identical content. This is likely a historical artifact from when demo code was separated from test code and a copy was retained. When maintaining, it is recommended to keep both in sync or consider extracting common utilities into a standalone module under `celestialflow/utils/`.

## Potential Issues

1. **Duplication with tests/test_utils.py**: Modifying one file without updating the other can lead to divergent behavior between demos and unit tests.
2. **Hardcoded Windows paths**: `download_to_file` replaces the `/tmp/` path with `X:/Download/...`, which will fail in non-Windows environments.
3. **`requests` network dependency**: `download_to_file` requires external network access and is unavailable in isolated network environments.

## How to Run

This is a shared module and is not run directly:
```python
from demo_utils import fibonacci, sleep_1, RouterWrapper
```

## Dependencies

- `requests`
