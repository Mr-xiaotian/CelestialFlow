# Runtime モジュール

> 📅 最終更新日: 2026/05/28

Runtime モジュールは、CelestialFlow のタスク実行ランタイム環境を提供します。タスクスケジューリング、キュー管理、エラーハンドリング、パフォーマンス監視などのコア機能が含まれています。タスクの実際の実行を支えるインフラストラクチャ層です。

## モジュール概要

Runtime モジュールは、タスクの送信から結果の返却までのタスク実行ライフサイクル全体を管理します。3つの実行モード（シリアル `serial`、スレッド `thread`、非同期 `async`）、堅牢なエラーハンドリングメカニズム、パフォーマンス監視、リソース管理機能を提供します。

## ファイル説明

### コアランタイムコンポーネント

1. **core_dispatch.py** (`TaskDispatch`)
   - **役割**: シリアル、スレッド、非同期モードで個々のタスクを実行するタスクスケジューラ
   - **実行モード**:
     - `dispatch_serial`: タスクを順次実行
     - `dispatch_thread`: `ThreadPoolExecutor` ベースの並行実行
     - `dispatch_async`: `asyncio` ベースの非同期タスク（セマフォ制御の並行数）
   - **主要機能**: タスクリトライ、重複チェック、終了シグナルマージ、スレッドプールライフサイクル管理

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **役割**: ノード間のデータ転送と終了シグナルマージを行うタスク入力/出力キュー
   - **キュータイプ**:
     - `TaskInQueue`: タスク入力キュー。複数の上流ソースからのタスクと終了シグナルを集約
     - `TaskOutQueue`: タスク出力キュー。結果を1つ以上の下流キューチャネルにブロードキャスト
   - **主要機能**: 終了シグナルマージ、ソース名管理、ログ記録、動的キューチャネル追加

3. **core_envelope.py** (`TaskEnvelope`)
   - **役割**: 元のタスクをハッシュ、ID、ソースなどのメタ情報と共にカプセル化するタスクデータラッパー
   - **含まれる情報**: タスクデータ、SHA1 ハッシュ値（遅延計算）、タスク ID、ソース識別子、先行タスク参照
   - **主要機能**: データカプセル化、遅延ハッシュ計算、タスク ID 変更（リトライシナリオ）

### 監視とメトリクス

4. **core_metrics.py** (`TaskMetrics`)
   - **役割**: タスク実行メトリクス統計。成功/失敗/重複カウントと重複排除ロジックを管理
   - **主要機能**: スレッドセーフカウンター、重複タスクチェック、リトライ可能例外設定、タスク完了判定

### ツールとユーティリティ

5. **util_errors.py**（例外クラス階層）
   - **役割**: 完全な例外定義体系
   - **対象**: 設定例外、グラフ構造例外、ランタイム例外、外部サービス例外、タスクロジック例外
   - 詳細な例外リストは `util_errors.md` を参照

6. **util_types.py**
   - **役割**: ランタイム型定義とデータ構造
   - **含まれる型**:
     - **コアシグナル**: `TerminationSignal` / `TERMINATION_SIGNAL` — センチネルオブジェクト; `TerminationIdPool` — 終了シグナル ID プール
     - **カウンター**: `ValueWrapper` — オプションのスレッドロック付き整数ラッパー; `SumCounter` — 複数の `ValueWrapper` からのカスケード集計
     - **コンテキストマネージャ**: `NoOpContext` — `with` ロジックを無効にする空のコンテキストマネージャ
     - **ライフサイクル**: `StageStatus` — IntEnum（NOT_STARTED / RUNNING / STOPPED）
     - **イベント定数**: `CTreeEvent` — タスク/終了イベント名定数（TASK_INPUT / TASK_SUCCESS / TASK_ERROR / TASK_RETRY_PREFIX / TASK_DUPLICATE / TERMINATION_INPUT / TERMINATION_MERGE）
     - **エラーレコード**: `PersistedErrorRecord` — 永続化エラーレコード frozen dataclass（グループ化対応）
     - **可視化**: `STAGE_STYLE` — CelestialTree ノードラベルスタイル

