import tracemalloc
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def noop(x: Any) -> Any:
    return x


def dispatch_no_cleanup(task_count: int, max_workers: int) -> None:
    """futures 列表不清理，全部保留到最后"""
    pool = ThreadPoolExecutor(max_workers=max_workers)
    futures = []

    for i in range(task_count):
        futures.append(pool.submit(noop, i))

    for f in futures:
        f.result()

    pool.shutdown(wait=False)


def dispatch_with_cleanup(task_count: int, max_workers: int) -> None:
    """futures 列表定期清理已完成的 future"""
    pool = ThreadPoolExecutor(max_workers=max_workers)
    futures = []

    for i in range(task_count):
        futures.append(pool.submit(noop, i))
        if len(futures) >= max_workers * 2:
            futures = [f for f in futures if not f.done()]

    for f in futures:
        f.result()

    pool.shutdown(wait=False)


def measure(
    fn: Callable[[int, int], None], task_count: int, max_workers: int
) -> dict[str, float]:
    tracemalloc.start()

    t0 = time.perf_counter()
    fn(task_count, max_workers)
    elapsed = time.perf_counter() - t0

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "elapsed": elapsed,
        "peak_mb": peak / 1024 / 1024,
        "current_mb": current / 1024 / 1024,
    }


def main() -> None:
    scales = [10_000, 100_000, 500_000]
    max_workers = 20

    print(f"max_workers = {max_workers}\n")
    print(
        f"{'tasks':>10}  {'mode':<12}  {'elapsed':>8}  {'peak_MB':>8}  {'current_MB':>10}"
    )
    print("-" * 58)

    for task_count in scales:
        r1 = measure(dispatch_no_cleanup, task_count, max_workers)
        r2 = measure(dispatch_with_cleanup, task_count, max_workers)

        print(
            f"{task_count:>10,}  {'no_cleanup':<12}  "
            f"{r1['elapsed']:>7.3f}s  {r1['peak_mb']:>7.2f}  {r1['current_mb']:>10.2f}"
        )
        print(
            f"{' ':>10}  {'with_cleanup':<12}  "
            f"{r2['elapsed']:>7.3f}s  {r2['peak_mb']:>7.2f}  {r2['current_mb']:>10.2f}"
        )
        print()


if __name__ == "__main__":
    main()
