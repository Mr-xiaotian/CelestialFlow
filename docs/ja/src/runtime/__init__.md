# src/celestialflow/runtime/__init__.py

> 📅 最終更新日: 2026/10/09

Runtime モジュールは CelestialFlow タスク実行ランタイムのコアインフラストラクチャを提供し、タスクエンベロープ（Envelope）、キュー（Queue）などのコンポーネントを含みます。

## モジュール概要

Runtime モジュールは、タスク実行プロセスにおけるデータラッパーとキュー通信を管理します。タスクスケジューリング自体は担当せず（スケジューリングは Graph モジュールが担当）、上層が利用するランタイム基礎コンポーネントを提供します。

### 公開エクスポートシンボル (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # タスクエンベロープ
    TaskInQueue,  # タスク入力キュー
    TaskOutQueue,  # タスク出力キュー
)
```

`__all__ = ["TaskEnvelope", "TaskInQueue", "TaskOutQueue"]`

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

### ユーティリティモジュール

3. **util_errors.py**
   - **役割**: 完全な例外定義体系
   - **対象**: 設定例外、グラフ構造例外、実行時例外、外部サービス例外、タスクロジック例外
   - 例外一覧の詳細は `util_errors.md` を参照

4. **util_types.py**
   - **役割**: ランタイム型定義とデータ構造
   - **含まれる型**: `TerminationSignal`、`TERMINATION_SIGNAL`、`TerminationIdPool`、`NoOpContext`、`ValueWrapper`、`NodeStatus`、`CTreeEvent`、`NodeMetrics`、`MetricsView`

5. **util_event.py**
   - **役割**: イベントクライアント抽象インターフェースとローカル実装
   - **主要クラス**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

6. **util_constant.py**
   - **役割**: ランタイム定数定義（ログレベルマッピングなど）

7. **util_config.py**
   - **役割**: ランタイム設定ロード（pyproject.toml からログレベル、レポートアドレス、レポートスイッチを読み取りなど）

8. **util_format.py**
   - **役割**: 汎用フォーマットツール（文字列切り詰め、テーブルレンダリング、値ごとのクラスタリング）

> 説明：指標（Metrics）とレポート（Reporter）関連の実装は、Runtime モジュールから `observer` / `observability` 領域へ移転しました。Runtime には `util_types` で定義された読み取り専用の指標スナップショット型（`NodeMetrics`）とビュー・プロトコル（`MetricsView`）のみが残っています。

## モジュール関連

### 内部関連
- `TaskInQueue`/`TaskOutQueue` は `util_types` の `TerminationSignal`/`TerminationIdPool` を使用
- `TaskInQueue` は内部で `util_errors` の `DuplicateNodeError`、`UnknownNodeError`、`TerminationMergeError` を使用
- すべてのエラーは `CelestialFlowError` およびそのサブクラスを通じて統一的に処理

### 外部関連
- **Graph モジュールとの連携**: `TaskGraph` は各種タスクノードを管理し、ノード間通信パイプラインとして `TaskInQueue`/`TaskOutQueue` を使用
- **Node モジュールとの連携**: ノードオブジェクトはデータ送受信の際に `TaskEnvelope`、`TaskInQueue`/`TaskOutQueue` を使用し、`util_types` の `MetricsView` を通じて読み取り専用の指標ビューを読み取る

## 使用例

以下の例は runtime モジュールの各基本コンポーネントの使用方法を示します。

```python
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope：タスクエンベロープの作成とアクセス
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"タスクデータ: {envelope.get_task()}")
print(f"タスクID: {envelope.get_id()}")
```

```python
# 2. TaskInQueue / TaskOutQueue：キュー通信
from queue import Queue as ThreadQueue

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
```

## ベストプラクティス

1. **キュー通信**: `maxsize` を適切に設定してメモリ溢れを避ける
2. **複数ソース管理**: `add_source_name()` / `add_queue()` で重複を防ぎながら上流・下流チャネルを登録する
3. **終了マージ**: `TaskInQueue` がすべての上流終了シグナルを集めた後に `TerminationIdPool` へマージする