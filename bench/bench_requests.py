import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# 测试配置
TEST_URL = "https://httpbin.org/get"  # 使用httpbin作为测试目标
NUM_REQUESTS = 50  # 每个测试的请求次数
CONCURRENT_WORKERS = 10  # 并发数
TIMEOUT = 30  # 超时时间


def test_without_session(url, num_requests):
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


def test_with_session(url, num_requests):
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


def test_concurrent_without_session(url, num_requests, workers):
    """并发测试 - 不使用Session"""

    def make_request(i):
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


def test_concurrent_with_session(url, num_requests, workers):
    """并发测试 - 每个线程独立Session"""

    def make_request(i):
        start = time.perf_counter()
        try:
            with requests.Session() as session:
                response = session.get(url, timeout=TIMEOUT)
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


def print_stats(label, times):
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
    print("=" * 60)
    print("Requests Session Performance Benchmark")
    print("=" * 60)
    print(f"Target URL: {TEST_URL}")
    print(f"Requests per test: {NUM_REQUESTS}")
    print(f"Concurrent workers: {CONCURRENT_WORKERS}")
    print("-" * 60)

    print("\n[1/4] Sequential - no session")
    print_stats("no session", test_without_session(TEST_URL, NUM_REQUESTS))

    print("\n[2/4] Sequential - with session")
    print_stats("with session", test_with_session(TEST_URL, NUM_REQUESTS))

    print("\n[3/4] Concurrent - no session")
    print_stats(
        "concurrent no session",
        test_concurrent_without_session(TEST_URL, NUM_REQUESTS, CONCURRENT_WORKERS),
    )

    print("\n[4/4] Concurrent - per-thread session")
    print_stats(
        "concurrent per-thread session",
        test_concurrent_with_session(TEST_URL, NUM_REQUESTS, CONCURRENT_WORKERS),
    )
