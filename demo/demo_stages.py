import os
import random

from dotenv import load_dotenv  # type: ignore[reportMissingImports]

from demo_utils import (
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

load_dotenv()

report_host: str = os.getenv("REPORT_HOST", "")
report_port: int = int(os.getenv("REPORT_PORT", "0"))

redis_host: str = os.getenv("REDIS_HOST", "")
redis_password: str = os.getenv("REDIS_PASSWORD", "")

ctree_host: str = os.getenv("CTREE_HOST", "")
ctree_http_port: int = int(os.getenv("CTREE_HTTP_PORT", "0"))
ctree_grpc_port: int = int(os.getenv("CTREE_GRPC_PORT", "0"))


class DownloadRedisTransport(TaskRedisTransport):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_go/")


class DownloadStage(TaskStage):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_py/")


def demo_splitter_0():
    # 定义任务节点
    generate_stage = TaskStage(
        "GenURLs",
        generate_urls_sleep,
        max_workers=4,
    )
    logger_stage = TaskStage(
        "Logger",
        log_urls_sleep,
        max_workers=4,
    )
    splitter = TaskSplitter(
        "Splitter",
    )
    download_stage = TaskStage(
        "Downloader",
        download_sleep,
        max_workers=4,
    )
    parse_stage = TaskStage(
        "Parser",
        parse_sleep,
        max_workers=4,
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

    graph.set_graph_mode("thread", "thread")
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


def demo_splitter_1():
    # 定义任务节点
    task_splitter = TaskSplitter("Splitter")
    process_stage = TaskStage("Process", no_op, execution_mode="thread", max_workers=50)

    chain = TaskChain([task_splitter, process_stage], "thread", log_level="INFO")
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


def demo_redis_ack_0():
    start_stage = TaskStage(
        "Start",
        sleep_1,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    redis_tranport = TaskRedisTransport(
        "RedisTransport",
        key="testFibonacci:input",
        host=redis_host,
        password=redis_password,
        stage_mode="thread",
    )
    redis_ack = TaskRedisAck(
        "RedisAck",
        key="testFibonacci:output",
        host=redis_host,
        password=redis_password,
        stage_mode="thread",
    )
    fibonacci_stage = TaskStage(
        "Fibonacci",
        fibonacci,
        stage_mode="thread",
        execution_mode="thread",
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


def demo_redis_ack_1():
    start_stage = TaskStage(
        "Start",
        sleep_1,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    redis_tranport = TaskRedisTransport(
        "RedisTransport",
        key="testSum:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
        stage_mode="thread",
    )
    redis_ack = TaskRedisAck(
        "RedisAck",
        key="testSum:output",
        host=redis_host,
        password=redis_password,
        stage_mode="thread",
    )
    sum_stage = TaskStage(
        "Sum",
        sum_int,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
        unpack_task_args=True,
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


def demo_redis_ack_2():
    start_stage = TaskStage(
        "Start",
        sleep_1,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    redis_tranport = DownloadRedisTransport(
        "RedisTransport",
        key="testDownload:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
        stage_mode="thread",
    )
    redis_ack = TaskRedisAck(
        "RedisAck",
        key="testDownload:output",
        host=redis_host,
        password=redis_password,
        stage_mode="thread",
    )
    download_stage = DownloadStage(
        "Download",
        download_to_file,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=4,
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


def demo_redis_source_0():
    sleep_stage_0 = TaskStage(
        "Sleep0",
        sleep_1,
        stage_mode="thread",
        execution_mode="serial",
    )
    redis_tranport = TaskRedisTransport(
        "RedisTransport",
        key="test_redis",
        host=redis_host,
        password=redis_password,
        stage_mode="thread",
    )
    redis_source = TaskRedisSource(
        "RedisSource",
        key="test_redis",
        host=redis_host,
        password=redis_password,
        stage_mode="thread",
    )
    sleep_stage_1 = TaskStage(
        "Sleep1",
        sleep_1,
        stage_mode="thread",
        execution_mode="serial",
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
    test_task_0 = list(range(25, 37))

    graph.start_graph(
        {
            sleep_stage_0.get_tag(): test_task_0,
            redis_source.get_tag(): list(range(12)),
        }
    )


def demo_router_0():
    router = TaskRouter(
        "Router",
        stage_mode="serial",
    )
    stage_a = TaskStage(
        "StageA",
        sleep_1,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=2,
    )
    stage_b = TaskStage(
        "StageB",
        sleep_1,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=2,
    )

    a_tag = stage_a.get_tag()
    b_tag = stage_b.get_tag()

    source_stage = TaskStage(
        "Origin",
        RouterWrapper(a_tag, b_tag),
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
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
            source_stage.get_tag(): list(range(20)),
        }
    )


if __name__ == "__main__":
    demo_splitter_0()
    # demo_router_0()
    pass
