# src/celestialflow/runtime/__init__.py

> 📅 最終更新日: 2026/10/30

Runtime モジュールは CelestialFlow タスク実行ランタイムのコアインフラストラクチャを提供し、実行時設定（`ReportConfig`）、タスクエンベロープ（Envelope）、キュー（Queue）などのコンポーネントを含みます。

## モジュール概要

Runtime モジュールは、タスク実行プロセスにおけるデータラッピング、キュー通信、実行時設定型を管理します。タスクスケジューリング自体は担当せず（スケジューリングは Graph モジュールが担当）、上層が利用するランタイム基礎コンポーネントを提供します。

### 公開エクスポートシンボル (`__all__`)

```python
from celestialflow.runtime import (
    DEFAULT_REPORT_URL,  # デフォルトのレポート先アドレス定数
    ReportConfig,  # リモートレポート設定（frozen 設定オブジェクト）
    TaskEnvelope,  # タスクエンベロープ
    TaskInQueue,  # タスク入力キュー
    TaskOutQueue,  # タスク出力キュー
)
```

`__all__ = ["DEFAULT_REPORT_URL", "ReportConfig", "TaskEnvelope", "TaskInQueue", "TaskOutQueue"]`

> **注意**：`core_*` ファイル内のシンボルのみがエクスポートされます。`util_constant`、`util_errors`、`util_event`、`util_format`、`util_log_level`、`util_types` などの `util_*` モジュールのシンボルは `runtime/__init__.py` の `__all__` に**含まれていません**。完全修飾パスでインポートしてください（例: `from celestialflow.runtime.util_errors import ConfigurationError`、`from celestialflow.runtime.util_log_level import normalize_log_level`）。

## ファイル説明

### コアランタイムコンポーネント

1. **core_config.py** (`DEFAULT_REPORT_URL`, `ReportConfig`)
   - **役割**: ランタイムエントリから明示的に渡されるレポート設定を定義します。`report=ReportConfig(...)` でレポートを有効化し、`report=None` でレポートを無効化します
   - **主要機能**: デフォルトアドレス定数、構築時のアドレス検証（`http`/`https`）、末尾の `/` を除去する正規化
   - 詳細は `core_config.md` を参照

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **役割**: タスク入出力キュー。ノード間のデータ転送と終了シグナルマージを実現します
   - **キュー種別**:
     - `TaskInQueue`: タスク入力キュー。複数上流からのタスクと終了シグナルを集約
     - `TaskOutQueue`: タスク出力キュー。結果を 1 つ以上の下流キューチャネルにブロードキャスト
   - **主要機能**: 終了シグナルマージ、ソース名管理、キューチャネルの動的追加

3. **core_envelope.py** (`TaskEnvelope`)
   - **役割**: タスクデータラッパー。元タスクとその ID をカプセル化します
   - **格納情報**: タスクデータ（`_task`）、タスク ID（`_id`）
   - **主要機能**: データのカプセル化とアクセス

### ユーティリティモジュール（外部非公開）

4. **util_errors.py**
   - **役割**: 完全な例外定義体系
   - **対象**: 設定例外、グラフ構造例外、実行時例外、外部サービス例外、タスクロジック例外
   - 例外一覧の詳細は `util_errors.md` を参照

5. **util_types.py**
   - **役割**: ランタイム型定義とデータ構造
   - **含まれる型**: `TerminationSignal`、`TERMINATION_SIGNAL`、`TerminationIdPool`、`NoOpContext`、`ValueWrapper`、`NodeStatus`、`CTreeEvent`、`NodeMetrics`、`MetricsView`

6. **util_event.py**
   - **役割**: イベントクライアント抽象インターフェースとローカル実装
   - **主要クラス**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

7. **util_constant.py**
   - **役割**: ランタイム定数定義（ログレベルマッピングテーブル `LEVEL_DICT`）

8. **util_log_level.py**
   - **役割**: ログレベルのデフォルト値 `DEFAULT_LOG_LEVEL` と正規化・検証 `normalize_log_level()`（ランタイムエントリ内部でのみ使用）

9. **util_format.py**
   - **役割**: 汎用フォーマットツール（文字列切り詰め、テーブルレンダリング、値ごとのクラスタリング）

