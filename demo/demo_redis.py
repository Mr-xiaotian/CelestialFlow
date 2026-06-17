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


class RedisClientHelper:
    def __init__(
        self,
        key: str,
        *,
        host: str,
        password: str | None,
        port: int = 6379,
        db: int = 0,
    ) -> None:
        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._redis_client: redis.Redis | None = None

    def get_redis(self) -> redis.Redis:
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
        return self._redis_client


class RedisTaskTransport(RedisClientHelper):
    def __init__(self, key: str, *, host: str, password: str | None) -> None:
        super().__init__(key, host=host, password=password)
        self._task_ids = count()

    def push(self, task: Any) -> int:
        redis_client = self.get_redis()
        task_id = next(self._task_ids)
        payload = json.dumps(
            {
                "id": task_id,
                "task": [task],
                "emit_ts": time.time(),
            }
        )
        _ = redis_client.rpush(self.key, payload)
        return task_id


class RedisTaskSource(RedisClientHelper):
    def __init__(
        self,
        key: str,
        *,
        host: str,
        password: str | None,
        timeout: int = 10,
    ) -> None:
        super().__init__(key, host=host, password=password)
        self.timeout = timeout

    def pop(self, _: Any) -> Any:
        redis_client = self.get_redis()
        res = cast(list[Any] | None, redis_client.blpop(self.key, timeout=self.timeout))
        if res is None:
            raise CelestialFlowTimeoutError(
                "Redis item not returned in time after being fetched"
            )

        _, item = res
        item_obj = cast(dict[str, Any], json.loads(cast(str, item)))
        task = item_obj.get("task")
        if task is None:
            raise RemoteWorkerError("Redis source payload missing 'task'")
        if len(task) == 1:
            return task[0]
        return tuple(task)


class RedisTaskAck(RedisClientHelper):
    def __init__(
        self,
        key: str,
        *,
        host: str,
        password: str | None,
        timeout: int = 10,
    ) -> None:
        super().__init__(key, host=host, password=password)
        self.timeout = timeout

    def wait(self, task_id: int) -> Any:
        redis_client = self.get_redis()
        start_time = time.perf_counter()

        while True:
            result = cast(str | None, redis_client.hget(self.key, str(task_id)))
            if result:
                _ = redis_client.hdel(self.key, str(task_id))
                result_obj = cast(dict[str, Any], json.loads(result))
                status = result_obj.get("status")
                if status == "success":
                    return self._normalize_result(result_obj.get("result"))
                if status == "error":
                    raise RemoteWorkerError(str(result_obj.get("error")))
                raise RemoteWorkerError(f"Unknown ack status: {result_obj}")

            if self.timeout and (time.perf_counter() - start_time) > self.timeout:
                raise CelestialFlowTimeoutError(
                    f"Redis ack timeout: task_id={task_id} not acknowledged"
                )
            time.sleep(0.1)

    @staticmethod
    def _normalize_result(result: Any) -> Any:
        if not hasattr(result, "__iter__") or isinstance(result, str | bytes):
            return result
        if isinstance(result, list):
            if len(result) == 1:
                return result[0]
            return tuple(result)
        return result


def demo_redis_ack_0() -> None:
    start_stage = TaskStage(
        "Start",
        sleep_1,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    redis_transport = RedisTaskTransport(
        "testFibonacci:input",
        host=redis_host,
        password=redis_password,
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_transport.push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    redis_ack = RedisTaskAck(
        "testFibonacci:output",
        host=redis_host,
        password=redis_password,
    )
    ack_stage = TaskStage(
        "RedisAck",
        redis_ack.wait,
        stage_mode="thread",
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    fibonacci_stage = TaskStage(
        "Fibonacci",
        fibonacci,
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
    start_stage = TaskStage(
        "Start",
        sleep_1,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    redis_transport = RedisTaskTransport(
        "testSum:input",
        host=redis_host,
        password=redis_password,
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_transport.push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    redis_ack = RedisTaskAck(
        "testSum:output",
        host=redis_host,
        password=redis_password,
    )
    ack_stage = TaskStage(
        "RedisAck",
        redis_ack.wait,
        stage_mode="thread",
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    sum_stage = TaskStage(
        "Sum",
        sum_int,
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
    start_stage = TaskStage(
        "Start",
        sleep_1,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    redis_transport = RedisTaskTransport(
        "testDownload:input",
        host=redis_host,
        password=redis_password,
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_transport.push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    redis_ack = RedisTaskAck(
        "testDownload:output",
        host=redis_host,
        password=redis_password,
    )
    ack_stage = TaskStage(
        "RedisAck",
        redis_ack.wait,
        stage_mode="thread",
        execution_mode="serial",
        enable_duplicate_check=False,
    )
    download_stage = TaskStage(
        "Download",
        download_to_file,
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
    sleep_stage_0 = TaskStage(
        "Sleep0",
        sleep_1,
        stage_mode="thread",
        execution_mode="serial",
    )
    redis_transport = RedisTaskTransport(
        "test_redis",
        host=redis_host,
        password=redis_password,
    )
    transport_stage = TaskStage(
        "RedisTransport",
        redis_transport.push,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
    )
    redis_source = RedisTaskSource(
        "test_redis",
        host=redis_host,
        password=redis_password,
    )
    source_stage = TaskStage(
        "RedisSource",
        redis_source.pop,
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
            source_stage.get_name(): list(range(12)),
        }
    )


if __name__ == "__main__":
    demo_redis_ack_0()
    # demo_redis_ack_1()
    # demo_redis_ack_2()
    # demo_redis_source_0()
