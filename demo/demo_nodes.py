import os

from celestialtree import Client as CelestialTreeClient
from demo_utils import (
    download_sleep,
    generate_urls_sleep,
    log_urls_sleep,
    no_op,
    parse_sleep,
    router_even,
    sleep_1,
)
from dotenv import load_dotenv

from celestialflow import (
    TaskChain,
    TaskGraph,
    TaskReporter,
    TaskRouter,
    TaskSplitter,
    TaskExecutor,
)

load_dotenv()

report_host: str = os.getenv("REPORT_HOST", "")
report_port: int = int(os.getenv("REPORT_PORT", "0"))

ctree_host: str = os.getenv("CTREE_HOST", "")
ctree_http_port: int = int(os.getenv("CTREE_HTTP_PORT", "0"))
ctree_grpc_port: int = int(os.getenv("CTREE_GRPC_PORT", "0"))

ctree_client = CelestialTreeClient(
    host=ctree_host,
    http_port=ctree_http_port,
    grpc_port=ctree_grpc_port,
)


def demo_splitter_0() -> None:
    # 节点定义：生成 URL、记录日志、拆分批量结果、下载资源、解析新 URL。
    generate_node = TaskExecutor(
        "GenURLs",
        generate_urls_sleep,
        max_workers=4,
    )
    logger_node = TaskExecutor(
        "Logger",
        log_urls_sleep,
        max_workers=4,
    )
    splitter = TaskSplitter(
        "Splitter",
    )
    download_node = TaskExecutor(
        "Downloader",
        download_sleep,
        max_workers=4,
    )
    parse_node = TaskExecutor(
        "Parser",
        parse_sleep,
        max_workers=4,
    )

    # 图组装：Generator 同时连到 Logger 和 Splitter，Parser 再回环到 Generator。
    graph = TaskGraph("demo_splitter_0")
    graph.set_nodes(
        nodes=[generate_node, logger_node, splitter, download_node, parse_node],
    )
    graph.connect([generate_node], [logger_node, splitter])
    graph.connect([splitter], [download_node, parse_node])
    graph.connect([parse_node], [generate_node])

    graph.set_graph_mode("thread")
    graph.set_node_execution_mode("thread")
    graph.set_reporter(TaskReporter(report_host, report_port, graph))
    # graph.set_ctree(ctree_client)

    # 运行入口：从 GenURLs 注入初始种子任务，观察 split 与回环效果。
    graph.run(
        {"GenURLs": [*list(range(10)), 1, 2, 3, 6, 7, 8, 9]},
        if_put_signal=False,
    )


def demo_splitter_1() -> None:
    # 节点定义：用 Splitter 把一个大 iterable 拆成大量细粒度任务。
    task_splitter = TaskSplitter("Splitter")
    process_node = TaskExecutor("Process", no_op, execution_mode="thread", max_workers=50)

    # 链式结构：这里不需要手动 connect，直接用 TaskChain 串起两个节点。
    chain = TaskChain(
        "demo_splitter_1",
        [task_splitter, process_node],
    )
    chain.set_reporter(TaskReporter(report_host, report_port, chain))
    chain.set_ctree(ctree_client)

    # 运行入口：把 range(100_000) 包成单个任务送进 Splitter。
    chain.run({"Splitter": [range(100_000)]})


def demo_router_0() -> None:
    # 节点定义：Origin 只生成任务本身，Router 负责按规则选择下游并分发。
    a_name = "NodeA"
    b_name = "NodeB"

    source_node = TaskExecutor(
        "Origin",
        sleep_1,
        execution_mode="thread",
        max_workers=4,
    )
    router = TaskRouter(
        "Router",
        router_even,
    )
    node_a = TaskExecutor(
        a_name,
        sleep_1,
        execution_mode="thread",
        max_workers=2,
    )
    node_b = TaskExecutor(
        b_name,
        sleep_1,
        execution_mode="thread",
        max_workers=2,
    )

    # 图组装：Origin -> Router -> {NodeA, NodeB}，演示基于奇偶的条件路由。
    graph = TaskGraph("demo_router_0", graph_mode="thread")
    graph.set_nodes(
        nodes=[source_node, router, node_a, node_b],
    )
    graph.connect([source_node], [router])
    graph.connect([router], [node_a, node_b])

    graph.set_reporter(TaskReporter(report_host, report_port, graph))
    # graph.set_ctree(ctree_client)

    # 运行入口：输入一组整数，观察 Router 按规则把奇偶任务分发到不同下游。
    graph.run({"Origin": list(range(20))})


if __name__ == "__main__":
    demo_splitter_0()
    # demo_router_0()
    pass
