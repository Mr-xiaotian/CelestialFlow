# Runtime モジュール

> 📅 最終更新日: 2026/08/12

Runtime モジュールは CelestialFlow タスク実行ランタイムのコアインフラストラクチャを提供し、タスクエンベロープ（Envelope）、キュー（Queue）、メトリクス統計（Metrics）などのコンポーネントを含みます。

## モジュール概要

Runtime モジュールは、タスク実行プロセスにおけるデータラッパー、キュー通信、メトリクス統計を管理します。タスクスケジューリング自体は担当せず（スケジューリングは Stage モジュールが担当）、上層が利用するランタイム基礎コンポーネントを提供します。

### 公開エクスポートシンボル (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # タスクエンベロープ
    TaskInQueue,  # タスク入力キュー
    TaskMetrics,  # タスクメトリクス統計
    TaskOutQueue,  # タスク出力キュー
)
```

> **注意**：`util_constant`、`util_errors`、`util_estimators`、`util_event`、`util_hash`、`util_types`、`util_config`、`util_format` などのユーティリティモジュールのシンボルは `runtime/__init__.py` の `__all__` に**含まれていません**。完全修飾パスでインポートしてください（例: `from celestialflow.runtime.util_errors import ConfigurationError`）。

## ファイル説明

### コアランタイムコンポーネント

1. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **役割**: タスク入出力キュー。ノード間のデータ転送と終了シグナルマージを実現します
   - **キュー種別**:
     - `TaskInQueue`: タスク入力キュー。複数上流からのタスクと終了シグナルを集約
     - `TaskOutQueue`: タスク出力キュー。結果を 1 つ以上の下流キューチャネルにブロードキャスト
   - **主要機能**: 終了シグナルマージ、ソース名管理、キューチャネルの動的追加

2. **core_envelope.py** (`TaskEnvelope`)
   - **役割**: タスクデータラッパー。元タスクとそのハッシュ、ID などのメタ情報をカプセル化します
   - **格納情報**: タスクデータ、SHA1 ハッシュ値（遅延計算）、タスク ID
   - **主要機能**: データカプセル化、遅延ハッシュ計算、hash 不可能タスクのフォールバック

3. **core_metrics.py** (`TaskMetrics`)
   - **役割**: タスク実行メトリクス統計。成功/失敗/重複カウントと重複排除ロジックを管理します
   - **主要機能**: スレッドセーフカウンター、重複タスク検査、リトライ可能例外の設定、タスク完了判定

### ユーティリティモジュール

4. **util_errors.py**
   - **役割**: 完全な例外定義体系
   - **対象**: 設定例外、グラフ構造例外、実行時例外、外部サービス例外、タスクロジック例外
   - 例外一覧の詳細は `util_errors.md` を参照

5. **util_types.py**
   - **役割**: ランタイム型定義とデータ構造
   - **含まれる型**: `TerminationSignal`、`TerminationIdPool`、`ValueWrapper`、`SumCounter`、`NoOpContext`、`StageStatus`、`CTreeEvent`

6. **util_hash.py**
   - **役割**: オブジェクトハッシュ計算。タスク重複排除に使用
   - **主要関数**: `make_hashable()`、`object_to_hash()`

7. **util_estimators.py**
   - **役割**: 実行時間推定と進捗計算
   - **主要関数**: `calc_remaining()`、`calc_elapsed()`、`format_avg_time()`

8. **util_event.py**
   - **役割**: イベントクライアント抽象インターフェースとローカル実装
   - **主要クラス**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

9. **util_constant.py**
   - **役割**: ランタイムグローバル定数定義（ログレベルマッピングなど）

10. **util_config.py**
    - **役割**: ランタイム設定ロード（pyproject.toml からログレベルを読み取りなど）

11. **util_format.py**
    - **役割**: 汎用フォーマットツール（文字列切り詰め、テーブルレンダリング、時間フォーマットなど）

## モジュール関連

### 内部関連
- `TaskEnvelope` は `util_hash` を使用してタスクハッシュを計算
- `TaskInQueue`/`TaskOutQueue` は `util_types` の `TerminationSignal`/`TerminationIdPool` を使用
- `TaskMetrics` は `util_types` の `ValueWrapper`/`SumCounter` を使用
- すべてのエラーは `CelestialFlowError` およびそのサブクラスを通じて統一的に処理

### 外部関連
- **Stage モジュール**: Stage は `TaskInQueue`/`TaskOutQueue` をノード間通信パイプラインとして使用
- **Graph モジュール**: `TaskGraph` にキューとメトリクスのインフラストラクチャを提供

## 使用例

以下の例は runtime モジュールの各基本コンポーネントの使用方法を示します。

```python
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope：タスクエンベロープの作成と操作
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"タスクデータ: {envelope.get_task()}")
print(f"タスクハッシュ: {envelope.get_hash().hex()[:8]}...")
print(f"タスクID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics：メトリクス統計
metrics = TaskMetrics(enable_duplicate_check=True)

# タスク処理のシミュレーション
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_fail_count(1)
metrics.add_duplicate_count(1)

# 各カウントの照会
print(f"入力: {metrics.get_task_count()}")
print(f"成功: {metrics.get_success_count()}")
print(f"失敗: {metrics.get_fail_count()}")
print(f"重複: {metrics.get_duplicate_count()}")
print(f"全完了: {metrics.is_tasks_finished()}")

# スナップショット辞書の取得
counts = metrics.get_counts()
print(f"保留中: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue：キュー通信
from queue import Queue as ThreadQueue

# 入力キューの作成
in_queue = TaskInQueue(out_name="processor")
in_queue.add_source_name("producer")

# 出力キューの作成
out_queue = TaskOutQueue(in_name="processor")
consumer_queue = ThreadQueue()
out_queue.add_queue(consumer_queue, "consumer")

# タスクを生産
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)
out_queue.put(envelope_a)

# タスクを消費
retrieved = in_queue.get()
print(f"デキューされたタスク: {retrieved.get_task()}")
```

## ベストプラクティス

1. **クリティカルタスク**: 適切な `set_retry_exceptions` を設定
2. **重複に敏感なシナリオ**: `enable_duplicate_check=True` を有効化
3. **キュー通信**: メモリ溢れを避けるため `maxsize` を適切に設定
