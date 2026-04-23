# test_utils.py Test Utility Documentation

> 📅 Last updated: 2026/04/22

## Test Purpose

`test_utils.py` is the shared utility library for the test suite, providing unified test functions, data generators, and helper classes for unit tests and demo tests. All test task functions are **pure functions or controlled side-effect functions**, ensuring predictable and repeatable test behavior.

## Test Scope

### 1. General Computation Functions
Mathematical functions for validating the framework's core computation logic:

| Function | Description | Characteristics |
|----------|-------------|-----------------|
| `fibonacci(n)` | Recursive Fibonacci | Raises `ValueError` when `n <= 0`, used for testing exception retry |
| `fibonacci_async(n)` | Async recursive Fibonacci | Validates `async` execution mode |
| `no_op(n)` | Identity function | No computation overhead, used as benchmark control |
| `sum_int(*num)` | Integer sum | Validates multi-argument unpacking (`unpack_task_args=True`) |
| `add_one(num)` | Add one | Most basic linear transformation |
| `sqrt(num)` | Square root | Floating-point arithmetic validation |
| `square(x)` | Square | Contains `sleep(1)` delay, simulates time-consuming tasks |

### 2. Arithmetic Functions with Exception Boundaries

| Function | Trigger Condition | Exception Type |
|----------|-------------------|----------------|
| `add_offset(x, offset=10)` | `x > 30` | `ValueError` |
| `add_5` / `add_10` / `add_15`, etc. | Same as above (different offsets) | `ValueError` |

These functions are used to validate:
- Exception capture and statistics
- Retry mechanism (configured to retry on `ValueError`)
- Data flow continuity under partial failure scenarios

### 3. Sleep Variants

| Function | Description |
|----------|-------------|
| `sleep_1(n)` | Synchronous 1-second delay |
| `sleep_1_async(n)` | Asynchronous 1-second delay |
| `add_one_sleep(n)` | 1-second delay then add one, with multi-condition exceptions |

### 4. URL Processing Functions (for demo_stages)

Function family simulating web crawler workflows:
- `generate_urls_sleep` / `log_urls_sleep` / `download_sleep` / `parse_sleep`
- Each function contains 4-6 seconds of random delay, simulating I/O-intensive tasks
- `download_to_file` performs real HTTP requests using `requests`

### 5. Special Classes

#### `RouterWrapper`
Routing wrapper for `TaskRouter` tests:
- Even numbers route to `a_tag`
- Odd numbers route to `b_tag`
- Must set `__name__` attribute to satisfy framework reflection requirements

## Potential Issues and Notes

### 1. Functions with `sleep` Slow Down Tests
`square`, `add_offset`, `sleep_1`, and similar functions contain hardcoded `sleep(1)` or random 4-6 second delays. Avoid using these functions directly in unit tests; use delay-free functions like `add_one` or `double` instead.

**Solution**:
- Unit test files (e.g., `test_executor.py`) define independent fast functions internally
- Demo tests (e.g., `demo_structure.py`) use delayed functions to simulate real workloads

### 2. `fibonacci` Recursion Depth
`fibonacci(32)` already involves approximately 2 million recursive calls, which may cause:
- Python recursion depth limit (default 1000)
- Excessive test execution time

**Recommendation**: Use only small values of `n <= 10` in unit tests.

### 3. Network Dependency of `download_to_file`
This function makes real HTTP requests, with the following risks:
- Target URL becoming invalid, causing test failure
- Network fluctuations causing timeouts
- Local filesystem permission issues (`/tmp/` path may not exist on Windows)

**Recommendation**: Use only in demo environments; unit tests should use `responses` or `httpx.MockTransport` for mocking.

### 4. Non-determinism of `random`
`generate_urls` uses `random.randint(1, 4)` to generate a random number of URLs, resulting in:
- Different task counts on each run
- Difficulty making precise assertions on success/failure counts

**Recommendation**: If precise assertions are needed, set a random seed before testing: `random.seed(42)`.

## How to Run

This file does not contain test cases itself; it is used as an imported shared module:
```python
from tests.test_utils import add_one, fibonacci
```

## Related Files

- `tests/test_executor.py`: Uses fast functions like `add_one`, `double`
- `tests/demo_executor.py`: Uses demo functions like `fibonacci`, `sleep_1`
- `tests/demo_stages.py`: Uses URL processing functions and `RouterWrapper`
