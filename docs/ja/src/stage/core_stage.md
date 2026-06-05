# TaskStage

> 📅 最終更新日: 2026/06/05

`TaskStage` は `TaskGraph` を構築する基本単位です。`TaskExecutor` を継承し、グラフ構造に関する接続機能と `stage_mode` 制御ロジックを追加しています。

> 注意: `TaskStage` も使い切りオブジェクトです。キュー接続、グラフ結線、実行時カウンタは 1 回の実行ライフサイクル向けに設計されており、完了後の再利用は前提とされていません。

## 継承関係

`TaskExecutor` -> `TaskStage`

`TaskStage` は `TaskExecutor` のすべてのコア機能（実行モード、リトライ、メトリクス監視など）を継承し、ノード間の接続ロジックを追加しています。

## 主要な概念

- **Stage Mode**: タスクグラフ内でのノードのスケジューリングロジックモード。
  - `serial`: シリアルモード、メインプロセスで実行。
  - `thread`: スレッドモード、メインプロセス内で独立したスレッドとして実行。
- **Execution Mode**: ノード内部でタスクを処理する並行モード（`serial`、`thread`、`async`）。
- **トポロジ関係**: ノード間の上流・下流の接続関係は `TaskGraph` によって管理され、`TaskStage` 自身は隣接表を保持しません。

## 初期化

```python
class TaskStage(TaskExecutor):
    def __init__(
        self,
        name: str,
        func: Callable[..., Any],
        stage_mode: str = "serial",
        **kwargs: Any,
    ):
        """
        :param name: ノード名（一意の識別子）
        :param func: 実行関数
        :param stage_mode: グラフ内での実行モード（'serial' または 'thread'）
        :param kwargs: TaskExecutor に転送されるパラメータ（execution_mode, max_workers, max_retries など）
        """
```

例：
```python
stage_a = TaskStage("StageA", func=process_a, execution_mode="thread", stage_mode="thread")
stage_b = TaskStage("StageB", func=process_b, execution_mode="serial", stage_mode="thread")

# グラフを作成しノードを接続
graph = TaskGraph()
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])
```

## 設定メソッド

### set_stage_mode

```python
def set_stage_mode(self, stage_mode: str):
    """
    タスクグラフ内でのノードの実行モードを設定。
    :param stage_mode: 'serial' または 'thread'
    :raises StageModeError: モードがサポートされていない場合
    """
```

### set_execution_mode

> ⚠️ このメソッドは `TaskExecutor` から継承されています。`TaskStage` はオーバーライドしていません。

```python
def set_execution_mode(self, execution_mode: str):
    """
    ノード内部のタスク処理モードを設定。

    :param execution_mode: 'serial'、'thread'、または 'async'
    :raises ExecutionModeError: モードがサポートされていない場合
    """
```

### set_name

> ⚠️ このメソッドは `TaskExecutor` から継承されています。`TaskStage` はオーバーライドしていません。

```python
def set_name(self, name: str):
    """
    ノード名を設定。
    """
```

## 状態管理

`TaskStage` は `StageStatus` 列挙型でライフサイクルを管理します：

- `NOT_STARTED` (0): 初期状態。
- `RUNNING` (1): 起動済み、キューを監視中。
- `STOPPED` (2): 正常停止または異常終了。

### 状態メソッド

```python
# 実行中としてマーク
def mark_running(self) -> None:
    """マーク：stage が実行中です。"""

# 停止としてマーク
def mark_stopped(self) -> None:
    """マーク：stage が停止しました（正常終了時に finally で呼び出されます）。"""

# 状態を取得
def get_status(self) -> StageStatus:
    """現在の状態を読み取ります（StageStatus 列挙型を返します）。"""
```

## 実行メカニズム

`TaskGraph` が起動すると、各 `TaskStage` は `stage_mode` に基づいて実行方法を決定します：

- **thread モード**: ノードは独立したスレッドで起動されます。
- **serial モード**: ノードはメインプロセスで直列実行されます（通常デバッグ用）。

### start_stage

`TaskGraph` が起動すると、このメソッドを呼び出してノードを起動します。

```python
def start_stage(self):
    """
    ノードの実行を開始し、execution_mode に基づいてスケジューラを選択。
    """
```

