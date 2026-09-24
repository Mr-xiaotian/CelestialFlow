# src/celestialflow/runtime/__init__.py

> 📅 最終更新日: 2026/09/24

Runtime モジュールは CelestialFlow タスク実行ランタイムのコアインフラストラクチャを提供し、タスクエンベロープ（Envelope）、キュー（Queue）、メトリクス統計（Metrics）などのコンポーネントを含みます。

## モジュール概要

Runtime モジュールは、タスク実行プロセスにおけるデータラッパー、キュー通信、メトリクス統計を管理します。タスクスケジューリング自体は担当せず（スケジューリングは Graph モジュールが担当）、上層が利用するランタイム基礎コンポーネントを提供します。

### 公開エクスポートシンボル (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # 任务信封
    TaskInQueue,  # 任务输入队列
    TaskMetrics,  # 任务指标统计
    TaskOutQueue,  # 任务输出队列
)
```

`__all__ = ["TaskEnvelope", "TaskInQueue", "TaskMetrics", "TaskOutQueue"]`

> **注意**：`util_constant`、`util_errors`、`util_event`、`util_types`、`util_config`、`util_format` などのユーティリティモジュールのシンボルは `runtime/__init__.py` の `__all__` に**含まれていません**。完全修飾パスでインポートしてください（例: `from celestialflow.runtime.util_errors import ConfigurationError`）。

## ファイル説明

### コアランタイムコンポーネント

1. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **役割**: タスク入出力キュー。ノード間のデータ転送と終了シグナルマージを実現します
   - **キュー種別**:
     - `TaskInQueue`: タスク入力キュー。複数上流からのタスクと終了シグナルを集約
     - `TaskOutQueue`: タスク出力キュー。結果を 1 つ以上の下流キューチャネルにブロードキャスト
   - **主要機能**: 終了シグナルマージ、ソース名管理、キューチャネルの動的追加

2. **core_envelope.py** (`TaskEnvelope`)
   - **役割**: タスクデータラッパー。元タスクとその ID をカプセル化します
   - **格納情報**: タスクデータ（`_task`）、タスク ID（`_id`）
   - **主要機能**: データのカプセル化とアクセス

3. **core_metrics.py** (`TaskMetrics`)
   - **役割**: タスク実行メトリクス統計。外部注入 / 上流受信 / 成功 / 失敗 / 重複のカウントを管理します
   - **主要機能**: スレッドセーフカウンター、上流/下流のノード別カウント、オブザーバーコールバック、リトライ可能例外の設定、タスク完了判定、実測のビジー時間

### ユーティリティモジュール

4. **util_errors.py**
   - **役割**: 完全な例外定義体系
   - **対象**: 設定例外、グラフ構造例外、実行時例外、外部サービス例外、タスクロジック例外
   - 例外一覧の詳細は `util_errors.md` を参照

5. **util_types.py**
   - **役割**: ランタイム型定義とデータ構造
   - **含まれる型**: `TerminationSignal`、`TERMINATION_SIGNAL`、`TerminationIdPool`、`NoOpContext`、`ValueWrapper`、`StageStatus`、`CTreeEvent`

6. **util_event.py**
   - **役割**: イベントクライアント抽象インターフェースとローカル実装
   - **主要クラス**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

7. **util_constant.py**
   - **役割**: ランタイム定数定義（ログレベルマッピングなど）

8. **util_config.py**
   - **役割**: ランタイム設定ロード（pyproject.toml からログレベルを読み取りなど）

9. **util_format.py**
   - **役割**: 汎用フォーマットツール（文字列切り詰め、テーブルレンダリング、値ごとのクラスタリング）

## モジュール関連

### 内部関連
- `TaskInQueue`/`TaskOutQueue` は `util_types` の `TerminationSignal`/`TerminationIdPool` を使用
- `TaskMetrics` は `util_types` の `ValueWrapper` を使用し、`StageStatus` でライフサイクル状態を表現
- すべてのエラーは `CelestialFlowError` およびそのサブクラスを通じて統一的に処理

### 外部関連
- **Graph モジュールとの連携**: `TaskGraph` は `TaskExecutor` / `TaskSplitter` / `TaskRouter` などのノードを管理し、ノード間通信パイプラインとして `TaskInQueue`/`TaskOutQueue` を使用
- **Node モジュールとの連携**: ノードオブジェクト（`BaseTaskNode` およびそのサブクラス）は `TaskMetrics` を保持し、`TaskInQueue`/`TaskOutQueue` を使用してデータを送受信

## 使用例

以下の例は runtime モジュールの各基本コンポーネントの使用方法を示します。

```python
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope：创建和访问任务信封
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"任务数据: {envelope.get_task()}")
print(f"任务ID: {envelope.get_id()}")
```

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# 2. TaskMetrics：指标统计
metrics = TaskMetrics()

# 模拟任务处理过程：外部注入 3 个 + 上游接收 2 个
metrics.add_external_input_count(3)
metrics.set_upstream_counter("upstream", ValueWrapper(value=2))
metrics.add_success_count(3)
metrics.add_fail_count(1)
metrics.add_duplicate_count(1)

# 查询各项计数
print(f"输入: {metrics.get_input_count()}")  # 5
print(f"成功: {metrics.get_success_count()}")  # 3
print(f"失败: {metrics.get_fail_count()}")  # 1
print(f"重复: {metrics.get_duplicate_count()}")  # 1
print(f"全部完成: {metrics.is_tasks_finished()}")

# 获取快照字典
counts = metrics.get_counts()
print(f"待处理: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue：队列通信
from queue import Queue as ThreadQueue

# 创建输入队列
in_queue = TaskInQueue(out_name="processor")
in_queue.add_source_name("producer")

# 创建输出队列
out_queue = TaskOutQueue(in_name="processor")
consumer_queue = ThreadQueue()
out_queue.add_queue("consumer", consumer_queue)

# 生产任务
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)
out_queue.put(envelope_a)

# 消费任务
retrieved = in_queue.get()
print(f"出队任务: {retrieved.get_task()}")
```

## ベストプラクティス

1. **クリティカルタスク**: `set_retry_exceptions()` でリトライ可能な例外型を設定
2. **ノード別統計**: `set_upstream_counter()` / `set_downstream_counter()` でノード間のトラフィックを追跡
3. **キュー通信**: `maxsize` を適切に設定してメモリ溢れを避ける
