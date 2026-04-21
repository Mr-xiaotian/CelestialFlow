import logging
import os
import random

import pytest
from test_utils import (
    RouterWrapper,
    download_sleep,
    download_to_file,
    fibonacci,
    generate_urls_sleep,
    log_urls_sleep,
    no_op,
    parse_sleep,
    sleep_1,
    sum_int,
)

from celestialflow import (
    TaskChain,
    TaskGraph,
    TaskRedisAck,
    TaskRedisSource,
    TaskRedisTransport,
    TaskRouter,
    TaskSplitter,
    TaskStage,
)

report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")

redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")

ctree_host = os.getenv("CTREE_HOST")
ctree_http_port = os.getenv("CTREE_HTTP_PORT")
ctree_grpc_port = os.getenv("CTREE_GRPC_PORT")


class DownloadRedisTransport(TaskRedisTransport):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_go/")


class DownloadStage(TaskStage):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_py/")


def test_splitter_0():
    # 定义任务节点
    generate_stage = TaskStage(
        func=generate_urls_sleep,
        execution_mode="thread",
        max_workers=4,
        stage_mode="process",
        stage_name="GenURLs",
    )
    logger_stage = TaskStage(
        func=log_urls_sleep,
        execution_mode="thread",
        max_workers=4,
        stage_mode="process",
        stage_name="Logger",
    )
    splitter = TaskSplitter(
        stage_mode="process",
        stage_name="Splitter",
    )
    download_stage = TaskStage(
        func=download_sleep,
        execution_mode="thread",
        max_workers=4,
        stage_mode="process",
        stage_name="Downloader",
    )
    parse_stage = TaskStage(
        func=parse_sleep,
        execution_mode="thread",
        max_workers=4,
        stage_mode="process",
        stage_name="Parser",
    )

    # 初始化 TaskGraph
    graph = TaskGraph(log_level="INFO")
    graph.set_stages(
        root_stages=[generate_stage],
        stages=[generate_stage, logger_stage, splitter, download_stage, parse_stage],
    )
    graph.connect([generate_stage], [logger_stage, splitter])
    graph.connect([splitter], [download_stage, parse_stage])
    graph.connect([parse_stage], [generate_stage])

    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(
        True, host=ctree_host, http_port=ctree_http_port, grpc_port=ctree_grpc_port
    )

    graph.start_graph(
        {
            generate_stage.get_tag(): list(range(10)) + [1, 2, 3, 6, 7, 8, 9],
        },
        True,
    )


def test_splitter_1():
    # 定义任务节点
    task_splitter = TaskSplitter()
    process_stage = TaskStage(no_op, execution_mode="thread", max_workers=50)

    chain = TaskChain([task_splitter, process_stage], "process", log_level="INFO")
    chain.set_reporter(True, host=report_host, port=report_port)
    chain.set_ctree(
        True,
        host=ctree_host,
        http_port=ctree_http_port,
        grpc_port=ctree_grpc_port,
        transport="grpc",
    )

    chain.start_chain(
        {
            task_splitter.get_tag(): [range(int(1e5))],
        }
    )


def test_redis_ack_0():
    start_stage = TaskStage(
        sleep_1,
        execution_mode="thread",
        max_workers=4,
        stage_mode="serial",
        stage_name="Start",
    )
    redis_tranport = TaskRedisTransport(
        key="testFibonacci:input",
        host=redis_host,
        password=redis_password,
        stage_mode="process",
        stage_name="RedisTransport",
    )
    redis_ack = TaskRedisAck(
        key="testFibonacci:output",
        host=redis_host,
        password=redis_password,
        stage_mode="process",
        stage_name="RedisAck",
    )
    fibonacci_stage = TaskStage(
        fibonacci,
        "thread",
        stage_mode="process",
        stage_name="Fibonacci",
    )

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[start_stage],
        stages=[start_stage, redis_tranport, redis_ack, fibonacci_stage],
    )
    graph.connect([start_stage], [redis_tranport, fibonacci_stage])
    graph.connect([redis_tranport], [redis_ack])

    graph.set_reporter(True, host=report_host, port=report_port)

    # 要测试的任务列表
    test_task_0 = range(25, 37)
    test_task_1 = list(test_task_0) + [0, 27, None, 0, ""]

    graph.start_graph(
        {
            start_stage.get_tag(): test_task_1,
        }
    )


