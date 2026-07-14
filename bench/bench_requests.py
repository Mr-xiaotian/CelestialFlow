import argparse
import os
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# 测试配置
DEFAULT_BENCH_URL = "http://127.0.0.1:5005/api/pull_server_state"
NUM_REQUESTS = 50  # 每个测试的请求次数
CONCURRENT_WORKERS = 10  # 并发数
TIMEOUT = 30  # 超时时间


def parse_args() -> argparse.Namespace:
    """解析 bench 命令行参数。"""
    parser = argparse.ArgumentParser(
        description="Benchmark requests Session reuse with a configurable HTTP target."
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("CELESTIALFLOW_BENCH_URL", DEFAULT_BENCH_URL),
        help=(
            "Benchmark target URL. Defaults to CELESTIALFLOW_BENCH_URL or "
            f"{DEFAULT_BENCH_URL}."
        ),
    )
    return parser.parse_args()


def bench_without_session(url: str, num_requests: int) -> list[float]:
    """不使用Session，每次新建连接"""
    times = []
    for i in range(num_requests):
        start = time.perf_counter()
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            times.append(time.perf_counter() - start)
        except Exception as e:
            print(f"Request {i} failed: {e}")
    return times


def bench_with_session(url: str, num_requests: int) -> list[float]:
    """使用Session复用连接"""
    session = requests.Session()
    times = []
    for i in range(num_requests):
        start = time.perf_counter()
        try:
            response = session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            times.append(time.perf_counter() - start)
        except Exception as e:
            print(f"Request {i} failed: {e}")
    session.close()
    return times


def bench_concurrent_without_session(
    url: str, num_requests: int, workers: int
) -> list[float]:
    """并发测试 - 不使用Session"""

    def make_request(i: int) -> float | None:
        start = time.perf_counter()
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return time.perf_counter() - start
        except Exception as e:
            print(f"Request {i} failed: {e}")
            return None

    times = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(make_request, i) for i in range(num_requests)]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                times.append(result)
    return times


def bench_concurrent_with_session(
    url: str, num_requests: int, workers: int
) -> list[float]:
    """并发测试 - 每个线程独立Session"""
    thread_local = threading.local()
    created_sessions: list[requests.Session] = []
    sessions_lock = threading.Lock()

    def get_thread_session() -> requests.Session:
        session = getattr(thread_local, "session", None)
        if session is None:
            session = requests.Session()
            thread_local.session = session
            with sessions_lock:
                created_sessions.append(session)
        return session

    def make_request(i: int) -> float | None:
        start = time.perf_counter()
        try:
            session = get_thread_session()
            response = session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return time.perf_counter() - start
        except Exception as e:
            print(f"Request {i} failed: {e}")
            return None

    times = []
    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    times.append(result)
    finally:
        for session in created_sessions:
            session.close()
    return times


def print_stats(label: str, times: list[float]) -> None:
    """打印一组耗时数据的统计摘要。"""
    if not times:
        print(f"{label}: no successful requests")
        return
    print(f"{label} ({len(times)} requests):")
    print(f"  mean:   {statistics.mean(times) * 1000:.1f} ms")
    print(f"  median: {statistics.median(times) * 1000:.1f} ms")
    print(
        f"  stdev:  {statistics.stdev(times) * 1000:.1f} ms"
        if len(times) > 1
        else "  stdev:  n/a"
    )
    print(f"  min:    {min(times) * 1000:.1f} ms")
    print(f"  max:    {max(times) * 1000:.1f} ms")


if __name__ == "__main__":
    args = parse_args()

    print("=" * 60)
    print("Requests Session Performance Benchmark")
    print("=" * 60)
    print(f"Target URL: {args.url}")
    print(
        "Tip: default target is the local benchmark endpoint. "
        "Override with --url or CELESTIALFLOW_BENCH_URL if needed."
    )
    print(f"Requests per test: {NUM_REQUESTS}")
    print(f"Concurrent workers: {CONCURRENT_WORKERS}")
    print("-" * 60)

    print("\n[1/4] Sequential - no session")
    print_stats("no session", bench_without_session(args.url, NUM_REQUESTS))

    print("\n[2/4] Sequential - with session")
    print_stats("with session", bench_with_session(args.url, NUM_REQUESTS))

    print("\n[3/4] Concurrent - no session")
    print_stats(
        "concurrent no session",
        bench_concurrent_without_session(args.url, NUM_REQUESTS, CONCURRENT_WORKERS),
    )

    print("\n[4/4] Concurrent - per-thread session")
    print_stats(
        "concurrent per-thread session",
        bench_concurrent_with_session(args.url, NUM_REQUESTS, CONCURRENT_WORKERS),
    )
