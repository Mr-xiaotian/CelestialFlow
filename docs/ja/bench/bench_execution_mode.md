# bench_execution_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/05/28

## 目的

`TaskExecutor` の 3 つの実行モード（`serial`、`thread`、`async`）における CPU 集約型タスク（フィボナッチ）と I/O 集約型タスク（sleep）の性能差を比較する。フレームワーク内蔵の `benchmark_executor` ツールで統一的な比較レポートを出力する。

## テスト内容

### `bench_executor_fibonacci`
- **タスク**：フィボナッチ数列の計算（`n=25..31`）、エッジケース含む（`0, None, ""`）
- **設定**：`max_workers=6`、`max_retries=1`、`ValueError` でリトライ
- **比較モード**：`serial`、`thread`、`async`

2 つのフィボナッチ実装は**同じイテレーティブ O(n) アルゴリズム**を使用し、公平な比較を保証します：

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

唯一の違いは `fibonacci_async` が 8 回の反復ごとに `await` 譲渡ポイントを持つことです。これは async 実行モードの協調的スケジューリングモデルに固有の特性です。

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

1. **CPU 集約型タスクは GIL に制限される**：Python の GIL は同時に 1 つのスレッドのみが Python バイトコードを実行するように制限します。`thread` モードでは、6 つのワーカーを使用しても、純粋な計算の大部分は GIL によってシリアル化されます。
2. **`asyncio` イベントループの競合**：`main()` は `asyncio.run()` を使用するため、Jupyter や既存のイベントループがある環境ではエラーになります。
3. **`benchmark_executor` の出力形式**：このツールは `TaskExecutor` の `execution_mode` を複数回変更して再実行するため、合計時間 = モード数 × タスク数 × 単一タスク時間となります。

## 実行方法

```bash
python bench/bench_execution_mode.py
```

## パラメータ調整

### 特定のテストシナリオの実行

`bench/bench_execution_mode.py` の `main()` で選択的にテストを実行できます：

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

フィボナッチテストの入力は関数内部で定義されており、`numbers` リストを変更できます：

```python
# 小さい値のみをテスト（迅速な検証）
numbers = [10, 15, 20]

# 範囲を拡大
numbers = list(range(20, 35))
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10

### シナリオ 1：フィボナッチ（CPU 集約型）
12 タスク（エッジケース 5 個含む）、max_workers=6、max_retries=1。3 つのモードすべてが**同じイテレーティブ O(n) アルゴリズム**を使用。

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 0.0065s | シングルスレッド逐次実行、純粋計算でスケジューリングオーバーヘッドなし |
| thread | 0.0048s | 6 スレッド並行、GIL に制限され、改善は限定的 |
| async | 0.0062s | コルーチン並行、反復中の await 譲渡ポイントが並行性を許容するが、純粋計算の性質により限定的 |

> 🟢 3 つのモードはすべて同じ桁（~5-6ms）です。thread がわずかに速いのは、GIL が高頻度の反復譲渡ポイント間に小さな並行ウィンドウをまだ持っているためです。async の `await` 譲渡ポイントは極めて小さなコルーチンスケジューリングオーバーヘッドをもたらします。全体の差はマイクロ秒レベルであり、CPU 集約型タスクではいずれのモードも顕著な高速化を提供しません。

### シナリオ 2：sleep_1（I/O 集約型）
6 タスク、各 1 秒スリープ、max_workers=6。同期版と非同期版の sleep 動作は同一で、比較結果は実行モードの違いを直接反映します。

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 6.010s | 逐次スリープ、合計時間 ≈ 6 × 1s |
| thread | 1.006s | 6 スレッド並列、合計時間 ≈ 1s + スケジューリングオーバーヘッド |
| async | 1.009s | コルーチン並列、thread とほぼ同等 |

**主要な結論**：
- **I/O 集約型タスク**：thread と async の両方がほぼ理論最適な並列度（約 6 倍の高速化）を達成し、両者の差は無視できる程度
- **CPU 集約型タスク**：3 つのモードはすべて同じ桁。純粋計算タスクは Python の GIL に制限され、thread モードに顕著な利点はない。async はコルーチン譲渡ポイントで並行性を達成できるが、全体的な改善は限定的
- 実行モード選択の核心的な基準は**タスクの性質**：I/O 待機には thread/async を使用し、純粋計算には GIL の影響を考慮する（またはマルチプロセスを検討）

## 依存関係

- `celestialflow`（`TaskExecutor`、`TaskProgress`、`benchmark_executor`）
