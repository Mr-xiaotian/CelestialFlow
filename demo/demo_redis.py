import json
import os
import random
import time
from itertools import count
from typing import Any, cast

import redis
from dotenv import load_dotenv

from demo_utils import download_to_file, fibonacci, sleep_1, sum_int

from celestialflow import TaskGraph, TaskStage
from celestialflow.runtime.util_errors import CelestialFlowTimeoutError, RemoteWorkerError

load_dotenv()

report_host: str = os.getenv("REPORT_HOST", "")
report_port: int = int(os.getenv("REPORT_PORT", "0"))

redis_host: str = os.getenv("REDIS_HOST", "")
redis_password: str = os.getenv("REDIS_PASSWORD", "")

_task_ids = count()
redis_timeout = 5


def sleep_1_fibonacci(num: int) -> Any:
    """模拟 1 秒的计算"""
    return "testFibonacci", sleep_1(num)


def sleep_1_sum(nums: tuple[int, ...]) -> Any:
    """模拟 1 秒的计算"""
    return "testSum", sleep_1(nums)


def sleep_1_download(url: str) -> Any:
    """模拟 1 秒的计算"""
    return "testDownload", sleep_1(url)


def sleep_1_report(task: tuple[str, Any]) -> Any:
    """模拟 1 秒的计算"""
    return "testReport", sleep_1(task)


def fibonacci_wrapper(task: tuple[str, int]) -> Any:
    """计算斐波那契数列"""
    num = task[1]
    return fibonacci(num)


def sum_int_wrapper(task: tuple[str, tuple[int, ...]]) -> Any:
    """计算整数和"""
    nums = task[1]
    return sum_int(nums)


def download_to_file_wrapper(task: tuple[str, str]) -> Any:
    """下载文件到本地"""
    url = task[1]
    return download_to_file(url)


def get_redis() -> redis.Redis:
    """获取 Redis 客户端"""
    redis_client = redis.Redis(
        host=redis_host,
        port=6379,
        db=0,
        password=redis_password,
        decode_responses=True,
    )
    return redis_client


def redis_push(task: Any) -> int:
    """将任务推送到 Redis 中"""
    key, task_payload = task
    redis_client: redis.Redis = get_redis()
    task_id = next(_task_ids)
    payload = json.dumps(
        {
            "id": task_id,
            "task": [task_payload],
            "emit_ts": time.time(),
        }
    )
    _ = redis_client.rpush(f"{key}:input", payload)
    return key, task_id


def redis_pop(key: str) -> Any:
    """从 Redis 中弹出任务"""
    redis_client: redis.Redis = get_redis()
    res = cast(list[Any] | None, redis_client.blpop(key, timeout=redis_timeout))
    if res is None:
        raise CelestialFlowTimeoutError(
            "Redis item not returned in time after being fetched"
        )

    _, item = res
    item_obj = cast(dict[str, Any], json.loads(cast(str, item)))
    task_payload = item_obj.get("task")
    if task_payload is None:
        raise RemoteWorkerError("Redis source payload missing 'payload'")
    if len(task_payload) == 1:
        return task_payload[0]
    return tuple(task_payload)


def redis_wait(task: tuple[str, int]) -> Any:
    """等待任务完成"""
    key, task_id = task
    redis_client: redis.Redis = get_redis()
    start_time = time.perf_counter()

    while True:
        result = cast(str | None, redis_client.hget(f"{key}:output", str(task_id)))
        if result:
            _ = redis_client.hdel(f"{key}:output", str(task_id))
            result_obj = cast(dict[str, Any], json.loads(result))
            status = result_obj.get("status")
            if status == "success":
                return _normalize_result(result_obj.get("result"))
            if status == "error":
                raise RemoteWorkerError(str(result_obj.get("error")))
            raise RemoteWorkerError(f"Unknown ack status: {result_obj}")

        if (time.perf_counter() - start_time) > redis_timeout:
            raise CelestialFlowTimeoutError(
                f"Redis ack timeout: task_id={task_id} not acknowledged"
            )
        time.sleep(0.1)

def _normalize_result(result: Any) -> Any:
    if not hasattr(result, "__iter__") or isinstance(result, str | bytes):
        return result
    if isinstance(result, list):
        if len(result) == 1:
            return result[0]
        return tuple(result)
    return result