> 説明：指標（Metrics）とレポート（Reporter）関連の実装は `observer` / `reporter` 領域にあります。Runtime には `util_types` で定義された読み取り専用の指標スナップショット型（`NodeMetrics`）とビュー・プロトコル（`MetricsView`）、および `core_config` のレポート**設定オブジェクト**（レポート実行ロジックは含みません）のみが残っています。

## モジュール関連

### 内部関連
- `core_queue` は `util_types` の `TerminationSignal`/`TerminationIdPool` を使用
- `core_queue` は `util_errors` の `DuplicateNodeError`、`UnknownNodeError`、`TerminationMergeError` を使用
- `core_config` は `util_errors` の `ConfigurationError` を使用
- `util_log_level` は `util_constant` の `LEVEL_DICT` と `util_errors` の `ConfigurationError` / `InvalidOptionError` を使用
- すべてのエラーは `CelestialFlowError` およびそのサブクラスを通じて統一的に処理

### 外部関連
- **Graph モジュールとの連携**: `TaskGraph.run()` / `run_async()` / `restore_db()` の `report` パラメータの型が `ReportConfig` です；`TaskGraph` はノード間通信パイプラインとして `TaskInQueue`/`TaskOutQueue` を使用
- **Assembly モジュールとの連携**: `run_graph_resources()` は `report` が `None` かどうかに基づいてリモートレポートリソースを組み立てるかどうかを決定
- **Node モジュールとの連携**: ノードオブジェクトはデータ送受信の際に `TaskEnvelope`、`TaskInQueue`/`TaskOutQueue` を使用し、`util_types` の `MetricsView` を通じて読み取り専用の指標ビューを読み取る
- **パッケージルート**: `celestialflow/__init__.py` が `ReportConfig` を再エクスポート（`from celestialflow import ReportConfig`）

## 使用例

以下の例は runtime モジュールの各基本コンポーネントの使用方法を示します。

```python
from celestialflow.runtime import (
    DEFAULT_REPORT_URL,
    ReportConfig,
    TaskEnvelope,
    TaskInQueue,
    TaskOutQueue,
)

# 1. ReportConfig：レポート設定
config = ReportConfig()  # デフォルトアドレスを使用
print(f"レポートアドレス: {config.url}")  # http://127.0.0.1:5005
print(f"デフォルトアドレス定数: {DEFAULT_REPORT_URL}")

custom = ReportConfig("https://flow.example.com/api/")
print(f"正規化後: {custom.url}")  # https://flow.example.com/api

# 2. TaskEnvelope：タスクエンベロープの作成とアクセス
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"タスクデータ: {envelope.get_task()}")
print(f"タスクID: {envelope.get_id()}")
```

```python
# 3. TaskInQueue / TaskOutQueue：キュー通信
from queue import Queue as ThreadQueue

from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue

# 入力キューを作成
in_queue = TaskInQueue(out_name="processor")
in_queue.add_source_name("producer")

# 出力キューを作成
out_queue = TaskOutQueue(in_name="processor")
consumer_queue = ThreadQueue()
out_queue.add_queue("consumer", consumer_queue)

# タスクを生成
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)
out_queue.put(envelope_a)

# タスクを消費
retrieved = in_queue.get()
print(f"デキューしたタスク: {retrieved.get_task()}")
print(f"下流が受信: {consumer_queue.get().get_task()}")
```

```python
# 4. ReportConfig をグラフのランタイムエントリへ渡す
from celestialflow import TaskExecutor, TaskGraph

from celestialflow.runtime import ReportConfig

graph = TaskGraph(name="RuntimeDemo")
graph.set_nodes([TaskExecutor("worker", lambda x: x * 2)])
graph.run({"worker": [1, 2, 3]}, report=ReportConfig())
```

## ベストプラクティス

1. **レポートスイッチ**: レポートしたい場合は `ReportConfig` を構築して `report=` に渡し、レポートしない場合はデフォルトの `None` のままにします。`pyproject.toml` から暗黙的に読み込まれる動作はありません
2. **キュー通信**: `maxsize` を適切に設定してメモリ溢れを避ける
3. **複数ソース管理**: `add_source_name()` / `add_queue()` で重複を防ぎながら上流・下流チャネルを登録する
4. **終了マージ**: すべての上流終了シグナルが揃った後に `TaskInQueue` が `TerminationIdPool` へマージする
