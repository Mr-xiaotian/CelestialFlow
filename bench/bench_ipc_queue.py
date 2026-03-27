from __future__ import annotations

import os
import time
from multiprocessing import (
    Manager,
    Pipe,
    Process,
    SimpleQueue,
    set_start_method,
)
from multiprocessing import (
    Queue as MPQueue,
)
from typing import Any, Callable

from bench_utils import summarize

# =========================
# Config
# =========================

COUNT = 100_000
REPEAT = 3


# payload mode:
#   "int"      -> 小对象
#   "small"    -> 小字符串
#   "medium"   -> 中等字符串
#   "large"    -> 大字符串
PAYLOAD_MODE = "int"


# =========================
# Payload factory
# =========================


def make_payload(i: int, mode: str) -> Any:
    if mode == "int":
        return i
    if mode == "small":
        return f"item-{i}"
    if mode == "medium":
        return f"{i}-" + ("x" * 128)
    if mode == "large":
        return f"{i}-" + ("x" * 4096)
    raise ValueError(f"Unknown PAYLOAD_MODE: {mode}")


# =========================
# Worker funcs: Queue-like
# =========================

_SENTINEL = None


def producer_queue(q, count: int, mode: str) -> None:
    for i in range(count):
        q.put(make_payload(i, mode))
    q.put(_SENTINEL)


def consumer_queue(q, result_q) -> None:
    consumed = 0
    checksum = 0

    while True:
        item = q.get()
        if item is _SENTINEL:
            break

        consumed += 1
        if isinstance(item, int):
            checksum += item
        else:
            checksum += len(item)

    result_q.put((consumed, checksum))


# =========================
# Worker funcs: Pipe
# =========================


def producer_pipe(conn, count: int, mode: str) -> None:
    try:
        for i in range(count):
            conn.send(make_payload(i, mode))
        conn.send(_SENTINEL)
    finally:
        conn.close()


def consumer_pipe(conn, result_q) -> None:
    consumed = 0
    checksum = 0

    try:
        while True:
            item = conn.recv()
            if item is _SENTINEL:
                break

            consumed += 1
            if isinstance(item, int):
                checksum += item
            else:
                checksum += len(item)
    finally:
        conn.close()

    result_q.put((consumed, checksum))


# =========================
# Checksum
# =========================


def expected_checksum(count: int, mode: str) -> int:
    if mode == "int":
        return count * (count - 1) // 2
    total = 0
    for i in range(count):
        total += len(make_payload(i, mode))
    return total


# =========================
# Benchmark helpers
# =========================


def run_queue_case(
    name: str,
    q_factory: Callable[[], Any],
    count: int,
    repeat: int,
    mode: str,
) -> None:
    durations: list[float] = []
    target_checksum = expected_checksum(count, mode)

    for _ in range(repeat):
        q = q_factory()
        result_q = MPQueue()

        p_prod = Process(target=producer_queue, args=(q, count, mode))
        p_cons = Process(target=consumer_queue, args=(q, result_q))

        start = time.perf_counter()

        p_prod.start()
        p_cons.start()

        p_prod.join()
        p_cons.join()

        duration = time.perf_counter() - start
        durations.append(duration)

        consumed, checksum = result_q.get()

        if consumed != count:
            raise RuntimeError(f"{name}: consumed={consumed}, expected={count}")
        if checksum != target_checksum:
            raise RuntimeError(
                f"{name}: checksum={checksum}, expected={target_checksum}"
            )

        result_q.close()

    summarize(name, durations, count)


def run_pipe_case(count: int, repeat: int, mode: str) -> None:
    durations: list[float] = []
    target_checksum = expected_checksum(count, mode)

    for _ in range(repeat):
        recv_conn, send_conn = Pipe(duplex=False)
        result_q = MPQueue()

        p_prod = Process(target=producer_pipe, args=(send_conn, count, mode))
        p_cons = Process(target=consumer_pipe, args=(recv_conn, result_q))

        start = time.perf_counter()

        p_prod.start()
        p_cons.start()

        # 父进程这边不参与通信，尽早关闭自己的句柄
        send_conn.close()
        recv_conn.close()

        p_prod.join()
        p_cons.join()

        duration = time.perf_counter() - start
        durations.append(duration)

        consumed, checksum = result_q.get()

        if consumed != count:
            raise RuntimeError(f"Pipe: consumed={consumed}, expected={count}")
        if checksum != target_checksum:
            raise RuntimeError(f"Pipe: checksum={checksum}, expected={target_checksum}")

        result_q.close()

    summarize("Pipe", durations, count)


def run_manager_queue_case(count: int, repeat: int, mode: str) -> None:
    durations: list[float] = []
    target_checksum = expected_checksum(count, mode)

    for _ in range(repeat):
        with Manager() as manager:
            q = manager.Queue()
            result_q = MPQueue()

            p_prod = Process(target=producer_queue, args=(q, count, mode))
            p_cons = Process(target=consumer_queue, args=(q, result_q))

            start = time.perf_counter()

            p_prod.start()
            p_cons.start()

            p_prod.join()
            p_cons.join()

            duration = time.perf_counter() - start
            durations.append(duration)

            consumed, checksum = result_q.get()

            if consumed != count:
                raise RuntimeError(
                    f"Manager().Queue: consumed={consumed}, expected={count}"
                )
            if checksum != target_checksum:
                raise RuntimeError(
                    f"Manager().Queue: checksum={checksum}, expected={target_checksum}"
                )

            result_q.close()

    summarize("Manager().Queue", durations, count)


# =========================
# Main
# =========================


def main() -> None:
    print(f"PID={os.getpid()}")
    print("Running real-world IPC benchmarks...")
    print(f"COUNT  = {COUNT}")
    print(f"REPEAT = {REPEAT}")
    print(f"PAYLOAD_MODE = {PAYLOAD_MODE}")

    run_queue_case(
        name="MPQueue",
        q_factory=MPQueue,
        count=COUNT,
        repeat=REPEAT,
        mode=PAYLOAD_MODE,
    )

    run_queue_case(
        name="SimpleQueue",
        q_factory=SimpleQueue,
        count=COUNT,
        repeat=REPEAT,
        mode=PAYLOAD_MODE,
    )

    run_pipe_case(
        count=COUNT,
        repeat=REPEAT,
        mode=PAYLOAD_MODE,
    )

    run_manager_queue_case(
        count=COUNT,
        repeat=REPEAT,
        mode=PAYLOAD_MODE,
    )


if __name__ == "__main__":
    # Windows/macOS 下更稳，行为也更统一
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    main()
