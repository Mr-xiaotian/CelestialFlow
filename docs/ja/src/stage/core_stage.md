# TaskStage

> 📅 最終更新日: 2026/06/22

`TaskStage` は `TaskGraph` を構築する基本単位です。`TaskExecutor` を継承し、グラフ構造関連の接続機能と `stage_mode` 制御ロジックを追加しています。

> 注意：`TaskStage` も使い捨てオブジェクトです。通常は `TaskGraph` に管理され、一度の完全実行に参加します。実行終了後、キューバインディング、カウント状態、グラフ内関連付けが安全にリセットされることは保証されません。

## 継承関係

`TaskExecutor` -> `TaskStage`

`TaskStage` は `TaskExecutor` のすべてのコア機能（実行モード、リトライ、メトリクス監視など）を継承し、ノード間の接続ロジックを追加しています。

## コアコンセプト

- **Stage Mode**: タスクグラフ内でのノードのスケジューリングロジックモード。
  - `serial`: シリアルモード。メインプロセス内で実行。
  - `thread`: スレッドモード。メインプロセス内で独立スレッドとして実行。
- **Execution Mode**: ノード内部でタスクを処理する並行モード（`serial`, `thread`, `async`）。`TaskExecutor` から継承。
- **トポロジー関係**: ノード間の上下游接続関係は `TaskGraph` が管理し、`TaskStage` 自身は隣接リストを保持しません。

## 初期化

```python
class TaskStage[T, R](TaskExecutor[T, R]):
    def __init__(
        self,
        name: str,
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
        stage_mode: str = "serial",
        **kwargs: Any,
    ):
        """
        :param name: 节点名称（唯一标识）
        :param func: 执行函数
        :param stage_mode: 在图中的运行模式 ('serial' 或 'thread')
        :param kwargs: 透传给 TaskExecutor 的参数 (execution_mode, max_workers, max_retries 等)
        """
```

例：
```python
stage_a = TaskStage("StageA", func=process_a, execution_mode="thread", stage_mode="thread")
stage_b = TaskStage("StageB", func=process_b, execution_mode="serial", stage_mode="thread")

# 创建图并连接节点
graph = TaskGraph()
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])
```

## 設定メソッド

### set_stage_mode

```python
def set_stage_mode(self, stage_mode: str):
    """
    设置节点在任务图中的执行模式。
    :param stage_mode: 'serial' 或 'thread'
    :raises StageModeError: 如果模式不支持
    """
```

### set_inlet

```python
def set_inlet(self, fallback_inlet: FallbackInlet, log_inlet: LogInlet) -> None:
    """
    初始化收集器，将 fallback/log 收集器接入当前 stage。
    :param fallback_inlet: fallback 收集器
    :param log_inlet: 日志收集器
    """
```

### TaskExecutor から継承した設定メソッド

| メソッド | 説明 |
|------|------|
| `set_execution_mode(mode)` | ノード内部のタスク処理モードを設定（`serial`/`thread`/`async`） |
| `set_name(name)` | ノード名を設定 |
| `set_log_level(level)` | ログレベルを設定 |

## 接続バインディング

### prev_binding

```python
def prev_binding(self, pending_prev_binding: TaskStage[Any, Any]) -> None:
    """
    绑定单个前置节点，将其计数器注册到当前 stage 的 task_counter 中。
    """
```

### get_binding_counter

```python
def get_binding_counter(self, _downstream_name: str) -> Any:
    """
    返回下游 stage 应绑定的计数器，子类可覆写（默认返回 success_counter）。
    """
```

## 状態管理

`TaskStage` は `StageStatus` 列挙型を使用してライフサイクルを管理します：

```mermaid
stateDiagram-v2
    [*] --> NOT_STARTED: __init__()
    NOT_STARTED --> RUNNING: start_stage()
    RUNNING --> RUNNING: タスク処理中
    RUNNING --> STOPPED: finally ブロック
    STOPPED --> [*]
```

### 状態メソッド

```python
# 标记运行
def mark_running(self) -> None:
    """标记：stage 正在运行。"""

# 标记停止
def mark_stopped(self) -> None:
    """标记：stage 已停止（正常结束时在 finally 里调用）。"""

# 获取状态
def get_status(self) -> StageStatus:
    """读取当前状态（返回 StageStatus 枚举）。"""
```

