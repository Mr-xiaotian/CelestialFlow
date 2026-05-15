# UtilsDebug

> 📅 Last Updated: 2026/05/09

`utils/util_debug.py` provides debugging helper functions.

## Main Functions

- `find_unpickleable(obj)`: Checks whether an object can be pickled; prints diagnostic information on failure.

Commonly used to troubleshoot object serialization issues (e.g., when data needs to be passed across processes or persisted).
