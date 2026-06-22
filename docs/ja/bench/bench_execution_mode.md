# bench_execution_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/06/22

## 目的

`TaskExecutor` の 3 つの実行モード（`serial`、`thread`、`async`）において、CPU 集約型タスク（フィボナッチ）と I/O 集約型タスク（sleep）の性能差を比較する。フレームワーク内蔵の `benchmark_executor` ツールを使用し、統一的な比較レポートを出力する。

## テスト内容

### `bench_executor_fibonacci`
- **タスク**：フィボナッチ数列の計算。入力は `list(range(25, 32)) + [0, 27, None, 0, ""]`（合計 12 タスク、うち 4 つが異常境界）
- **設定**：`max_workers=6`、`max_retries=1`、`ValueError` 発生時にリトライ
- **比較モード**：`serial`、`thread`、`async`

2 つのフィボナッチ実装は**同じ反復 O(n) アルゴリズム**を使用し、公平な比較を保証する：

```python
# 同步版 — 迭代，O(n)
def fibonacci(n):
    ...
    prev, curr = 1, 1
    for _ in range(3, n + 1):
        prev, curr = curr, prev + curr
    return curr

# 异步版 — 迭代 + 每 8 轮协程出让，O(n)
async def fibonacci_async(n):
    ...
    prev, curr = 1, 1
    for i in range(3, n + 1):
        prev, curr = curr, prev + curr
        if i % 8 == 0:
            await asyncio.sleep(0)  # 让出事件循环
    return curr
```

唯一の違いは `fibonacci_async` が 8 回の反復ごとに `await` 譲渡ポイントを 1 つ持つことであり、これは async 実行モード固有の協調的スケジューリング特性である。

### `bench_executor_sleep`
- **タスク**：純粋な 1 秒 sleep（I/O 待機のシミュレーション）。同期版と非同期版の動作は完全一致
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
    # 仅运行斐波那契测试
    await bench_executor_fibonacci()
    # await bench_executor_sleep()  # 注释掉 sleep 测试
```

```bash
# 修改后运行
python bench/bench_execution_mode.py
```

### 入力範囲のカスタマイズ

フィボナッチテストの入力は関数内部の `bench_task_1` リストで定義されており、タスクリストを変更できる：

```python
# 仅测试小数值（快速验证）
bench_task_1: list[Any] = [10, 15, 20]

# 扩大范围
bench_task_1: list[Any] = list(range(20, 35))
```

## ベンチマーク結果（実測）

### 履歴結果 - Windows 実行モード比較（日時未記録）

> 環境：Windows、Python 3.10

#### シナリオ 1：フィボナッチ（CPU 集約型）
12 タスク（うち 4 つが異常境界：2 つの `0` と `None`、`""` が例外を発生）を入力、max_workers=6、max_retries=1。3 つのモードすべてが**同じ反復 O(n) アルゴリズム**を使用。

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 0.0065s | シングルスレッド逐次実行。純粋計算でスケジューリングオーバーヘッドなし |
| thread | 0.0048s | 6 スレッド並行。GIL に制限され、改善は限定的 |
| async | 0.0062s | コルーチン並行。反復中の await 譲渡ポイントが並行性を許容するが、純粋計算の性質により限定的 |

> 🟢 3 つのモードはすべて同じ桁（~5-6ms）。thread がわずかに速いのは、GIL が高頻度反復の譲渡ポイント間にわずかな並行ウィンドウを持つため。async の `await` 譲渡ポイントは極めて微量のコルーチンスケジューリングオーバーヘッドをもたらす。全体の差はマイクロ秒レベルであり、CPU 集約型タスクではいずれのモードも顕著な高速化は得られない。

#### シナリオ 2：sleep_1（I/O 集約型）
6 タスクを入力し、それぞれ 1 秒 sleep、max_workers=6。同期版と非同期版の sleep 動作は同一で、比較結果は実行モードの違いを直接反映する。

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 6.010s | 逐次スリープ。合計時間 ≈ 6 × 1s |
| thread | 1.006s | 6 スレッド並列。合計時間 ≈ 1s + スケジューリングオーバーヘッド |
| async | 1.009s | コルーチン並列。thread とほぼ同等 |

**主要な結論**：
- **I/O 集約型タスク**：thread と async の両方がほぼ理論最適な並列度（~12x の高速化）を達成し、両者の差は無視できる
- **CPU 集約型タスク**：3 モードとも同じ桁の所要時間。純粋計算タスクは Python GIL に制限され、thread に顕著な利点はない。async はコルーチン譲渡ポイントで並行性を得られるが、全体的な改善は限定的
- 実行モード選択の核心的な基準は**タスクの本質**：I/O 待機には thread/async を使用し、純粋計算には GIL の影響を考慮する（またはマルチプロセスを検討）

### 2026/06/16 - ローカル再テスト

> 環境：Windows、現在のコードバージョンで `bench/bench_execution_mode.py` を直接実行

#### シナリオ 1：フィボナッチ（CPU 集約型）

| モード | 所要時間 |
|--------|----------|
| serial | 0.2191s |
| thread | **0.1432s** |
| async | 0.1456s |

#### シナリオ 2：sleep_1（I/O 集約型）

| モード | 所要時間 |
|--------|----------|
| serial | 6.1359s |
| thread | **1.1359s** |
| async | 1.1485s |

**今回の補足結論**：
- CPU シナリオでは `thread` と `async` が `serial` より明らかに速いが、両者の差は非常に小さく、現在のタスク規模ではスケジューリングと計算の混合が主因であることを示している
- I/O シナリオでは `thread` と `async` は依然として理論的な並列上限に近く、いずれも直列より約 **5.3x** 高速
- 今回の再テストは履歴の結論と一致：実行モードの選択はまず、タスクに並列化可能な待機時間が存在するかに依存する

## 依存関係

- `celestialflow`（`TaskExecutor`、`TaskProgress`、`benchmark_executor`）
