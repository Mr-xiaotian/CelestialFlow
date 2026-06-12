# Runtime モジュール

> 📅 最終更新日: 2026/06/11

Runtime モジュールは CelestialFlow のタスク実行ランタイム環境を提供し、タスクスケジューリング、キュー管理、エラー処理、パフォーマンス監視などのコア機能を含みます。タスクを実際に実行するインフラストラクチャ層です。

## モジュール概要

Runtime モジュールは、タスク投入から結果返却までのタスク実行ライフサイクル全体を管理します。3 つの実行モード（シリアル `serial`、スレッド `thread`、非同期 `async`）、堅牢なエラー処理機構、パフォーマンス監視、リソース管理機能を提供します。

### 公開エクスポートシンボル (`__all__`)

```python
from celestialflow.runtime import (
    TaskDispatch,    # タスクディスパッチャ（TaskDispatch）
    TaskEnvelope,    # タスクエンベロープ（TaskEnvelope）
    TaskInQueue,     # タスク入力キュー
    TaskMetrics,     # タスクメトリクス統計
    TaskOutQueue,    # タスク出力キュー
)
```

> **注意**: `util_constant`、`util_errors`、`util_estimators`、`util_hash`、`util_types` などのユーティリティモジュールのシンボルは `runtime/__init__.py` の `__all__` に**含まれていません**。完全修飾パスでインポートしてください（例: `from celestialflow.runtime.util_errors import ConfigurationError`）。

## ファイル説明

### コアランタイムコンポーネント

1. **core_dispatch.py** (`TaskDispatch`)
   - **役割**: タスクディスパッチャ。シリアル、スレッド、非同期のいずれかの方式で単一タスクを実行します
   - **実行モード**:
     - `dispatch_serial`: タスクを順次実行
     - `dispatch_thread`: `ThreadPoolExecutor` による並行実行
     - `dispatch_async`: `asyncio` ベースの非同期タスク（セマフォで並行数を制御）
   - **主要機能**: タスクリトライ、重複排除チェック、終了シグナル（TerminationSignal）マージ、スレッドプールライフサイクル管理

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **役割**: タスク入出力キュー。ノード間のデータ転送と終了シグナルマージを実現します
   - **キュー種別**:
     - `TaskInQueue`: タスク入力キュー。複数上流からのタスクと終了シグナルを集約
     - `TaskOutQueue`: タスク出力キュー。結果を 1 つ以上の下流キューチャネルにブロードキャスト
   - **主要機能**: 終了シグナルマージ、ソース名管理、キューチャネルの動的追加

3. **core_envelope.py** (`TaskEnvelope`)
   - **役割**: タスクデータラッパー。元タスクとそのハッシュ、ID、ソースなどのメタ情報をカプセル化します
   - **格納情報**: タスクデータ、SHA1 ハッシュ値（遅延計算）、タスク ID、ソース識別子、先行タスク参照
   - **主要機能**: データカプセル化、遅延ハッシュ計算、タスク ID と先行タスク参照

### 監視とメトリクス

4. **core_metrics.py** (`TaskMetrics`)
   - **役割**: タスク実行メトリクス統計。成功/失敗/重複カウントと重複排除ロジックを管理します
   - **主要機能**: スレッドセーフカウンター、重複タスク検査、リトライ可能例外の設定、タスク完了判定

### ユーティリティ

5. **util_errors.py**（例外クラス階層）
   - **役割**: 完全な例外定義体系
   - **対象**: 設定例外、グラフ構造例外、実行時例外、外部サービス例外、タスクロジック例外
   - 例外一覧の詳細は `util_errors.md` を参照

6. **util_types.py**
   - **役割**: ランタイム型定義とデータ構造
   - **含まれる型**:
     - **コアシグナル**: `TerminationSignal` / `TERMINATION_SIGNAL` — センチネルオブジェクト; `TerminationIdPool` — 終了シグナル ID プール
     - **カウンター**: `ValueWrapper` — オプションのスレッドロック付き整数ラッパー; `SumCounter` — 複数 `ValueWrapper` のカスケード累算
     - **コンテキストマネージャ**: `NoOpContext` — 空のコンテキストマネージャ。`with` ロジックの無効化に使用
     - **ライフサイクル**: `StageStatus` — IntEnum（NOT_STARTED / RUNNING / STOPPED）
     - **イベント定数**: `CTreeEvent` — タスク/終了イベント名定数（TASK_INPUT / TASK_SUCCESS / TASK_ERROR / TASK_RETRY_PREFIX / TASK_DUPLICATE / TERMINATION_INPUT / TERMINATION_MERGE）
     - **エラーレコード**: `PersistedErrorRecord` — 永続化エラーレコード frozen dataclass（グループ化対応）
     - **可視化**: `STAGE_STYLE` — CelestialTree ノードラベルスタイル

