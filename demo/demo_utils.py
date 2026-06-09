"""
Shared helper functions and classes used across test files.
"""

from __future__ import annotations

import asyncio
import math
import random
import re
from collections.abc import Iterable
from time import sleep
from typing import Any

import requests

# =========================
# 通用计算函数
# =========================


def fibonacci(n: Any) -> int:
    """同步版斐波那契 — 迭代 O(n)"""
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        prev, curr = 1, 1
        for _ in range(3, n + 1):
            prev, curr = curr, prev + curr
        return curr


async def fibonacci_async(n: Any) -> int:
    """异步版斐波那契 — 迭代 O(n)，每 8 轮出让事件循环"""
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        prev, curr = 1, 1
        for i in range(3, n + 1):
            prev, curr = curr, prev + curr
            if i % 8 == 0:
                await asyncio.sleep(0)
        return curr


def no_op(n: Any) -> Any:
    return n


def sum_int(num: Iterable[int]) -> int:
    return sum(num)


def add_one(num: Any) -> Any:
    return num + 1


def sqrt(num: float | int) -> float:
    return num**0.5


def square(x: Any) -> Any:
    sleep(1)
    return x * x


def add_offset(x: Any, offset: int = 10) -> Any:
    if x > 30:
        raise ValueError("Test error for greater than 30")
    sleep(1)
    return x + offset


def add_5(x: Any) -> Any:
    return add_offset(x, 5)


def add_10(x: Any) -> Any:
    return add_offset(x, 10)


def add_15(x: Any) -> Any:
    return add_offset(x, 15)


def add_20(x: Any) -> Any:
    return add_offset(x, 20)


def add_25(x: Any) -> Any:
    return add_offset(x, 25)


def neuron_activation(x: float | int) -> float:
    if not isinstance(x, (int, float)):
        raise ValueError("Invalid input type")
    sleep(1)
    return 1 / (1 + math.exp(-x))


# =========================
# sleep 变体
#   sleep_1       — 纯延迟，有返回值（demo_executor 用）
#   sleep_1_async — 纯延迟，有返回值的异步版本（demo_executor 用）
# =========================


def sleep_1(n: Any) -> Any:
    sleep(1)
    return n


async def sleep_1_async(n: Any) -> Any:
    await asyncio.sleep(1)
    return n


# =========================
# 带 sleep 的运算函数（demo_structure 用）
# =========================


def operate_sleep(a: Any, b: Any) -> tuple[Any, Any]:
    sleep(1)
    return a + b, a * b


def operate_sleep_A(a: Any, b: Any) -> tuple[Any, Any]:
    return operate_sleep(a, b)


def operate_sleep_B(a: Any, b: Any) -> tuple[Any, Any]:
    return operate_sleep(a, b)


def operate_sleep_C(a: Any, b: Any) -> tuple[Any, Any]:
    return operate_sleep(a, b)


def operate_sleep_D(a: Any, b: Any) -> tuple[Any, Any]:
    return operate_sleep(a, b)


def operate_sleep_E(a: Any, b: Any) -> tuple[Any, Any]:
    return operate_sleep(a, b)


def add_one_sleep(n: Any) -> Any:
    sleep(1)
    if n > 30:
        raise ValueError("Test error for greater than 30")
    elif n == 0:
        raise ValueError("Test error for 0")
    elif n is None:
        raise ValueError("Test error for None")
    return n + 1


# =========================
# URL 处理函数（demo_stages 用）
# =========================


def generate_urls(x: Any) -> tuple[str, ...]:
    return tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4))])


def log_urls(data: tuple[str, ...]) -> str:
    if data == ("url_1_0", "url_1_1"):
        raise ValueError("Test error in ('url_1_0', 'url_1_1')")
    return f"Logged({data})"


def download(url: str) -> str:
    if "url_3" in url:
        raise ValueError("Test error in url_3_*")
    return f"Downloaded({url})"


def parse(url: str) -> int:
    num_list = re.findall(r"\d+", url)
    parse_num = int("".join(num_list))
    if parse_num % 2 == 0:
        raise ValueError("Test error for even")
    elif parse_num % 3 == 0:
        raise ValueError("Test error for multiple of 3")
    elif parse_num == 0:
        raise ValueError("Test error for 0")
    return parse_num


def generate_urls_sleep(x: Any) -> tuple[str, ...]:
    sleep(random.randint(4, 6))
    return generate_urls(x)


def log_urls_sleep(url: tuple[str, ...]) -> str:
    sleep(random.randint(4, 6))
    return log_urls(url)


def download_sleep(url: str) -> str:
    sleep(random.randint(4, 6))
    return download(url)


def parse_sleep(url: str) -> int:
    sleep(random.randint(4, 6))
    return parse(url)


def download_to_file(task: tuple[str, str]) -> str:
    url, file_path = task
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        return f"Downloaded {url} → {file_path}"
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")


# =========================
# 其他
# =========================


# =========================
# ETL 模拟函数（demo_graph 用）
# =========================


def extract_record(raw_id: int) -> dict[str, Any]:
    sleep(0.5)
    return {"id": raw_id, "value": raw_id * 10, "label": f"item_{raw_id}"}


def transform_normalize(record: dict[str, Any]) -> dict[str, Any]:
    sleep(0.3)
    value = record["value"]
    return {**record, "normalized": value / 100.0}


def transform_enrich(record: dict[str, Any]) -> dict[str, Any]:
    sleep(0.3)
    return {**record, "category": "even" if record["id"] % 2 == 0 else "odd"}


def load_record(record: dict[str, Any]) -> str:
    sleep(0.2)
    return f"Saved record #{record['id']} (category={record.get('category', '?')})"


async def async_double(n: Any) -> Any:
    await asyncio.sleep(0.3)
    return n * 2


async def async_to_str(n: Any) -> str:
    await asyncio.sleep(0.2)
    return f"result={n}"


class RouterWrapper:
    def __init__(self, a_name: str, b_name: str) -> None:
        self.a_name = a_name
        self.b_name = b_name
        self.__name__ = "RouterWrapper"  # 框架需要这个属性

    def __call__(self, n: int) -> tuple[str, int]:
        target = self.a_name if (n % 2 == 0) else self.b_name
        return (target, n)
