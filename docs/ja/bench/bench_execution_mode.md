# bench_execution_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/06/11

## 目的

`TaskExecutor` の 3 つの実行モード（`serial`、`thread`、`async`）における CPU 集約型タスク（フィボナッチ）と I/O 集約型タスク（sleep）の性能差を比較する。フレームワーク内蔵の `benchmark_executor` ツールにより統一的な比較レポートを出力する。

## テスト内容

### `bench_executor_fibonacci`
- **タスク**：フィボナッチ数列の計算（`n=25..31`）、異常入力を含む（`0, None, ""`）
- **設定**：`max_workers=6`、`max_retries=1`、`ValueError` 発生時にリトライ
- **比較モード**：`serial`、`thread`、`async`

2 つのフィボナッチ実装は**同じイテレーティブ O(n) アルゴリズム**を使用し、公平な比較を保証する：

```python
# 同期版 — イテレーティブ、O(n)
def fibonacci(n):
    ...
    prev, curr = 1, 1
    for _ in range(3, n + 1):
        prev, curr = curr, prev + curr
    return curr

# 非同期版 — イテレーティブ + 8 ラウンドごとにコルーチン譲渡、O(n)
async def fibonacci_async(n):
    ...
    prev, curr = 1, 1
    for i in range(3, n + 1):
        prev, curr = curr, prev + curr
        if i % 8 == 0:
            await asyncio.sleep(0)  # イベントループを譲渡
    return curr
```

唯一の違いは `fibonacci_async` が 8 回の反復ごとに `await` 譲渡ポイントを持つことであり、これは async 実行モード固有の協調的スケジューリング特性である。

### `bench_executor_sleep`
- **タスク**：純粋な 1 秒スリープ（I/O 待機のシミュレーション）、同期版と非同期版の動作は完全に同一
- **設定**：`max_workers=6`、`max_retries=0`
- **比較モード**：`serial`、`thread`、`async`

## 主要パラメータ

| パラメータ | 値 | 説明 |
|------------|-----|------|
| `max_workers` | 6 (CPU) / 6 (I/O) | 並行ワーカー数 |
| `max_retries` | 1 (CPU) / 0 (I/O) | リトライ回数 |

## 発生し得る問題

1. **CPU 集約型タスクは GIL に制限される**：Python の GIL は同時に 1 つのスレッドのみが Python バイトコードを実行するよう制限する。`thread` モードでは 6 ワーカーを使用しても、純粋な計算の大部分は GIL により直列化される。
2. **`asyncio` イベントループの競合**：`main()` は `asyncio.run()` を使用するため、Jupyter や既存のイベントループがある環境ではエラーが発生する。
3. **`benchmark_executor` の出力形式**：このツールは `TaskExecutor` の `execution_mode` を複数回変更して再実行するため、合計時間 = モード数 × タスク数 × 単一タスク時間となる。

## 実行方法

```bash
python bench/bench_execution_mode.py
```

## パラメータ調整

### 特定テストシナリオの単独実行

`bench/bench_execution_mode.py` の `main()` で選択的に実行できる：

```python
async def main():
    # フィボナッチテストのみ実行
    await bench_executor_fibonacci()
    # await bench_executor_sleep()  # sleep テストをコメントアウト
```

```bash
# 修正後に実行
python bench/bench_execution_mode.py
```



### 入力範囲のカスタマイズ

フィボナッチテストの入力は関数内部の `bench_task_1` リストで定義されており、タスクリストを変更できる：

```python
# 小さい値のみをテスト（素早く検証）
bench_task_1: list[Any] = [10, 15, 20]

# 範囲を拡大
bench_task_1: list[Any] = list(range(20, 35))
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10

### シナリオ 1：フィボナッチ（CPU 集約型）
12 タスク（異常境界 5 個を含む）、max_workers=6、max_retries=1。3 つのモードすべてが**同じイテレーティブ O(n) アルゴリズム**を使用。

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 0.0065s | シングルスレッド逐次実行、純粋計算でスケジューリングオーバーヘッドなし |
| thread | 0.0048s | 6 スレッド並行、GIL に制限され改善は限定的 |
| async | 0.0062s | コルーチン並行、反復中の await 譲渡ポイントが並行性を許容するが、純粋計算の性質により限定的 |

> 🟢 3 つのモードはすべて同じ桁（~5-6ms）。thread がわずかに速いのは、GIL が高頻度反復の譲渡ポイント間にわずかな並行ウィンドウを持つため。async の `await` 譲渡ポイントは極めて微量のコルーチンスケジューリングオーバーヘッドをもたらす。全体の差はマイクロ秒レベルであり、CPU 集約型タスクではいずれのモードも顕著な高速化は得られない。

### シナリオ 2：sleep_1（I/O 集約型）
6 タスク、各 1 秒スリープ、max_workers=6。同期版と非同期版の sleep 動作は同一で、比較結果は実行モードの違いを直接反映する。

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 6.010s | 逐次スリープ、合計時間 ≈ 6 × 1s |
| thread | 1.006s | 6 スレッド並列、合計時間 ≈ 1s + スケジューリングオーバーヘッド |
| async | 1.009s | コルーチン並列、thread とほぼ同等 |

**主要な結論**：
- **I/O 集約型タスク**：thread と async の両方がほぼ理論最適な並列度（約 6x の高速化）を達成し、両者の差は無視できる
- **CPU 集約型タスク**：3 モードとも同じ桁の所要時間。純粋計算タスクは Python GIL に制限され、thread に顕著な利点はない。async はコルーチン譲渡ポイントで並行性を得られるが全体的な改善は限定的
- 実行モード選択の核心的な基準は**タスクの本質**：I/O 待機には thread/async を使用し、純粋計算には GIL の影響を考慮する（またはマルチプロセスを検討）

## 依存関係

- `celestialflow`（`TaskExecutor`、`TaskProgress`、`benchmark_executor`）
