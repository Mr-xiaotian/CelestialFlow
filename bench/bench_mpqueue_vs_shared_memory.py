from __future__ import annotations

import os
import struct
import time
from multiprocessing import (
    Process,
    Queue as MPQueue,
    Semaphore,
    Value,
    Lock,
    shared_memory,
    set_start_method,
)
from typing import Any, Iterable

from bench_utils import summarize


# =========================
# Config
# =========================

COUNT = 100_000
REPEAT = 3
PAYLOAD_MODE = "int"   # int | small | medium | large

# SharedMemory ring config
SLOT_COUNT = 1024

# Topologies to test
#   SPSC = single producer, single consumer
#   MPSC = multi producer, single consumer
#   SPMC = single producer, multi consumer
TOPOLOGIES = (
    ("SPSC", 1, 1),
    ("MPSC", 4, 1),
    ("SPMC", 1, 4),
)


# =========================
# Payload
# =========================

def make_payload(i: int, mode: str) -> bytes:
    if mode == "int":
        return struct.pack("<Q", i)
    if mode == "small":
        return f"item-{i}".encode("utf-8")
    if mode == "medium":
        return (f"{i}-" + ("x" * 128)).encode("utf-8")
    if mode == "large":
        return (f"{i}-" + ("x" * 4096)).encode("utf-8")
    raise ValueError(f"Unknown PAYLOAD_MODE: {mode}")


def payload_max_bytes(mode: str) -> int:
    if mode == "int":
        return 8
    if mode == "small":
        return 32
    if mode == "medium":
        return 160
    if mode == "large":
        return 4200
    raise ValueError(f"Unknown PAYLOAD_MODE: {mode}")


def checksum_of_payload_bytes(payload: bytes, mode: str) -> int:
    if mode == "int":
        return struct.unpack("<Q", payload)[0]
    return len(payload)


def expected_checksum(start: int, count: int, mode: str) -> int:
    if mode == "int":
        end = start + count - 1
        return (start + end) * count // 2
    # Payload lengths are deterministic: prefix is f"{i}-" (or f"item-{i}"),
    # plus a fixed suffix. Compute analytically instead of constructing payloads.
    total = 0
    for i in range(start, start + count):
        digits = len(str(i))
        if mode == "small":
            total += 5 + digits           # "item-{i}" encoded
        elif mode == "medium":
            total += digits + 1 + 128     # "{i}-" + "x"*128 encoded
        elif mode == "large":
            total += digits + 1 + 4096    # "{i}-" + "x"*4096 encoded
        else:
            raise ValueError(f"Unknown PAYLOAD_MODE: {mode}")
    return total


def split_counts(total: int, parts: int) -> list[int]:
    base = total // parts
    rem = total % parts
    return [base + (1 if i < rem else 0) for i in range(parts)]


def prefix_starts(counts: Iterable[int]) -> list[int]:
    starts: list[int] = []
    s = 0
    for c in counts:
        starts.append(s)
        s += c
    return starts


# =========================
# MPQueue workers
# =========================

def producer_mpqueue(q: MPQueue, start: int, count: int, mode: str) -> None:
    for i in range(start, start + count):
        q.put(make_payload(i, mode))


def consumer_mpqueue(q: MPQueue, count: int, mode: str, result_q: MPQueue) -> None:
    consumed = 0
    checksum = 0
    for _ in range(count):
        item = q.get()
        consumed += 1
        checksum += checksum_of_payload_bytes(item, mode)
    result_q.put((consumed, checksum))


# =========================
# SharedMemory ring workers
# Layout:
#   shm[0 .. slot_count * slot_size] : ring slots, each = [4B length][payload]
#
# Protocol:
#   producer:
#     1. acquire empty_slots      (blocks if ring is full)
#     2. with write_lock:
#          a. claim slot index
#          b. write payload into shm
#     3. full_slots.release()     (outside lock — just an atomic counter bump)
#   consumer:
#     1. acquire full_slots       (blocks until an item is available)
#     2. with read_lock:
#          a. claim slot index
#          b. read payload from shm
#     3. empty_slots.release()
#
# Holding write_lock across the payload write is necessary for correctness in
# MPSC: without it, two producers could race — one claims slot N and starts
# writing while another also claims slot N (if write_idx wraps) or the
# consumer reads a slot whose payload hasn't been fully written yet.
# The lock window is minimised by keeping full_slots.release() outside.
# =========================