7. **util_hash.py**
   - **役割**: タスク重複排除のためのオブジェクトハッシュ計算
   - **主要関数**:
     - `make_hashable()`: list/dict/set を安定したハッシュ可能構造に再帰的に変換
     - `object_to_hash()`: pickle 後に SHA1 を計算し、`bytes` を返す

8. **util_estimators.py**
   - **役割**: 実行時間推定と進捗計算
   - **主要関数**:
     - `calc_remaining()`: 平均値に基づいて残り時間を推定
     - `calc_elapsed()`: 状態ごとに経過時間を集計
     - `calc_global_remain_equal_pred()`: DAG トポロジーに基づくグローバル残り時間推定（保守的）

## モジュール関連

### 内部関連
- `TaskDispatch` は `TaskInQueue`/`TaskOutQueue` を使用してタスク取得と結果送信を行う
- `TaskEnvelope` はキューを通じて渡され、タスクのハッシュとソース情報を含む
- `TaskMetrics` は `TaskDispatch` の実行状態を監視
- すべてのエラーは `CelestialFlowError` とそのサブクラスを通じて統一的に処理

### 外部関連
- **Stage モジュールとの関連**: `TaskDispatch` は `TaskExecutor` と `TaskStage` を実行
- **Graph モジュールとの関連**: `TaskGraph` に実行エンジンと通信メカニズムを提供
- **Persistence モジュールとの関連**: 実行状態の永続化とログ記録をサポート
- **Observability モジュールとの関連**: 監視データとパフォーマンスメトリクスを提供

## アーキテクチャ特徴

### 3モード実行
- `serial`: 順次実行、軽量タスクとデバッグに適する
- `thread`: スレッドプール並行、I/O 集約型タスクに適する
- `async`: 非同期コルーチン、ネットワーク I/O シナリオに適する

### 堅牢性設計
- 完全なエラーハンドリングチェーン（リトライ可能 / リトライ不可）
- スレッドセーフカウンター
- リソースリーク防止（スレッドプール自動解放）

### 可観測性
- 包括的なメトリクス収集（成功、失敗、重複、保留中）
- DAG ベースのグローバル残り時間推定
- 詳細な実行ログ

## 使用例

以下に、ランタイムモジュールの各コンポーネントの協調使用例を示します。タスクエンベロープ、メトリクス統計、キュー通信をカバーしています。

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue
from celestialflow.persistence import LogInlet

# 1. TaskEnvelope：タスクエンベロープの作成と操作
envelope = TaskEnvelope(task={"data": 42}, id=1, source="input")
print(f"タスクデータ: {envelope.get_task()}")
print(f"タスクハッシュ: {envelope.get_hash().hex()[:8]}...")
print(f"タスクID: {envelope.get_id()}")

# リトライ時に ID を変更
envelope.change_id(100)
print(f"変更後 ID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics：メトリクス統計
import time

metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)

# タスク処理をシミュレート
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_error_count(1)
metrics.add_duplicate_count(1)

# 各カウントをクエリ
print(f"入力: {metrics.get_task_count()}")
print(f"成功: {metrics.get_success_count()}")
print(f"失敗: {metrics.get_error_count()}")
print(f"重複: {metrics.get_duplicate_count()}")
print(f"全完了: {metrics.is_tasks_finished()}")

# スナップショット辞書を取得
counts = metrics.get_counts()
print(f"保留中: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue：キュー通信

# 入力キューを作成（上流タスクを集約）
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["producer"],
    out_name="processor",
)

# 出力キューを作成（下流にブロードキャスト）
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

# 出力チャネルを動的に追加
out_queue.add_queue(ThreadQueue(), "another_consumer")
print(f"出力チャネル数: {len(out_queue.queue_list)}")
```

## ベストプラクティス

1. **I/O 集約型タスク**: `thread` モードを使用
2. **非同期タスク**: `async` モードを使用（関数はコルーチンである必要あり）
3. **デバッグ**: `serial` モードを使用、単一実行の追跡が容易
4. **クリティカルタスク**: 適切な `max_retries` と `add_retry_exceptions` を設定
5. **重複に敏感なシナリオ**: `enable_duplicate_check=True` を有効化