def test_redis_ack_1():
    start_stage = TaskStage(
        sleep_1,
        execution_mode="thread",
        max_workers=4,
        stage_mode="serial",
        stage_name="Start",
    )
    redis_tranport = TaskRedisTransport(
        key="testSum:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
        stage_mode="process",
        stage_name="RedisTransport",
    )
    redis_ack = TaskRedisAck(
        key="testSum:output",
        host=redis_host,
        password=redis_password,
        stage_mode="process",
        stage_name="RedisAck",
    )
    sum_stage = TaskStage(
        sum_int,
        execution_mode="thread",
        max_workers=4,
        unpack_task_args=True,
        stage_mode="process",
        stage_name="Sum",
    )

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[start_stage],
        stages=[start_stage, redis_tranport, redis_ack, sum_stage],
    )
    graph.connect([start_stage], [redis_tranport, sum_stage])
    graph.connect([redis_tranport], [redis_ack])

    graph.set_reporter(True, host=report_host, port=report_port)

    # 要测试的任务列表
    test_task_0 = [(random.randint(1, 100), random.randint(1, 100)) for _ in range(12)]

    graph.start_graph(
        {
            start_stage.get_tag(): test_task_0,
        }
    )


def test_redis_ack_2():
    start_stage = TaskStage(
        sleep_1,
        execution_mode="thread",
        max_workers=4,
        stage_mode="serial",
        stage_name="Start",
    )
    redis_tranport = DownloadRedisTransport(
        key="testDownload:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
        stage_mode="process",
        stage_name="RedisTransport",
    )
    redis_ack = TaskRedisAck(
        key="testDownload:output",
        host=redis_host,
        password=redis_password,
        stage_mode="process",
        stage_name="RedisAck",
    )
    download_stage = DownloadStage(
        download_to_file,
        execution_mode="thread",
        max_workers=4,
        stage_mode="process",
        stage_name="Download",
    )

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[start_stage],
        stages=[start_stage, redis_tranport, redis_ack, download_stage],
    )
    graph.connect([start_stage], [redis_tranport, download_stage])
    graph.connect([redis_tranport], [redis_ack])

    graph.set_reporter(True, host=report_host, port=report_port)

    download_links = [
        [
            "https://img.4khd.com/-IaKPu2ONWz8/aEhVCP-4Wsl/AAAAAAADirM/2Fg5CujCaKk7PqPY3I6DELSmidZE3ofqgCNcBGAsHYQ/w1300-rw/orts-shoes-4khd.com-001.webp?w=1300",
            "/tmp/orts-shoes-4khd.com-001.png",
        ],
        [
            "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/2949210/ss_a2792205c92812f5be3321f2e685135b402e5a72.600x338.jpg?t=1714466877",
            "/tmp/steam_2949210.jpg",
        ],
    ]

    graph.start_graph({start_stage.get_tag(): download_links})


def test_redis_source_0():
    sleep_stage_0 = TaskStage(
        sleep_1,
        execution_mode="serial",
        stage_mode="process",
        stage_name="Sleep0",
    )
    redis_tranport = TaskRedisTransport(
        "test_redis",
        host=redis_host,
        password=redis_password,
        stage_mode="process",
        stage_name="RedisTransport",
    )
    redis_source = TaskRedisSource(
        "test_redis",
        host=redis_host,
        password=redis_password,
        stage_mode="process",
        stage_name="RedisSource",
    )
    sleep_stage_1 = TaskStage(
        sleep_1,
        execution_mode="serial",
        stage_mode="process",
        stage_name="Sleep1",
    )

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[sleep_stage_0, redis_source],
        stages=[sleep_stage_0, redis_tranport, redis_source, sleep_stage_1],
    )
    graph.connect([sleep_stage_0], [redis_tranport])
    graph.connect([redis_source], [sleep_stage_1])

    graph.set_reporter(True, host=report_host, port=report_port)

    # 要测试的任务列表
    test_task_0 = range(25, 37)

    graph.start_graph(
        {
            sleep_stage_0.get_tag(): test_task_0,
            redis_source.get_tag(): range(12),
        }
    )


def test_router_0():
    router = TaskRouter(
        stage_mode="serial",
        stage_name="Router",
    )
    stage_a = TaskStage(
        func=sleep_1,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
        stage_name="Stage A",
    )
    stage_b = TaskStage(
        func=sleep_1,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
        stage_name="Stage B",
    )

    a_tag = stage_a.get_tag()
    b_tag = stage_b.get_tag()

    source_stage = TaskStage(
        RouterWrapper(a_tag, b_tag),
        execution_mode="thread",
        max_workers=4,
        stage_mode="serial",
        stage_name="Origin",
    )

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[source_stage],
        stages=[source_stage, router, stage_a, stage_b],
    )
    graph.connect([source_stage], [router])
    graph.connect([router], [stage_a, stage_b])

    graph.set_reporter(True, host=report_host, port=report_port)

    graph.start_graph(
        {
            source_stage.get_tag(): range(20),
        }
    )


if __name__ == "__main__":
    # test_splitter_0()
    test_router_0()
    pass
