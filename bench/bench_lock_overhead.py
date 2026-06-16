from __future__ import annotations

import multiprocessing as mp
import queue as py_queue
import statistics
import time
from collections.abc import Sequence
from ctypes import c_longlong
from typing import Any

INT_OPS = 100_000
MPQUEUE_ITEMS = 20_000
PARALLEL_WORKERS = 4
REPEAT = 2


def split_evenly(total: int, parts: int) -> list[int]:
    base = total // parts
    remainder = total % parts
    return [base + (1 if i < remainder else 0) for i in range(parts)]


def increment_counter_worker(
    counter: Any,
    iterations: int,
    use_lock: bool,
) -> None:
    if use_lock:
        lock = counter.get_lock()
        for _ in range(iterations):
            with lock:
                counter.value += 1
        return

    for _ in range(iterations):
        counter.value += 1


def queue_put_worker(
    q: Any,
    start_value: int,
    count: int,
    use_lock: bool,
    op_lock: Any | None,
) -> None:
    if use_lock and op_lock is not None:
        for i in range(count):
            with op_lock:
                q.put(start_value + i)
        return

    for i in range(count):
        q.put(start_value + i)


def queue_get_worker(
    q: Any,
    use_lock: bool,
    op_lock: Any | None,
    result_queue: Any,
) -> None:
    checksum = 0
    consumed = 0
    while True:
        try:
            if use_lock and op_lock is not None:
                with op_lock:
                    item = q.get(timeout=0.05)
            else:
                item = q.get(timeout=0.05)
        except py_queue.Empty:
            continue

        if item is None:
            break
        checksum += int(item)
        consumed += 1
    result_queue.put((consumed, checksum))


def bench_shared_int_serial(ctx: mp.context.BaseContext, use_lock: bool) -> dict[str, Any]:
    counter = ctx.Value(c_longlong, 0, lock=use_lock)
    start = time.perf_counter()
    increment_counter_worker(counter, INT_OPS, use_lock)
    elapsed = time.perf_counter() - start
    return {
        "elapsed": elapsed,
        "final": int(counter.value),
        "expected": INT_OPS,
    }


def bench_shared_int_parallel(
    ctx: mp.context.BaseContext,
    use_lock: bool,
) -> dict[str, Any]:
    counter = ctx.Value(c_longlong, 0, lock=use_lock)
    chunks = split_evenly(INT_OPS, PARALLEL_WORKERS)
    processes = [
        ctx.Process(target=increment_counter_worker, args=(counter, chunk, use_lock))
        for chunk in chunks
    ]
    start = time.perf_counter()
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    elapsed = time.perf_counter() - start
    return {
        "elapsed": elapsed,
        "final": int(counter.value),
        "expected": sum(chunks),
    }


def bench_mpqueue_serial(ctx: mp.context.BaseContext, use_lock: bool) -> dict[str, Any]:
    q = ctx.Queue()
    op_lock = ctx.Lock() if use_lock else None

    start_put = time.perf_counter()
    for i in range(MPQUEUE_ITEMS):
        if use_lock and op_lock is not None:
            with op_lock:
                q.put(i)
        else:
            q.put(i)
    put_elapsed = time.perf_counter() - start_put

    checksum = 0
    start_get = time.perf_counter()
    for _ in range(MPQUEUE_ITEMS):
        if use_lock and op_lock is not None:
            with op_lock:
                item = q.get()
        else:
            item = q.get()
        checksum += int(item)
    get_elapsed = time.perf_counter() - start_get

    return {
        "put_elapsed": put_elapsed,
        "get_elapsed": get_elapsed,
        "total_elapsed": put_elapsed + get_elapsed,
        "checksum": checksum,
        "expected_checksum": MPQUEUE_ITEMS * (MPQUEUE_ITEMS - 1) // 2,
    }


def bench_mpqueue_parallel(ctx: mp.context.BaseContext, use_lock: bool) -> dict[str, Any]:
    q = ctx.Queue()
    result_queue = ctx.Queue()
    op_lock = ctx.Lock() if use_lock else None
    chunks = split_evenly(MPQUEUE_ITEMS, PARALLEL_WORKERS)

    producers: list[mp.Process] = []
    offset = 0
    for chunk in chunks:
        producers.append(
            ctx.Process(
                target=queue_put_worker,
                args=(q, offset, chunk, use_lock, op_lock),
            )
        )
        offset += chunk

    consumers = [
        ctx.Process(
            target=queue_get_worker,
            args=(q, use_lock, op_lock, result_queue),
        )
        for chunk in chunks
    ]

    for process in consumers:
        process.start()

    start_total = time.perf_counter()
    for process in producers:
        process.start()
    for process in producers:
        process.join()
    put_elapsed = time.perf_counter() - start_total

    for _ in consumers:
        if use_lock and op_lock is not None:
            with op_lock:
                q.put(None)
        else:
            q.put(None)

    for process in consumers:
        process.join()
    total_elapsed = time.perf_counter() - start_total

    consumed = 0
    checksum = 0
    for _ in consumers:
        worker_consumed, worker_checksum = result_queue.get()
        consumed += int(worker_consumed)
        checksum += int(worker_checksum)

    return {
        "put_elapsed": put_elapsed,
        "get_elapsed": max(total_elapsed - put_elapsed, 0.0),
        "total_elapsed": total_elapsed,
        "consumed": consumed,
        "expected_consumed": MPQUEUE_ITEMS,
        "checksum": checksum,
        "expected_checksum": MPQUEUE_ITEMS * (MPQUEUE_ITEMS - 1) // 2,
    }