def demo_redis_ack_0() -> None:
    """演示 Redis 任务确认"""

    start_stage = TaskStage(
        "Start",
        sleep_1_fibonacci,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    ack_stage = TaskStage(
        "RedisAck",
        redis_wait,
        stage_mode="thread",
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    fibonacci_stage = TaskStage(
        "Fibonacci",
        fibonacci_wrapper,
        stage_mode="thread",
        execution_mode="thread",
    )

    graph = TaskGraph("demo_redis_ack_0")
    graph.set_stages([start_stage, transport_stage, ack_stage, fibonacci_stage])
    graph.connect([start_stage], [transport_stage, fibonacci_stage])
    graph.connect([transport_stage], [ack_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    test_task: list[Any] = list(range(25, 37)) + [0, 27, None, 0, ""]
    graph.start_graph({start_stage.get_name(): test_task})


def demo_redis_ack_1() -> None:
    """演示 Redis 任务确认"""

    start_stage = TaskStage(
        "Start",
        sleep_1_sum,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    ack_stage = TaskStage(
        "RedisAck",
        redis_wait,
        stage_mode="thread",
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    sum_stage = TaskStage(
        "Sum",
        sum_int_wrapper,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )

    graph = TaskGraph("demo_redis_ack_1")
    graph.set_stages([start_stage, transport_stage, ack_stage, sum_stage])
    graph.connect([start_stage], [transport_stage, sum_stage])
    graph.connect([transport_stage], [ack_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    test_task: list[tuple[int, int]] = [
        (random.randint(1, 100), random.randint(1, 100)) for _ in range(12)
    ]
    graph.start_graph({start_stage.get_name(): test_task})


def demo_redis_ack_2() -> None:
    """演示 Redis 任务确认"""

    start_stage = TaskStage(
        "Start",
        sleep_1_download,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    ack_stage = TaskStage(
        "RedisAck",
        redis_wait,
        stage_mode="thread",
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    download_stage = TaskStage(
        "Download",
        download_to_file_wrapper,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )

    graph = TaskGraph("demo_redis_ack_2")
    graph.set_stages([start_stage, transport_stage, ack_stage, download_stage])
    graph.connect([start_stage], [transport_stage, download_stage])
    graph.connect([transport_stage], [ack_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    download_links: list[tuple[str, str]] = [
        (
            "https://img.4khd.com/-IaKPu2ONWz8/aEhVCP-4Wsl/AAAAAAADirM/2Fg5CujCaKk7PqPY3I6DELSmidZE3ofqgCNcBGAsHYQ/w1300-rw/orts-shoes-4khd.com-001.webp?w=1300",
            "X:/Download/download_py/orts-shoes-4khd.com-001.png",
        ),
        (
            "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/2949210/ss_a2792205c92812f5be3321f2e685135b402e5a72.600x338.jpg?t=1714466877",
            "X:/Download/download_py/steam_2949210.jpg",
        ),
    ]
    graph.start_graph({start_stage.get_name(): download_links})


def demo_redis_source_0() -> None:
    """演示 Redis 任务确认"""

    sleep_stage_0 = TaskStage(
        "Sleep0",
        sleep_1_report,
        stage_mode="thread",
        execution_mode="serial",
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    source_stage = TaskStage(
        "RedisSource",
        redis_pop,
        stage_mode="thread",
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    sleep_stage_1 = TaskStage(
        "Sleep1",
        sleep_1,
        stage_mode="thread",
        execution_mode="serial",
    )

    graph = TaskGraph("demo_redis_source_0")
    graph.set_stages([sleep_stage_0, transport_stage, source_stage, sleep_stage_1])
    graph.connect([sleep_stage_0], [transport_stage])
    graph.connect([source_stage], [sleep_stage_1])
    graph.set_reporter(True, host=report_host, port=report_port)

    graph.start_graph(
        {
            sleep_stage_0.get_name(): list(range(25, 37)),
            source_stage.get_name(): ["testReport:input" for i in range(12)],
        }
    )


if __name__ == "__main__":
    # demo_redis_ack_0()
    # demo_redis_ack_1()
    # demo_redis_ack_2()
    demo_redis_source_0()
