import os

from dotenv import load_dotenv

from demo_utils import (
    router_even,
    download_sleep,
    generate_urls_sleep,
    log_urls_sleep,
    no_op,
    parse_sleep,
    sleep_1,
)

from celestialtree import Client as CelestialTreeClient

from celestialflow import (
    TaskChain,
    TaskGraph,
    TaskRouter,
    TaskSplitter,
    TaskStage,
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
    # 阶段定义：生成 URL、记录日志、拆分批量结果、下载资源、解析新 URL。
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
        persist_result=True,
    )
    parse_stage = TaskStage(
        "Parser",
        parse_sleep,
        max_workers=4,
    )

    # 图组装：Generator 同时连到 Logger 和 Splitter，Parser 再回环到 Generator。
    graph = TaskGraph("demo_splitter_0", log_level="INFO")
    graph.set_stages(
        stages=[generate_stage, logger_stage, splitter, download_stage, parse_stage],
    )
    graph.connect([generate_stage], [logger_stage, splitter])
    graph.connect([splitter], [download_stage, parse_stage])
    graph.connect([parse_stage], [generate_stage])

    graph.set_graph_mode("thread", "thread")
    graph.set_reporter(True, host=report_host, port=report_port)
    # graph.set_ctree(ctree_client)

    # 运行入口：从 GenURLs 注入初始种子任务，观察 split 与回环效果。
    graph.start_graph(
        {
            generate_stage.get_name(): list(range(10)) + [1, 2, 3, 6, 7, 8, 9],
        },
        False,
    )


def demo_splitter_1() -> None:
    # 阶段定义：用 Splitter 把一个大 iterable 拆成大量细粒度任务。
    task_splitter = TaskSplitter("Splitter")
    process_stage = TaskStage("Process", no_op, execution_mode="thread", max_workers=50)

    # 链式结构：这里不需要手动 connect，直接用 TaskChain 串起两个阶段。
    chain = TaskChain(
        "demo_splitter_1",
        [task_splitter, process_stage],
        stage_mode="thread",
        log_level="INFO",
    )
    chain.set_reporter(True, host=report_host, port=report_port)
    chain.set_ctree(ctree_client)

    # 运行入口：把 range(100_000) 包成单个任务送进 Splitter。
    chain.start_chain(
        {
            task_splitter.get_name(): [range(100_000)],
        }
    )


def demo_router_0() -> None:
    # 阶段定义：Origin 只生成任务本身，Router 负责按规则选择下游并分发。
    a_name = "StageA"
    b_name = "StageB"

    source_stage = TaskStage(
        "Origin",
        sleep_1,
        stage_mode="serial",
        execution_mode="thread",
        max_workers=4,
    )
    router = TaskRouter(
        "Router",
        router_even,
        stage_mode="serial",
    )
    stage_a = TaskStage(
        a_name,
        sleep_1,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=2,
    )
    stage_b = TaskStage(
        b_name,
        sleep_1,
        stage_mode="thread",
        execution_mode="thread",
        max_workers=2,
    )

    # 图组装：Origin -> Router -> {StageA, StageB}，演示基于奇偶的条件路由。
    graph = TaskGraph("demo_router_0")
    graph.set_stages(
        stages=[source_stage, router, stage_a, stage_b],
    )
    graph.connect([source_stage], [router])
    graph.connect([router], [stage_a, stage_b])

    graph.set_reporter(True, host=report_host, port=report_port)
    # graph.set_ctree(ctree_client)

    # 运行入口：输入一组整数，观察 Router 按规则把奇偶任务分发到不同下游。
    graph.start_graph(
        {
            source_stage.get_name(): list(range(20)),
        }
    )


if __name__ == "__main__":
    demo_splitter_0()
    # demo_router_0()
    pass
