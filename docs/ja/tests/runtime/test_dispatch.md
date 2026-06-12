# タスクスケジューリングコアテスト (test_dispatch.py)

> 📅 最終更新日: 2026/06/11

## 役割

`celestialflow.runtime.core_dispatch.TaskDispatch` が `serial`、`thread`、`async` の3つのスケジューリングモードで示すコア動作（タスク実行、例外リトライ、重複排除、終了信号処理）を検証します。

## コアテスト対象

- `TaskDispatch`: タスクキューから `TaskEnvelope` を取得し、指定されたモードでワーカーにディスパッチして実行し、結果を結果キューに書き込む責務を担います。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|-------------|---------|--------------|
| `TestDispatchSerial` | 6 | 単一/複数タスク、リトライ成功、リトライ枯渇、終了信号（単一/複数ID） |
| `TestDispatchThread` | 2 | 10タスク並行、重複タスク排除統計 |
| `TestDispatchAsync` | 2 | 10タスクコルーチン並行、非同期リトライ成功 |
| `TestDispatchCoreBehavior` | 2 | 空キュー+終了信号（3モードパラメータ化）、5タスク結果数（3モードパラメータ化） |
| **合計** | **12** | |

## 主要テストシナリオ

### `TestDispatchSerial` — 直列スケジューリング
- 単一タスク / 複数タスクの逐次実行
- リトライ成功（最初のN回は例外をスローし、最後に成功）
- リトライ枯渇（常に例外をスローし、最終的に成功結果なし）
- 終了信号のマージ（単一ID / 複数ID）

### `TestDispatchThread` — スレッドスケジューリング
- 10タスク並行（4ワーカー）、結果の正しい収集を検証
- 重複タスク排除（同一ハッシュを2回投入、1回のみ実行、`duplicate_count` が1になる）

### `TestDispatchAsync` — 非同期スケジューリング
- 10タスクコルーチン並行（4ワーカー）
- 非同期リトライ成功（3回の呼び出し後に正しい値を返す）

### `TestDispatchCoreBehavior` — クロスモードパラメータ化
- 空キュー + 終了信号：3モードすべてが正しく終了
- 5タスク結果数：3モードすべてが5つの結果 + 終了信号を出力

## 実行方法

```bash
# 全テスト実行
pytest tests/runtime/test_dispatch.py -v

# 直列スケジューリングテストのみ
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
|-------------|---------|
| `TestDispatchSerial` | ~0.1s |
| `TestDispatchThread` | ~0.2s |
| `TestDispatchAsync` | ~0.2s |
| `TestDispatchCoreBehavior` | ~0.3s |

## 重要な詳細

- テストは `TaskEnvelope` でタスクをラップし、`_put` および `_put_termination` ヘルパー関数でキューに注入します。
- 終了信号は公開API `task_queue.put(TerminationSignal(...))` で注入され、内部の `TerminationIdPool` を直接操作しません。
- 非同期テストは `asyncio.run()` で独立したイベントループを作成し、既存ループとの競合を回避します。
- `_make_executor` は `result_queue.add_queue()` 公開APIを通じてテスト用の結果収集キューを登録し、executor へのテスト専用属性注入を回避します。

## 注意事項

- スケジューラは `TaskExecutor` と `TaskStage` の基盤実行エンジンであり、その正確性はフレームワーク全体のタスク実行に直接影響します。
- 関連実装は `src/celestialflow/runtime/core_dispatch.py` にあります。
