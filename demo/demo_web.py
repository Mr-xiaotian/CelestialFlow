from __future__ import annotations

import os
from collections.abc import Callable
from time import sleep
from typing import Any

from dotenv import load_dotenv

from demo_utils import add_one_sleep

from celestialflow import (
    TaskExecutor,
    TaskGraph,
    TaskReporter,
    TaskRouter,
    TaskSplitter,
)

load_dotenv()

report_host: str = os.getenv("REPORT_HOST", "")
report_port: int = int(os.getenv("REPORT_PORT", "0"))


# ==== 任务函数 ====


def ingest_task(n: int) -> int:
    """注入阶段：轻量返回输入值。"""
    sleep(1)
    return n


def make_flaky(fail_map: dict[int, int]) -> Callable[[int], tuple[int, ...]]:
    """
    构造一个"前 ``fail_map[n]`` 次抛 ValueError、之后成功"的任务函数。

    :param fail_map: 每个输入值需要连续失败的次数映射
    :return: 归一化阶段任务函数
    """

    counts: dict[int, int] = {}

    def normalize(n: int) -> tuple[int, ...]:
        sleep(0.5)
        if counts.get(n, 0) < fail_map.get(n, 0):
            counts[n] = counts.get(n, 0) + 1
            raise ValueError(f"flaky failure for input {n}")
        return (n, n * 10, n * 100)

    return normalize


def validate_task(n: int) -> tuple[int, int]:
    """校验阶段：特定输入直接抛出不可重试的错误。"""
    sleep(0.5)
    if n % 11 == 0:
        raise RuntimeError(f"validation rejected {n}")
    return (n, n * 2)


def split_task(items: tuple[Any, ...]) -> tuple[Any, ...]:
    """拆分阶段：把上游传入的可迭代结果原样拆分为独立条目。"""
    sleep(0.03)
    return items


def route_task(item: Any) -> dict[str, Any]:
    """路由阶段：按 ``item % 3`` 分发到三个不同的下游节点。"""
    sleep(0.02)
    target = {0: "StageA", 1: "StageB", 2: "StageC"}[item % 3]
    return {target: item}


def make_stage_task(prefix: str) -> Callable[[Any], str]:
    """
    构造指定前缀的 stage 处理函数。

    :param prefix: 结果字符串前缀 (StageA / StageB / StageC)
    :return: stage 阶段任务函数
    """

    def stage(x: Any) -> str:
        sleep(0.5)
        return f"{prefix}({x})"

    return stage


def collect_task(x: str) -> str:
    """汇聚阶段：原样返回。"""
    sleep(0.2)
    return x


# ==== 主入口 ====