def mean(values: Sequence[float]) -> float:
    return statistics.mean(values)


def pstdev(values: Sequence[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def run_int_case(
    ctx: mp.context.BaseContext,
    mode: str,
    use_lock: bool,
) -> dict[str, Any]:
    samples: list[float] = []
    finals: list[int] = []
    expected = 0

    for _ in range(REPEAT):
        if mode == "serial":
            result = bench_shared_int_serial(ctx, use_lock)
        else:
            result = bench_shared_int_parallel(ctx, use_lock)
        samples.append(float(result["elapsed"]))
        finals.append(int(result["final"]))
        expected = int(result["expected"])

    correct_rounds = sum(1 for final in finals if final == expected)
    return {
        "mode": mode,
        "lock": "lock" if use_lock else "no_lock",
        "mean": mean(samples),
        "std": pstdev(samples),
        "final": finals[-1],
        "expected": expected,
        "correct_rounds": f"{correct_rounds}/{REPEAT}",
    }


def run_queue_case(
    ctx: mp.context.BaseContext,
    mode: str,
    use_lock: bool,
) -> dict[str, Any]:
    put_samples: list[float] = []
    get_samples: list[float] = []
    total_samples: list[float] = []
    expected_checksum = 0
    correct_rounds = 0

    for _ in range(REPEAT):
        if mode == "serial":
            result = bench_mpqueue_serial(ctx, use_lock)
        else:
            result = bench_mpqueue_parallel(ctx, use_lock)
        put_samples.append(float(result["put_elapsed"]))
        get_samples.append(float(result["get_elapsed"]))
        total_samples.append(float(result["total_elapsed"]))
        expected_checksum = int(result["expected_checksum"])
        if (
            int(result["checksum"]) == expected_checksum
            and int(result.get("consumed", MPQUEUE_ITEMS)) == int(result.get("expected_consumed", MPQUEUE_ITEMS))
        ):
            correct_rounds += 1

    return {
        "mode": mode,
        "lock": "lock" if use_lock else "no_lock",
        "put_mean": mean(put_samples),
        "get_mean": mean(get_samples),
        "total_mean": mean(total_samples),
        "total_std": pstdev(total_samples),
        "correct_rounds": f"{correct_rounds}/{REPEAT}",
    }


def print_shared_int_results(rows: list[dict[str, Any]]) -> None:
    print("\n=== Shared Int Benchmark ===")
    print(
        f"{'Mode':<10} {'Lock':<10} {'Mean(s)':>10} {'Std(s)':>10} "
        f"{'Final(last)':>12} {'Expected':>10} {'Correct':>10}"
    )
    print("-" * 76)
    for row in rows:
        print(
            f"{row['mode']:<10} {row['lock']:<10} {row['mean']:>10.4f} "
            f"{row['std']:>10.4f} {row['final']:>12} {row['expected']:>10} "
            f"{row['correct_rounds']:>10}"
        )


def print_mpqueue_results(rows: list[dict[str, Any]]) -> None:
    print("\n=== MPQueue Benchmark ===")
    print(
        f"{'Mode':<10} {'Lock':<10} {'Put(s)':>10} {'Get(s)':>10} "
        f"{'Total(s)':>10} {'Std(s)':>10} {'Correct':>10}"
    )
    print("-" * 72)
    for row in rows:
        print(
            f"{row['mode']:<10} {row['lock']:<10} {row['put_mean']:>10.4f} "
            f"{row['get_mean']:>10.4f} {row['total_mean']:>10.4f} "
            f"{row['total_std']:>10.4f} {row['correct_rounds']:>10}"
        )


def main() -> None:
    ctx = mp.get_context("spawn")

    print("=" * 88)
    print("Lock Overhead Benchmark")
    print("=" * 88)
    print(f"INT_OPS          = {INT_OPS}")
    print(f"MPQUEUE_ITEMS    = {MPQUEUE_ITEMS}")
    print(f"PARALLEL_WORKERS = {PARALLEL_WORKERS}")
    print(f"REPEAT           = {REPEAT}")

    int_rows = [
        run_int_case(ctx, "serial", False),
        run_int_case(ctx, "serial", True),
        run_int_case(ctx, "parallel", False),
        run_int_case(ctx, "parallel", True),
    ]
    print_shared_int_results(int_rows)

    queue_rows = [
        run_queue_case(ctx, "serial", False),
        run_queue_case(ctx, "serial", True),
        run_queue_case(ctx, "parallel", False),
        run_queue_case(ctx, "parallel", True),
    ]
    print_mpqueue_results(queue_rows)


if __name__ == "__main__":
    main()
