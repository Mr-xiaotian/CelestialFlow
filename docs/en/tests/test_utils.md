# test_utils.py Test Utilities Documentation

> 📅 Last Updated: 2026/04/22

## Test Objective

`test_utils.py` is a shared utility library for the test suite, providing unified test functions, data generators, and helper classes for unit tests and demo tests. All test task functions are **pure functions or controlled side-effect functions**, ensuring predictable and repeatable test behavior.

## Test Scope

### 1. General Computation Functions
Mathematical functions for validating framework core computation logic:

| Function | Description | Characteristics |
|----------|-------------|-----------------|
| `fibonacci(n)` | Recursive Fibonacci | Throws `ValueError` when input `n <= 0`, used for testing exception retry |
| `fibonacci_async(n)` | Async recursive Fibonacci | Validates `async` execution mode |
| `no_op(n)` | Identity function | No computation overhead, used as benchmark control |
| `sum_int(*num)` | Integer sum | Validates multi-argument unpacking (`unpack_task_args=True`) |
| `add_one(num)` | Add one | Most basic linear transformation |
| `sqrt(num)` | Square root | Floating-point arithmetic validation |
| `square(x)` | Square | Contains `sleep(1)` delay, simulates time-consuming tasks |

### 2. Functions with Exception Boundaries

| Function | Trigger Condition | Exception Type |
|----------|-------------------|----------------|
| `add_offset(x, offset=10)` | `x > 30` | `ValueError` |
| `add_5` / `add_10` / `add_15`, etc. | Same as above (different offsets) | `ValueError` |

These functions are used to validate:
- Exception capture and statistics
- Retry mechanism (retry configured for `ValueError`)
- Data flow continuity under partial failure scenarios

### 3. Sleep Variants

| Function | Description |
|----------|-------------|
| `sleep_1(n)` | Synchronous 1-second delay |
| `sleep_1_async(n)` | Asynchronous 1-second delay |
| `add_one_sleep(n)` | 1-second delay then add one, with multi-condition exceptions |

### 4. URL Processing Functions (demo_stages specific)

Function family simulating crawler workflows:
- `generate_urls_sleep` / `log_urls_sleep` / `download_sleep` / `parse_sleep`
- Each function contains 4-6 second random delays, simulating I/O-intensive tasks
- `download_to_file` uses `requests` for real HTTP requests

### 5. Special Classes

#### `RouterWrapper`
Routing wrapper for `TaskRouter` testing:
- Even numbers route to `a_tag`
- Odd numbers route to `b_tag`
- Must set `__name__` attribute to satisfy framework reflection requirements

## Potential Issues and Notes

### 1. Functions with `sleep` Slow Down Tests
`square`, `add_offset`, `sleep_1`, and similar functions contain hardcoded `sleep(1)` or random 4-6 second delays. These functions should be avoided in unit tests; use `add_one`, `double`, and other delay-free functions instead.

**Solution**:
- Unit test files (e.g., `test_executor.py`) define independent fast functions internally
- Demo tests (e.g., `demo_structure.py`) use delay functions to simulate real workloads

### 2. `fibonacci` Recursion Depth
`fibonacci(32)` involves approximately 2 million recursive calls, which may cause:
- Python recursion depth limit (default 1000)
- Excessive test execution time

**Recommendation**: Only use small values `n <= 10` in unit tests.

### 3. Network Dependency of `download_to_file`
This function makes real HTTP requests, presenting the following risks:
- Target URL becoming invalid causes test failures
- Network fluctuations cause timeouts
- Local filesystem permission issues (`/tmp/` path may not exist on Windows)

**Recommendation**: Use only in demo environments; unit tests should use `responses` or `httpx.MockTransport` for mocking.

### 4. Non-determinism of `random`
`generate_urls` uses `random.randint(1, 4)` to generate a random number of URLs, resulting in:
- Different task counts per run
- Difficulty in making precise success/failure assertions

**Recommendation**: For precise assertions, set the random seed beforehand with `random.seed(42)`.

## How to Run

This file contains no test cases itself; it is used as an imported shared module:
```python
from tests.test_utils import add_one, fibonacci
```

## Related Files

- `tests/test_executor.py`: Uses `add_one`, `double`, and other fast functions
- `tests/demo_executor.py`: Uses `fibonacci`, `sleep_1`, and other demo functions
- `tests/demo_stages.py`: Uses URL processing functions and `RouterWrapper`