7. **util_hash.py**
   - **役割**: オブジェクトハッシュ計算。タスク重複排除に使用
   - **主要関数**:
     - `make_hashable()`: list/dict/set を再帰的に安定したハッシュ可能構造へ変換
     - `object_to_hash()`: pickle 後に SHA1 を計算し `bytes` を返す

8. **util_estimators.py**
   - **役割**: 実行時間推定と進捗計算
   - **主要機能**:
     - `calc_remaining()`: 平均値に基づく残り時間の推定
     - `calc_elapsed()`: 状態別の経過時間累計
     - `calc_global_pending()`: DAG トポロジに基づくグローバル保留タスク数の推定（保守的）

## モジュール関連

### 内部関連
- `TaskDispatch` は `TaskInQueue`/`TaskOutQueue` を使用してタスクの取得と結果の送信を行います
- `TaskEnvelope` はキュー内を転送され、タスクのハッシュとソース情報を運びます
- `TaskMetrics` は `TaskDispatch` の実行状態を監視します
- すべてのエラーは `CelestialFlowError` およびそのサブクラスを通じて統一的に処理されます

### 外部関連
- **Stage モジュールと**: `TaskDispatch` は `TaskExecutor` と `TaskStage` を実行します
- **Graph モジュールと**: `TaskGraph` に実行エンジンと通信機構を提供します
- **Persistence モジュールと**: 実行状態の永続化とログ記録をサポートします
- **Observability モジュールと**: 監視データとパフォーマンスメトリクスを提供します

## アーキテクチャの特徴

### 3 モード実行
- `serial`: 順次実行。軽量タスクやデバッグに最適
- `thread`: スレッドプール並行。I/O バウンドタスクに最適
- `async`: 非同期コルーチン。ネットワーク I/O シナリオに最適

### 堅牢性設計
- 完全なエラー処理チェーン（リトライ / リトライ不可）
- スレッドセーフカウンター
- リソースリーク防止（スレッドプール自動解放）

### 可観測性（Observability）
- 包括的なメトリクス収集（成功、失敗、重複、保留中）
- DAG ベースのグローバル残り時間推定
- 詳細な実行ログ

## 使用例

以下の例は runtime モジュールの各コンポーネントの連携方法を示し、タスクエンベロープ、メトリクス統計、キュー通信を網羅します。

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue
from celestialflow.persistence import LogInlet

# 1. TaskEnvelope：タスクエンベロープの作成と操作
envelope = TaskEnvelope(task={"data": 42}, id=1, source="input")
print(f"タスクデータ: {envelope.get_task()}")
print(f"タスクハッシュ: {envelope.get_hash().hex()[:8]}...")
print(f"タスクID: {envelope.get_id()}")

# リトライ時は emit_retry_envelope で新しいエンベロープを生成
print(f"タスクID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics：メトリクス統計
import time

metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)

# タスク処理のシミュレーション
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_error_count(1)
metrics.add_duplicate_count(1)

# 各カウントの照会
print(f"入力: {metrics.get_task_count()}")
print(f"成功: {metrics.get_success_count()}")
print(f"失敗: {metrics.get_error_count()}")
print(f"重複: {metrics.get_duplicate_count()}")
print(f"全完了: {metrics.is_tasks_finished()}")

# スナップショット辞書の取得
counts = metrics.get_counts()
print(f"保留中: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue：キュー通信

# 入力キューの作成（上流タスクを集約）
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["producer"],
    out_name="processor",
)

# 出力キューの作成（下流へブロードキャスト）
out_queue = TaskOutQueue(
    queue_list=[ThreadQueue()],
    target_names=["consumer"],
    in_name="processor",
)

# 上流がタスクを生産
envelope_a = TaskEnvelope(task="hello", id=1, source="producer")
in_queue.put(envelope_a)

# 下流がタスクを消費
retrieved = in_queue.get()
print(f"デキューされたタスク: {retrieved.get_task()}")

# 出力キューがタスクをブロードキャスト
out_queue.put(envelope_a)

# 出力チャネルの動的追加
out_queue.add_queue(ThreadQueue(), "another_consumer")
print(f"出力チャネル数: {len(out_queue.queue_list)}")
```

## ベストプラクティス

1. **I/O バウンドタスク**: `thread` モードを使用
2. **非同期タスク**: `async` モードを使用（関数はコルーチンである必要あり）
3. **デバッグ**: `serial` モードを使用。単一実行の追跡が容易
4. **クリティカルタスク**: 適切な `max_retries` と `add_retry_exceptions` を設定
5. **重複に敏感なシナリオ**: `enable_duplicate_check=True` を有効化