def demo_forest() -> None:
    # 构建 DAG: A ➝ B ➝ E；C ➝ D ➝ E
    node_a = TaskExecutor(
        "node_a",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_b = TaskExecutor(
        "node_b",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_c = TaskExecutor(
        "node_c",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_d = TaskExecutor(
        "node_d",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_e = TaskExecutor(
        "node_e",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )

    # 构建 DAG: F ➝ G ➝ I；F ➝ H ➝ J
    node_f = TaskExecutor(
        "node_f",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_g = TaskExecutor(
        "node_g",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_h = TaskExecutor(
        "node_h",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_i = TaskExecutor(
        "node_i",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_j = TaskExecutor(
        "node_j",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )

    # 设置图结构
    graph = TaskGraph("demo_forest", graph_mode="thread")
    graph.set_nodes(
        nodes=[
            node_a,
            node_b,
            node_c,
            node_d,
            node_e,
            node_f,
            node_g,
            node_h,
            node_i,
            node_j,
        ],
    )
    graph.connect([node_a], [node_c])
    graph.connect([node_b], [node_d])
    graph.connect([node_c], [node_e])
    graph.connect([node_d], [node_e])

    graph.connect([node_f], [node_g, node_h])
    graph.connect([node_g], [node_i])
    graph.connect([node_h], [node_j])

    graph.set_reporter(TaskReporter(report_host, report_port, graph))
    # graph.set_ctree(ctree_client)

    # 初始任务
    init_tasks: dict[str, list[int]] = {
        node_a.get_name(): list(range(1, 11)),
        node_b.get_name(): list(range(11, 21)),
        node_f.get_name(): list(range(21, 31)),
    }

    graph.run(init_tasks)


def demo_topology_topology() -> None:
    """
    复杂拓扑 Web 仪表盘展示 demo.

    构建一个 6 层、含扇出/扇入、TaskSplitter 与 TaskRouter 的复杂任务图,
    通过 TaskReporter 周期性向 celestialflow-web 推送状态、结构、错误与
    生命周期数据, 用于观察 web 仪表盘在复杂拓扑下的显示效果:

    - 结构图: 九节点多层拓扑, Splitter 显示为 subgraph、Router 显示为菱形,
      启用"边标签"配置后可观察每条边累计/增量传输量
    - 节点状态卡: 不同执行模式 (serial / thread) 与并行度展示
    - 错误日志: ValueError (重试后失败, retry=2) 与 RuntimeError (不可重试) 两类错误
    - 进度条: 成功 / 失败 / 重复四段比例
    - 生命周期: 重试次数 (retry_times) 随失败记录持久化

    若未设置 REPORT_HOST / REPORT_PORT 环境变量, demo 仍可独立运行 (跳过上报)。
    """
    # 节点定义：混合 serial / thread 执行模式。
    ingest = TaskExecutor(
        "Ingest",
        ingest_task,
        execution_mode="thread",
        max_workers=4,
    )
    normalize = TaskExecutor(
        "Normalize",
        make_flaky({11: 1, 7: 3}),
        execution_mode="thread",
        max_workers=4,
        max_retries=2,
    )
    validate = TaskExecutor(
        "Validate",
        validate_task,
        execution_mode="thread",
        max_workers=4,
    )
    splitter = TaskSplitter(
        "Splitter",
        split_task,
        execution_mode="thread",
        max_workers=4,
    )
    router = TaskRouter(
        "Router",
        route_task,
        execution_mode="thread",
        max_workers=4,
    )
    stage_a = TaskExecutor("StageA", make_stage_task("A"), execution_mode="serial")
    stage_b = TaskExecutor(
        "StageB",
        make_stage_task("B"),
        execution_mode="thread",
        max_workers=3,
    )
    stage_c = TaskExecutor(
        "StageC",
        make_stage_task("C"),
        execution_mode="thread",
        max_workers=3,
    )
    collect = TaskExecutor("Collect", collect_task, execution_mode="serial")

    # Normalize 阶段的 ValueError 允许重试, 展示重试后成功 / 重试耗尽失败两种结果。
    normalize.set_retry_exceptions(ValueError)

    # 拓扑组装（6 层）：
    #   Ingest ──┬── Normalize ──┐
    #            └── Validate ───┴── Splitter ── Router ──┬── StageA ──┐
    #                                                     ├── StageB ──┴── Collect
    #                                                     └── StageC ──┘
    graph = TaskGraph("demo_web_topology", graph_mode="thread")
    graph.set_nodes(
        nodes=[
            ingest,
            normalize,
            validate,
            splitter,
            router,
            stage_a,
            stage_b,
            stage_c,
            collect,
        ],
    )
    graph.connect([ingest], [normalize, validate])
    graph.connect([normalize, validate], [splitter])
    graph.connect([splitter], [router])
    graph.connect([router], [stage_a, stage_b, stage_c])
    graph.connect([stage_a, stage_b, stage_c], [collect])

    # 上报到 web（可选）：未配置 REPORT_HOST / REPORT_PORT 时跳过。
    if report_host:
        reporter = TaskReporter(report_host, report_port, graph)
        reporter.interval = 2  # 加快刷新间隔，便于在仪表盘上观察
        graph.set_reporter(reporter)
        print(f"[demo] 已启用上报: http://{report_host}:{report_port} "
              f"(interval={reporter.interval}s)")
    else:
        print("[demo] 未设置 REPORT_HOST/REPORT_PORT，跳过 web 上报（可独立运行）")

    # 输入：24 个任务（其中 3 / 5 / 8 / 12 与前面的值重复）。
    seeds = [*range(1, 21), 3, 5, 8, 12]
    print(f"[demo] 注入 {len(seeds)} 个任务（含 4 个重复值）")
    graph.run({"Ingest": seeds})

    # 结果摘要。
    print("\n[demo] 各节点计数:")
    for name in ["Ingest", "Normalize", "Validate", "Splitter", "Router",
                 "StageA", "StageB", "StageC", "Collect"]:
        node = graph.node_dict[name]
        counts = node.metrics.get_counts()
        print(
            f"  {name:<9} input={counts['tasks_input']:<4} "
            f"ok={counts['tasks_succeeded']:<4} "
            f"fail={counts['tasks_failed']:<3} "
            f"skip={counts['tasks_skipped']}"
        )


if __name__ == "__main__":
    demo_forest()
    demo_topology_topology()
