# タスクディスパッチコアテスト (test_dispatch.py)

> 📅 最終更新日: 2026/05/28

## 目的

`celestialflow.runtime.core_dispatch.TaskDispatch` の `serial`、`thread`、`async` の 3 つのスケジューリングモードにおけるコア動作（タスク実行、例外リトライ、重複排除、終了シグナル処理）を検証します。

## コアテスト対象

- `TaskDispatch`: タスクキューから `TaskEnvelope` を取り出し、指定されたモードでワーカーにディスパッチし、結果を結果キューに書き込む責務を持ちます。

## 主要テストシナリオ

### `TestDispatchSerial` — シリアルスケジューリング
- 単一タスク / 複数タスクの逐次実行
- リトライ成功（最初の N 回は例外をスローし、最後に成功）
- リトライ枯渇（常に例外をスローし、成功結果なし）
- 終了シグナルマージ（単一 ID / 複数 ID）

### `TestDispatchThread` — スレッドスケジューリング
- 10 タスク並行（4 ワーカー）、結果の正しい収集を検証
- 重複タスクの排除（同じハッシュを 2 回投入、1 回のみ実行）

### `TestDispatchAsync` — 非同期スケジューリング
- 10 タスクコルーチン並行（4 ワーカー）
- 非同期リトライ成功（3 回の呼び出し後に正しい値を返す）

### `TestDispatchCoreBehavior` — クロスモードパラメータ化
- 空キュー + 終了シグナル：3 モードすべてが正しく終了
- 5 タスク結果数：3 モードすべてが 5 結果 + 終了シグナルを出力

## 実行方法

```bash
# 全実行
pytest tests/runtime/test_dispatch.py -v

# シリアルスケジューリングテストのみ
pytest tests/runtime/test_dispatch.py -k "Serial" -v

# スレッドスケジューリングテストのみ
pytest tests/runtime/test_dispatch.py -k "Thread" -v

# 非同期スケジューリングテストのみ
pytest tests/runtime/test_dispatch.py -k "Async" -v

# クロスモードパラメータ化テストのみ
pytest tests/runtime/test_dispatch.py -k "CoreBehavior" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------------|----------|
| `TestDispatchSerial` | ~0.1s |
| `TestDispatchThread` | ~0.2s |
| `TestDispatchAsync` | ~0.2s |
| `TestDispatchCoreBehavior` | ~0.3s |

## 重要な詳細

- テストでは `TaskEnvelope` を使用してタスクをラップし、`_put` および `_put_termination` ヘルパー関数を介してキューに注入します。
- 終了シグナルは内部の `TerminationIdPool` を直接操作するのではなく、公開 API `task_queue.put(TerminationSignal(...))` を介して注入されます。
- 非同期テストは `asyncio.run()` を使用して独立したイベントループを作成し、既存のループとの競合を回避します。

## 注意事項

- ディスパッチャは `TaskExecutor` と `TaskStage` の基盤となる実行エンジンであり、その正確性はフレームワーク全体のタスク実行に直接影響します。
- 関連実装は `src/celestialflow/runtime/core_dispatch.py` にあります。
