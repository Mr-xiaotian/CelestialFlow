import os
from typing import Any

from celestialtree import Client as CelestialTreeClient
from demo_utils import (
    async_double,
    async_to_str,
    extract_record,
    load_record,
    transform_enrich,
    transform_normalize,
)
from dotenv import load_dotenv

from celestialflow import (
    TaskGraph,
    TaskReporter,
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

ctree_client = CelestialTreeClient(
    host=ctree_host,
    http_port=ctree_http_port,
    grpc_port=ctree_grpc_port,
)


def demo_etl_fan_out_fan_in() -> None:
    """
    ETL pipeline with fan-out/fan-in topology:

        Extract ──┬── Normalize ──┬── Load
                  └── Enrich ─────┘

    Demonstrates:
    - Fan-out: one stage feeds two parallel downstream stages
    - Fan-in: two stages merge into one downstream stage
    - Mixed execution modes across stages
    - Querying graph summary after execution
    """
    extract = TaskStage(
        "Extract",
        extract_record,
        execution_mode="thread",
        max_workers=4,
    )
    normalize = TaskStage(
        "Normalize",
        transform_normalize,
        execution_mode="thread",
        max_workers=4,
    )
    enrich = TaskStage(
        "Enrich",
        transform_enrich,
        execution_mode="thread",
        max_workers=4,
    )
    load = TaskStage(
        "Load",
        load_record,
        execution_mode="serial",
    )

    graph = TaskGraph("demo_etl_fan_out_fan_in", graph_mode="thread")
    graph.set_reporter(TaskReporter(report_host, report_port, graph))
    graph.set_ctree(ctree_client)
    graph.set_stages(
        stages=[extract, normalize, enrich, load],
    )
    graph.connect([extract], [normalize, enrich])
    graph.connect([normalize, enrich], [load])

    raw_ids = list(range(1, 16))
    graph.run({"Extract": raw_ids})


async def demo_async_pipeline() -> None:
    """
    Two-stage async pipeline:

        AsyncDouble ──> AsyncToStr

    Demonstrates:
    - execution_mode="async" for coroutine-based task functions
    - Retrieving per-stage status after completion
    """
    stage_double = TaskStage(
        "AsyncDouble",
        async_double,
        execution_mode="async",
        max_workers=8,
    )
    stage_to_str = TaskStage(
        "AsyncToStr",
        async_to_str,
        execution_mode="async",
        max_workers=8,
    )

    graph = TaskGraph("demo_async_pipeline", graph_mode="async")
    graph.set_reporter(TaskReporter(report_host, report_port, graph))
    graph.set_ctree(ctree_client)
    graph.set_stages(
        stages=[stage_double, stage_to_str],
    )
    graph.connect([stage_double], [stage_to_str])

    tasks: list[Any] = list(range(1, 21))
    await graph.run_async({"AsyncDouble": tasks})



if __name__ == "__main__":
    demo_etl_fan_out_fan_in()
    # demo_async_pipeline()
    pass