def producer_shm_ring(
    shm_name: str,
    slot_count: int,
    slot_size: int,
    start: int,
    count: int,
    mode: str,
    write_idx: Any,
    write_lock: Any,
    empty_slots: Any,
    full_slots: Any,
) -> None:
    shm = shared_memory.SharedMemory(name=shm_name)
    buf = shm.buf
    try:
        for i in range(start, start + count):
            payload = make_payload(i, mode)
            n = len(payload)
            if n > slot_size - 4:
                raise RuntimeError(f"payload too large: {n} > {slot_size - 4}")

            empty_slots.acquire()
            with write_lock:
                slot = write_idx.value
                write_idx.value = (write_idx.value + 1) % slot_count
                base = slot * slot_size
                buf[base:base + 4] = struct.pack("<I", n)
                buf[base + 4:base + 4 + n] = payload
            # Signal outside the lock: consumer just needs to know *a* slot is
            # ready, not which one — it reads read_idx under its own lock.
            full_slots.release()
    finally:
        shm.close()


def consumer_shm_ring(
    shm_name: str,
    slot_count: int,
    slot_size: int,
    count: int,
    mode: str,
    read_idx: Any,
    read_lock: Any,
    empty_slots: Any,
    full_slots: Any,
    result_q: MPQueue,
) -> None:
    shm = shared_memory.SharedMemory(name=shm_name)
    buf = shm.buf
    consumed = 0
    checksum = 0
    try:
        for _ in range(count):
            full_slots.acquire()
            with read_lock:
                slot = read_idx.value
                read_idx.value = (read_idx.value + 1) % slot_count
                base = slot * slot_size
                n = struct.unpack("<I", bytes(buf[base:base + 4]))[0]
                payload = bytes(buf[base + 4:base + 4 + n])
            consumed += 1
            checksum += checksum_of_payload_bytes(payload, mode)
            empty_slots.release()
    finally:
        shm.close()

    result_q.put((consumed, checksum))


# =========================
# Benchmark runners
# =========================

def run_mpqueue_case(
    topology_name: str,
    producer_count: int,
    consumer_count: int,
    total_count: int,
    repeat: int,
    mode: str,
) -> list[float]:
    durations: list[float] = []
    producer_counts = split_counts(total_count, producer_count)
    consumer_counts = split_counts(total_count, consumer_count)
    producer_starts = prefix_starts(producer_counts)
    target_checksum = expected_checksum(0, total_count, mode)

    for _ in range(repeat):
        q = MPQueue()
        result_q = MPQueue()

        producers = [
            Process(
                target=producer_mpqueue,
                args=(q, producer_starts[i], producer_counts[i], mode),
            )
            for i in range(producer_count)
        ]
        consumers = [
            Process(
                target=consumer_mpqueue,
                args=(q, consumer_counts[i], mode, result_q),
            )
            for i in range(consumer_count)
        ]

        start = time.perf_counter()

        for p in producers:
            p.start()
        for c in consumers:
            c.start()

        for p in producers:
            p.join()
        for c in consumers:
            c.join()

        duration = time.perf_counter() - start
        durations.append(duration)

        total_consumed = 0
        total_checksum = 0
        for _ in range(consumer_count):
            consumed, checksum = result_q.get()
            total_consumed += consumed
            total_checksum += checksum

        if total_consumed != total_count:
            raise RuntimeError(
                f"MPQueue/{topology_name} consumed={total_consumed}, expected={total_count}"
            )
        if total_checksum != target_checksum:
            raise RuntimeError(
                f"MPQueue/{topology_name} checksum={total_checksum}, expected={target_checksum}"
            )

        q.close()
        result_q.close()

    return durations


