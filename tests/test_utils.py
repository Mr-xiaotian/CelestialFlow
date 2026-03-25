"""
Shared helper functions and classes used across test files.
"""
from __future__ import annotations

import asyncio
import math
import re
import random
import time
from time import sleep

import requests

from celestialflow import TaskStage, TaskRedisTransport


# =========================
# 通用计算函数
# =========================

def fibonacci(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


async def fibonacci_async(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        result_0 = await fibonacci_async(n - 1)
        result_1 = await fibonacci_async(n - 2)
        return result_0 + result_1


def no_op(n):
    return n


def sum_int(*num):
    return sum(num)


def add_one(num):
    return num + 1


def sqrt(num):
    return num ** 0.5


def square(x):
    sleep(1)
    return x * x


def add_offset(x, offset=10):
    if x > 30:
        raise ValueError("Test error for greater than 30")
    sleep(1)
    return x + offset


def add_5(x):
    return add_offset(x, 5)


def add_10(x):
    return add_offset(x, 10)


def add_15(x):
    return add_offset(x, 15)


def add_20(x):
    return add_offset(x, 20)


def add_25(x):
    return add_offset(x, 25)


def neuron_activation(x):
    if not isinstance(x, (int, float)):
        raise ValueError("Invalid input type")
    sleep(1)
    return 1 / (1 + math.exp(-x))


# =========================
# sleep 变体
#   sleep_1       — 纯延迟，有返回值（test_executor 用）
#   sleep_1_async — 纯延迟，有返回值的异步版本（test_executor 用）
# =========================


def sleep_1(n):
    sleep(1)
    return n


async def sleep_1_async(n):
    await asyncio.sleep(1)
    return n


# =========================
# 带 sleep 的运算函数（test_structure 用）
# =========================

def operate_sleep(a, b):
    sleep(1)
    return a + b, a * b


def operate_sleep_A(a, b):
    return operate_sleep(a, b)


def operate_sleep_B(a, b):
    return operate_sleep(a, b)


def operate_sleep_C(a, b):
    return operate_sleep(a, b)


def operate_sleep_D(a, b):
    return operate_sleep(a, b)


def operate_sleep_E(a, b):
    return operate_sleep(a, b)


def add_one_sleep(n):
    sleep(1)
    if n > 30:
        raise ValueError("Test error for greater than 30")
    elif n == 0:
        raise ValueError("Test error for 0")
    elif n is None:
        raise ValueError("Test error for None")
    return n + 1


# =========================
# URL 处理函数（test_stages 用）
# =========================

def generate_urls(x):
    return tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4))])


def log_urls(data):
    if data == ("url_1_0", "url_1_1"):
        raise ValueError("Test error in ('url_1_0', 'url_1_1')")
    return f"Logged({data})"


def download(url):
    if "url_3" in url:
        raise ValueError("Test error in url_3_*")
    return f"Downloaded({url})"


def parse(url):
    num_list = re.findall(r"\d+", url)
    parse_num = int("".join(num_list))
    if parse_num % 2 == 0:
        raise ValueError("Test error for even")
    elif parse_num % 3 == 0:
        raise ValueError("Test error for multiple of 3")
    elif parse_num == 0:
        raise ValueError("Test error for 0")
    return parse_num


def generate_urls_sleep(x):
    sleep(random.randint(4, 6))
    return generate_urls(x)


def log_urls_sleep(url):
    sleep(random.randint(4, 6))
    return log_urls(url)


def download_sleep(url):
    sleep(random.randint(4, 6))
    return download(url)


def parse_sleep(url):
    sleep(random.randint(4, 6))
    return parse(url)


def download_to_file(url: str, file_path: str) -> str:
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

class RouterWrapper:
    def __init__(self, a_tag, b_tag):
        self.a_tag = a_tag
        self.b_tag = b_tag
        self.__name__ = "RouterWrapper" # 框架需要这个属性

    def __call__(self, n: int) -> tuple:
        target = self.a_tag if (n % 2 == 0) else self.b_tag
        return (target, n)