1. `_init_state()` を呼び出して内部状態を初期化。
2. 起動ログを記録。
3. 状態を `RUNNING` にマーク。
4. `TaskDispatch` ループに入りタスクを処理。
5. 完了後、リソースをクリーンアップし `STOPPED` にマーク。

## 状態スナップショット

```python
def get_summary(self) -> dict[str, Any]:
    """
    現在のノードの状態サマリーを取得。
    class_name、name、func_name、execution_mode、stage_mode を含む辞書を返します。
    """
```

## 実行モードの制限

`TaskStage` では、`execution_mode` の使用可能な値は制限されています：

```python
# 有効なモード
valid_modes = ("serial", "thread", "async")

# 注意：stage_mode と execution_mode は独立した設定です
```

## 継承による拡張

カスタム Stage を作成する際、以下のメソッドをオーバーライドできます：

```python
class MyStage(TaskStage):
    def get_args(self, task):
        """カスタム引数抽出"""
        return (task.data,)

    def process_result(self, task, result):
        """カスタム結果処理"""
        return {"data": result, "metadata": task.metadata}
```

## 使用例

以下に、複数の実行モード、状態管理、グラフ接続を含む `TaskStage` の完全な使用例を示します。

### 基本的な使用法（serial モード）

```python
from celestialflow import TaskGraph, TaskStage

# serial 実行モードで2つのステージを作成
def step1(x: int) -> int:
    return x + 5

def step2(x: int) -> int:
    return x * 3

stage1 = TaskStage(
    name="Step1",
    func=step1,
    execution_mode="serial",  # シングルスレッド順次実行
    stage_mode="serial",      # メインプロセスで実行
)
stage2 = TaskStage(
    name="Step2",
    func=step2,
    execution_mode="serial",
    stage_mode="serial",
)

# グラフを構築して実行
chain = TaskGraph()
chain.set_stages([stage1, stage2])
chain.connect([stage1], [stage2])
chain.start_graph({stage1.get_name(): [1, 2, 3, 4, 5]})

print(f"チェーンサマリー: {chain.get_graph_summary()}")
```

### thread 実行モードの使用（I/O 集約型）

```python
import time
from celestialflow import TaskGraph, TaskStage

def io_task(x: int) -> int:
    time.sleep(0.05)  # ネットワーク I/O をシミュレート
    return x * 10

stage_a = TaskStage(
    name="IOWorker",
    func=io_task,
    execution_mode="thread",  # スレッドプール並行
    max_workers=4,            # 4 つの並行スレッド
    stage_mode="thread",      # 独立したスレッドで実行
)

# スタンドアロン実行（グラフ構造外）
stage_a.start_stage()
```

### 非同期モード

```python
import asyncio
from celestialflow import TaskStage

async def async_process(x: int) -> int:
    await asyncio.sleep(0.01)  # 非同期 I/O をシミュレート
    return x ** 2

async_stage = TaskStage(
    name="AsyncProcessor",
    func=async_process,
    execution_mode="async",
    max_workers=4,
)
print(f"非同期ステージサマリー: {async_stage.get_summary()}")
```

### 状態管理

```python
from celestialflow import TaskStage
from celestialflow.runtime.util_types import StageStatus

stage = TaskStage("StatusDemo", func=lambda x: x)

print(f"初期状態: {stage.get_status().name}")  # NOT_STARTED

stage.mark_running()
print(f"実行中: {stage.get_status().name}")   # RUNNING

stage.mark_stopped()
print(f"停止済み: {stage.get_status().name}")   # STOPPED
```

### カスタムサブクラス

```python
from celestialflow import TaskStage

class MyCustomStage(TaskStage):
    def get_args(self, task):
        """カスタム引数抽出"""
        return (task["data"],)

    def process_result(self, task, result):
        """カスタム結果処理"""
        return {"original": task, "computed": result}

# カスタムステージを使用
stage = MyCustomStage("Custom", func=lambda x: x * 10)
print(f"サマリー: {stage.get_summary()}")
```

## 注意事項

1. **名前の一意性**: 同じ `TaskGraph` 内では、各 `TaskStage` の `name` は一意でなければなりません。重複すると `DuplicateNodeError` が発生します。
2. **非同期サポート**: `execution_mode` が `async` に設定されている場合、`func` はコルーチン関数である必要があります。
3. **リソースクリーンアップ**: ノードが停止すると、クライアント接続とクロージャリソースが自動的に解放されます。
