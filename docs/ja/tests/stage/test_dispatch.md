# タスクスケジューリングコアテスト (test_dispatch.py)

> 📅 最終更新日: 2026/08/26

## 役割

`celestialflow.stage.core_dispatch.TaskDispatch` が `serial`、`thread`、`async` の3つのスケジューリングモードで示すコア動作（タスク実行、例外リトライ、重複排除、終了信号処理、worker クラッシュのフォールバック）を検証します。

## コアテスト対象

- `TaskDispatch`: タスクキューから `TaskEnvelope` を取得し、指定されたモードでワーカーにディスパッチして実行し、結果を結果キューに書き込む責務を担います。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|-------------|---------|--------------|
| `TestDispatchSerial` | 7 | 単一/複数タスク、リトライ成功、リトライ枯渇、終了信号（単一/複数ID）、success fanout で下流タスク ID が独立であること |
| `TestDispatchThread` | 2 | 10タスク並行、重複タスク排除統計 |
| `TestDispatchAsync` | 2 | 10タスクコルーチン並行、非同期リトライ成功 |
| `TestWorkerCrashKeepsTerminationSignal` | 2 | 失敗処理チェーンのクラッシュ、リトライエンベロープ生成のクラッシュ時も終了信号は正常に送信される（3モードパラメータ化） |
| `TestDispatchCoreBehavior` | 2 | 空キュー + 終了信号（3モードパラメータ化）、5タスクの結果数（3モードパラメータ化） |
| **合計** | **15** | |

## 主要テストシナリオ

### `TestDispatchSerial` — 直列スケジューリング
- 単一タスク / 複数タスクの逐次実行
- リトライ成功（最初のN回は例外をスローし、最後に成功）
- リトライ枯渇（常に例外をスローし、最終的に成功結果なし）
- 終了信号のマージ（単一ID / 複数ID）
- success fanout が各実際の下流ノードに対して独立したタスク ID を作成すること（`get_id()` が互いに異なる）

### `TestDispatchThread` — スレッドスケジューリング
- 10タスク並行（4ワーカー）、結果の正しい収集を検証
- 重複タスク排除（同一タスクを2回投入、`metrics.get_duplicate_count()` のカウントが 1、実行結果が少なくとも1件残る）

### `TestDispatchAsync` — 非同期スケジューリング
- 10タスクコルーチン並行（4ワーカー）
- 非同期リトライ成功（3回の呼び出し後に正しい値を返す）

### `TestWorkerCrashKeepsTerminationSignal` — Worker クラッシュフォールバック（回帰テスト）
- 失敗処理チェーンのクラッシュ（observer が例外をスロー）：例外は `observer_error` で捕捉され、終了信号は正常に送信され、`worker_crash` はトリガーされない
- リトライエンベロープ生成のクラッシュ（ログが例外をスロー）：スケジューリングは中断されず、終了信号は依然として送信され、`worker_crash` が例外を記録する
- 上記2つのシナリオはいずれも `serial` / `thread` / `async` の3モードでパラメータ化されて実行される

### `TestDispatchCoreBehavior` — クロスモードパラメータ化
- 空キュー + 終了信号：3モードすべてが正しく終了
- 5タスク結果数：3モードすべてが5つの結果 + 終了信号を出力

## 実行方法

```bash
# すべて実行
pytest tests/stage/test_dispatch.py -v

# 直列スケジューリングテストのみ
pytest tests/stage/test_dispatch.py -k "Serial" -v

# スレッドスケジューリングテストのみ
pytest tests/stage/test_dispatch.py -k "Thread" -v

# 非同期スケジューリングテストのみ
pytest tests/stage/test_dispatch.py -k "Async" -v

# worker クラッシュフォールバックテストのみ
pytest tests/stage/test_dispatch.py -k "Crash" -v

# クロスモードパラメータ化テストのみ
pytest tests/stage/test_dispatch.py -k "CoreBehavior" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|-------------|---------|
| `TestDispatchSerial` | ~0.1s |
| `TestDispatchThread` | ~0.2s |
| `TestDispatchAsync` | ~0.2s |
| `TestWorkerCrashKeepsTerminationSignal` | ~0.3s |
| `TestDispatchCoreBehavior` | ~0.3s |

## 重要な詳細

- テストは `TaskEnvelope` でタスクをラップし、`_put` および `_put_termination` ヘルパー関数でキューに注入します。
- 終了信号は公開API `task_queue.put(TerminationSignal(...))` で注入され、内部の `TerminationIdPool` を直接操作しません。
- 非同期テストは `asyncio.run()` で独立したイベントループを作成し、既存ループとの競合を回避します。
- `_make_executor` は `result_queue.add_queue()` 公開APIを通じてテスト用の結果収集キューを登録し、executor へのテスト専用属性注入を回避します。
- `TestWorkerCrashKeepsTerminationSignal` は `_CrashOnFailObserver` と `_CrashRetryLogInlet` を使用して処理チェーンのクラッシュをシミュレートし、終了信号のフォールバックメカニズムを検証します。

## 注意事項

- スケジューラは `TaskExecutor` と `TaskStage` の基盤実行エンジンであり、その正確性はフレームワーク全体のタスク実行に直接影響します。
- 関連実装は `src/celestialflow/stage/core_dispatch.py` にあります。