## 実行メカニズム

### start / start_async（直接呼び出し禁止）

`TaskStage` が `TaskGraph` に管理されている場合、`start()` または `start_async()` を直接呼び出すと `GraphManagedError` が送出されます。`TaskGraph.start_graph()` による統一起動が必要です。

### start_stage

`TaskGraph` が起動されると、このメソッドが呼び出されてノードの実際の実行が開始されます。

```python
def start_stage(self):
    """
    根据 execution_mode 的值，选择串行、线程或异步执行任务。
    记录启动/结束日志，管理状态转换。
    """
```

ライフサイクル制約：

- `TaskStage` の実行時状態は、起動フェーズで `TaskGraph` によって確立・駆動されます。
- 現在の実装は、複数回の再利用に対応した完全なリセットセマンティクスを提供していません。
- 同じノードを再度実行する必要がある場合は、新しい `TaskStage` を作成し、新しい `TaskGraph` に再接続することを推奨します。

### drain_task_queue

```python
def drain_task_queue(self) -> None:
    """清空任务队列，将所有剩余任务移至失败队列并标记为 UnconsumedError。"""
```

## 状態スナップショット

```python
def get_summary(self) -> dict[str, Any]:
    """
    获取当前节点的状态摘要。
    返回继承自 TaskExecutor 的字段（name, func_name, execution_mode, max_workers）
    外加 stage_mode。
    """
```

## 使用例

以下は `TaskStage` の完全な使用法を示す例で、複数の実行モード、状態管理、グラフ接続を含みます。

### 基本的な使用法（serial モード）

```python
from celestialflow import TaskGraph, TaskStage

def step1(x: int) -> int:
    return x + 5

def step2(x: int) -> int:
    return x * 3

stage1 = TaskStage("Step1", func=step1, execution_mode="serial", stage_mode="serial")
stage2 = TaskStage("Step2", func=step2, execution_mode="serial", stage_mode="serial")

chain = TaskGraph()
chain.set_stages([stage1, stage2])
chain.connect([stage1], [stage2])
chain.start_graph({stage1.get_name(): [1, 2, 3, 4, 5]})

for name, runtime in chain.stage_runtime_dict.items():
    pairs = runtime.stage.get_success_pairs()
    print(f"{name}: {len(pairs)} 成功")
```

### thread 実行モードの使用（I/O 密集型）

```python
import time
from celestialflow import TaskGraph, TaskStage

def io_task(x: int) -> int:
    time.sleep(0.05)
    return x * 10

stage_a = TaskStage(
    name="IOWorker",
    func=io_task,
    execution_mode="thread",
    max_workers=4,
    stage_mode="thread",
)

graph = TaskGraph()
graph.set_stages([stage_a])
graph.start_graph({stage_a.get_name(): list(range(20))})
```

### 非同期モード（async）

```python
import asyncio
from celestialflow import TaskStage

async def async_process(x: int) -> int:
    await asyncio.sleep(0.01)
    return x ** 2

async_stage = TaskStage(
    name="AsyncProcessor",
    func=async_process,
    execution_mode="async",
    max_workers=4,
)
print(f"异步阶段摘要: {async_stage.get_summary()}")
```

### 状態管理

```python
from celestialflow import TaskStage
from celestialflow.runtime.util_types import StageStatus

stage = TaskStage("StatusDemo", func=lambda x: x)

print(f"初始状态: {stage.get_status().name}")  # NOT_STARTED
stage.mark_running()
print(f"运行中: {stage.get_status().name}")   # RUNNING
stage.mark_stopped()
print(f"已停止: {stage.get_status().name}")   # STOPPED
```

## 注意事項

1. **名前の一意性**: 同一の `TaskGraph` 内では、各 `TaskStage` の `name` は一意でなければならない。
2. **非同期サポート**: `execution_mode` が `async` に設定されている場合、`func` はコルーチン関数である必要がある。
3. **Graph 管理**: `TaskGraph` に管理されている Stage では `start()` / `start_async()` を直接呼び出せない。
4. **使い捨て**: 実行完了後、同一の `TaskStage` インスタンスを再利用すべきではない。