def run_shared_memory_case(
    topology_name: str,
    producer_count: int,
    consumer_count: int,
    total_count: int,
    repeat: int,
    mode: str,
    slot_count: int,
) -> list[float]:
    durations: list[float] = []
    slot_size = 4 + payload_max_bytes(mode)
    shm_size = slot_count * slot_size
    producer_counts = split_counts(total_count, producer_count)
    consumer_counts = split_counts(total_count, consumer_count)
    producer_starts = prefix_starts(producer_counts)
    target_checksum = expected_checksum(0, total_count, mode)

    for _ in range(repeat):
        shm = shared_memory.SharedMemory(create=True, size=shm_size)
        try:
            result_q = MPQueue()

            write_idx = Value("i", 0)
            read_idx = Value("i", 0)
            write_lock = Lock()
            read_lock = Lock()
            empty_slots = Semaphore(slot_count)
            full_slots = Semaphore(0)

            producers = [
                Process(
                    target=producer_shm_ring,
                    args=(
                        shm.name,
                        slot_count,
                        slot_size,
                        producer_starts[i],
                        producer_counts[i],
                        mode,
                        write_idx,
                        write_lock,
                        empty_slots,
                        full_slots,
                    ),
                )
                for i in range(producer_count)
            ]

            consumers = [
                Process(
                    target=consumer_shm_ring,
                    args=(
                        shm.name,
                        slot_count,
                        slot_size,
                        consumer_counts[i],
                        mode,
                        read_idx,
                        read_lock,
                        empty_slots,
                        full_slots,
                        result_q,
                    ),
                )
                for i in range(consumer_count)
            ]

            start = time.perf_counter()

            for p in producers:
                p.start()
            for c in consumers:
                c.start()

            for p in producers:
                p.join()
            for c in consumers:
                c.join()

            duration = time.perf_counter() - start
            durations.append(duration)

            total_consumed = 0
            total_checksum = 0
            for _ in range(consumer_count):
                consumed, checksum = result_q.get()
                total_consumed += consumed
                total_checksum += checksum

            if total_consumed != total_count:
                raise RuntimeError(
                    f"SharedMemory/{topology_name} consumed={total_consumed}, expected={total_count}"
                )
            if total_checksum != target_checksum:
                raise RuntimeError(
                    f"SharedMemory/{topology_name} checksum={total_checksum}, expected={target_checksum}"
                )

            result_q.close()
        finally:
            shm.close()
            shm.unlink()

    return durations


# =========================
# Main
# =========================

def main() -> None:
    print(f"PID={os.getpid()}")
    print("Running MPQueue vs SharedMemory benchmarks...")
    print(f"COUNT        = {COUNT}")
    print(f"REPEAT       = {REPEAT}")
    print(f"PAYLOAD_MODE = {PAYLOAD_MODE}")
    print(f"SLOT_COUNT   = {SLOT_COUNT}")

    for topology_name, producer_count, consumer_count in TOPOLOGIES:
        print(
            f"\n--- Topology: {topology_name} "
            f"(producers={producer_count}, consumers={consumer_count}) ---"
        )

        mpq = run_mpqueue_case(
            topology_name=topology_name,
            producer_count=producer_count,
            consumer_count=consumer_count,
            total_count=COUNT,
            repeat=REPEAT,
            mode=PAYLOAD_MODE,
        )
        summarize(f"MPQueue / {topology_name}", mpq, COUNT)

        shm = run_shared_memory_case(
            topology_name=topology_name,
            producer_count=producer_count,
            consumer_count=consumer_count,
            total_count=COUNT,
            repeat=REPEAT,
            mode=PAYLOAD_MODE,
            slot_count=SLOT_COUNT,
        )
        summarize(f"SharedMemory ring / {topology_name}", shm, COUNT)


if __name__ == "__main__":
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    main()
