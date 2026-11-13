"""演示用 CelestialTree 客户端替代默认的 ``LocalEventClient``。

``TaskGraph`` / ``TaskExecutor`` 默认使用 ``LocalEventClient``：事件只在本地生成
递增 ID，不离开当前进程。把 ``CelestialTreeClient`` 通过 ``set_ctree()`` 注入后，
任务输入、成功、失败、重试与终止信号等事件都会发送到 CelestialTree 服务，并可用
其客户端接口查询任务血缘（provenance / ancestors / descendants）。

运行前准备：

- 启动 CelestialTree 服务（HTTP 默认 ``7777``，gRPC 默认 ``7778``）；
- 安装 ``celestialtree``（源码仓库中执行 ``uv sync --group dev``）；
- 可选：通过 ``CTREE_HOST`` / ``CTREE_HTTP_PORT`` / ``CTREE_GRPC_PORT`` /
  ``CTREE_TRANSPORT``（``http`` 或 ``grpc``）覆盖默认连接参数。
"""

from __future__ import annotations

import os
from typing import Any

from celestialtree import Client as CelestialTreeClient
from dotenv import load_dotenv

from celestialflow import Observer, TaskExecutor, TaskGraph
from celestialflow.observer import Event, TaskSuccessEvent

load_dotenv()

CTREE_HOST: str = os.getenv("CTREE_HOST", "127.0.0.1")
CTREE_HTTP_PORT: int = int(os.getenv("CTREE_HTTP_PORT", "7777"))
CTREE_GRPC_PORT: int = int(os.getenv("CTREE_GRPC_PORT", "7778"))
CTREE_TRANSPORT: str = os.getenv("CTREE_TRANSPORT", "http")


class EventCapture(Observer):
    """记录指定节点最后一次成功任务的事件 ID，供后续溯源查询使用。"""

    def __init__(self, node: str) -> None:
        """
        初始化事件捕获器。

        :param node: 需要观察的节点名称
        """
        self.node = node
        self.input_id: int | None = None
        self.success_id: int | None = None
        self.success_count = 0

    def on_event(self, event: Event) -> None:
        """
        接收观测事件，记录目标节点最近一次成功任务的输入/成功事件 ID。

        :param event: 任意观测事件
        """
        match event:
            case TaskSuccessEvent() if event.node == self.node:
                self.success_count += 1
                self.input_id = event.task_id
                self.success_id = event.success_id
            case _:
                pass


def _add(task: tuple[int, int]) -> int:
    """把二元组任务相加。"""
    x, y = task
    return x + y


def _square(x: int) -> int:
    """对输入求平方。"""
    return x * x


def _client_name(target: Any) -> str:
    """
    返回目标对象当前事件客户端的完整类型名。

    :param target: 持有 ``ctree_client`` 属性的任务图或节点
    :return: ``模块名.类名`` 形式的事件客户端类型名
    """
    client_type = type(target.ctree_client)
    return f"{client_type.__module__}.{client_type.__name__}"


def _collect_ids(node: dict[str, Any], link_key: str) -> list[int]:
    """
    按指定链接字段递归收集事件 ID。

    CelestialTree 的 ``provenance`` 使用 ``parents`` 嵌套，``descendants`` 使用
    ``children`` 嵌套，二者形状一致，因此共用本函数。

    :param node: 嵌套事件节点
    :param link_key: 递归字段名，``"parents"`` 或 ``"children"``
    :return: 深度优先顺序的事件 ID 列表
    """
    ids: list[int] = []

    def walk(current: dict[str, Any]) -> None:
        ids.append(int(current["id"]))
        for child in current.get(link_key, []):
            walk(child)

    walk(node)
    return ids


def _print_trace(client: CelestialTreeClient, capture: EventCapture) -> None:
    """
    查询并打印最后一次成功任务的溯源信息。

    :param client: CelestialTree 客户端
    :param capture: 已记录事件 ID 的捕获器
    """
    if capture.success_id is None or capture.input_id is None:
        print("  未捕获到成功事件，跳过溯源查询。")
        return

    success_id = capture.success_id
    input_id = capture.input_id
    event = client.get_event(success_id)
    print(f"  最后一次成功事件: {success_id}（共 {capture.success_count} 次成功）")
    print(f"  event       : type={event['type']}, parents={event['parents']}")
    print(f"  input event : {client.get_event(input_id)['type']} [{input_id}]")
    print(f"  ancestors   : {client.ancestors(success_id)}")
    print(
        "  provenance  : "
        + " <- ".join(map(str, _collect_ids(client.provenance(success_id), "parents")))
    )
    print(
        "  descendants : "
        + " -> ".join(
            map(str, _collect_ids(client.descendants(input_id), "children"))
        )
    )


def demo_graph_with_ctree(client: CelestialTreeClient) -> None:
    """
    演示任务图通过 ``set_ctree()`` 把事件客户端换成 CelestialTree。

    该入口会把客户端同步注入到图中所有节点：``Adder -> Square``。

    :param client: CelestialTree 客户端
    """
    print("\n=== 任务图：graph.set_ctree(client) ===")
    adder = TaskExecutor("Adder", _add, execution_mode="thread", max_workers=2)
    squarer = TaskExecutor("Square", _square, execution_mode="thread", max_workers=2)

    graph = TaskGraph("demo_ctree_graph", graph_mode="thread")
    graph.set_nodes([adder, squarer])
    graph.connect([adder], [squarer])

    capture = EventCapture("Square")
    graph.add_observer(capture)

    print(f"  默认事件客户端: {_client_name(graph)}")
    graph.set_ctree(client)
    print(f"  替换后事件客户端: {_client_name(graph)}")

    graph.run({"Adder": [(1, 2), (3, 4), (5, 6)]})
    _print_trace(client, capture)


def demo_executor_with_ctree(client: CelestialTreeClient) -> None:
    """
    演示单个 ``TaskExecutor`` 通过 ``set_ctree()`` 接入 CelestialTree。

    不经过任务图时，节点自身持有的事件客户端同样可以被替换。

    :param client: CelestialTree 客户端
    """
    print("\n=== 单节点：executor.set_ctree(client) ===")
    executor = TaskExecutor(
        "StandaloneSquare",
        _square,
        execution_mode="thread",
        max_workers=2,
    )
    capture = EventCapture(executor.get_name())
    executor.add_observer(capture)

    print(f"  默认事件客户端: {_client_name(executor)}")
    executor.set_ctree(client)
    print(f"  替换后事件客户端: {_client_name(executor)}")

    executor.run([2, 3, 4])
    _print_trace(client, capture)


def main() -> None:
    """连接 CelestialTree 并运行两个接入示例。"""
    client = CelestialTreeClient(
        host=CTREE_HOST,
        http_port=CTREE_HTTP_PORT,
        grpc_port=CTREE_GRPC_PORT,
        transport=CTREE_TRANSPORT,
    )

    if not client.health():
        print(f"无法连接 CelestialTree: {CTREE_HOST}:{CTREE_HTTP_PORT}")
        print(
            "请先启动 CelestialTree 服务，或通过 CTREE_HOST / CTREE_HTTP_PORT / "
            "CTREE_GRPC_PORT / CTREE_TRANSPORT 配置连接参数。"
        )
        return

    print(f"CelestialTree version: {client.version()} transport={CTREE_TRANSPORT}")
    demo_graph_with_ctree(client)
    demo_executor_with_ctree(client)


if __name__ == "__main__":
    main()
