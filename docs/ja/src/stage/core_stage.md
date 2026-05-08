# TaskStage

> 📅 最終更新日: 2026/05/08

`TaskStage` は `TaskGraph` を構築する基本単位です。`TaskExecutor` を継承し、グラフ構造に関する接続機能を追加しています。

## 継承関係

`TaskExecutor` -> `TaskStage`

`TaskStage` は `TaskExecutor` のすべての実行機能（実行モード、リトライ、キャッシュなど）を保持し、ノード間の接続ロジックを追加しています。

## 主要な概念

- **Stage Mode**: グラフ内でのノードの実行モード。
  - `serial`: 直列モード、メインプロセスで実行。
  - `thread`: スレッドモード、メインプロセス内で独立したスレッドとして実行。
  - `process`: 並列モード、独立した子プロセスで実行。
- **トポロジ関係**: ノード間の上流・下流の接続関係は `TaskGraph` によって管理され（`graph.out_edges` / `graph.in_edges` を通じて）、ノード自身には保存されません。

## 初期化

```python
class TaskStage(TaskExecutor):
    def __init__(
        self,
        name,
        func,
        execution_mode="serial",
        max_workers=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_duplicate_check=True,
        log_level="SUCCESS",
        stage_mode="serial",
    ):
        ...
```

パラメータは `TaskExecutor` と同じで、`log_level` と `stage_mode` パラメータが追加されています。`TaskStage` の `execution_mode` は `serial`、`thread`、または `async` を指定できます（`process` モードは `stage_mode` で制御します）。

## グラフ構築メソッド

### graph.connect

`graph.connect(from_stages, to_stages)` を通じてノード間の接続関係を確立します。`stage_mode` と `name` は `TaskStage.__init__()` のコンストラクタ引数で渡されます。

```python
def connect(
    self,
    from_stages: list[TaskStage],
    to_stages: list[TaskStage],
):
    """
    上流ノードと下流ノードを接続します。

    :param from_stages: 上流ノードリスト
    :param to_stages: 下流ノードリスト
    """
```

例：
```python
stage_a = TaskStage("StageA", func=process_a, execution_mode="thread", stage_mode="process")
stage_b = TaskStage("StageB", func=process_b, execution_mode="serial", stage_mode="process")

# グラフを作成しノードを接続
graph = TaskGraph()
graph.set_stages(root_stages=[stage_a], stages=[stage_b])
graph.connect([stage_a], [stage_b])
```

### モード設定

```python
# ノードの実行モードを設定
def set_stage_mode(self, stage_mode: str):
    """
    グラフ内での現在のノードの実行モードを設定します。
    :param stage_mode: 'serial'、'thread'、または 'process'
    """

# ノードの実行モードを取得
def get_stage_mode(self) -> str:
    """
    グラフ内での現在のノードの実行モードを取得します。
    """
```

### 名前の設定

```python
def set_name(self, name: str):
    """
    現在のノード名を設定します。
    注意：名前を変更すると、タグは無効になり再生成されます。
    """
```

## 状態管理

`TaskStage` は `StageStatus` 列挙型で実行状態を管理します：

- `NOT_STARTED` (0): 未開始
- `RUNNING` (1): 実行中
- `STOPPED` (2): 停止済み

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

- **process モード**: ノードは独立した `Process` にラップされて起動され、他のノードから隔離されます。
- **serial モード**: ノードはメインプロセスで実行されます（通常デバッグ用）。

### start_stage

```python
def start_stage(
    self,
    input_queues: TaskInQueue,
    output_queues: TaskOutQueue,
    fail_queue: MPQueue,
    log_queue: MPQueue,
):
    """
    ノードの実行を開始します。

    :param input_queues: 入力キュー
    :param output_queues: 出力キュー
    :param fail_queue: 失敗キュー
    :param log_queue: ログキュー
    """
```

ノードは継続的に `input_queues` からタスクを取得し、実行（`TaskExecutor` のロジックを使用）し、結果を `output_queues` に投入します。

## 状態スナップショット

```python
def get_summary(self) -> dict:
    """
    現在のノードの状態スナップショットを取得します。
    含まれる情報：name, func_name, class_name, execution_mode, stage_mode
    """
```

## 実行モードの制限

`TaskStage` では、`execution_mode` の使用可能な値は制限されています：

```python
# 有効なモード
valid_modes = ("serial", "thread", "async")

# 注意：process モードは stage_mode で制御され、execution_mode ではありません
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

## 注意事項

1. **プロセスモード**: `stage_mode="process"` の場合、関数が pickle 可能であることを確認してください（lambda、ネストされた関数などは避けてください）。
2. **カウンターの連鎖**: 上流が `TaskSplitter` または `TaskRouter` の場合、カウンターは自動的に連鎖します。
3. **状態の共有**: `multiprocessing.Value` を使用して実装され、プロセス間の状態クエリをサポートします。
4. **タグの一意性**: タグは `名前[関数名]` で構成され、ログトレースとグラフトポロジの識別に使用されます。
