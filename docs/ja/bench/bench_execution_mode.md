# bench_execution_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/05/08

## 目的

`TaskExecutor` の 3 つの実行モード（`serial`、`thread`、`async`）における CPU 集約型タスク（フィボナッチ）と I/O 集約型タスク（sleep）の性能差を比較する。フレームワーク内蔵の `benchmark_executor` ツールで統一的な比較レポートを出力する。

## テスト内容

### `bench_executor_fibonacci`
- **タスク**：フィボナッチ数列の再帰計算（`n=25..31`）、エッジケース含む（`0, None, ""`）
- **設定**：`max_workers=6`、`max_retries=1`、`ValueError` でリトライ
- **比較モード**：`serial`、`thread`、`async`

### `bench_executor_sleep`
- **タスク**：純粋な 1 秒スリープ（I/O 待機のシミュレーション）
- **設定**：`max_workers=12`、`max_retries=0`
- **比較モード**：`serial`、`thread`、`async`

## 主要パラメータ

| パラメータ | 値 | 説明 |
|------------|-----|------|
| `max_workers` | 6 (CPU) / 12 (I/O) | 並行ワーカー数 |
| `max_retries` | 1 (CPU) / 0 (I/O) | リトライ回数 |

## 発生し得る問題

1. **再帰深度制限**：`fibonacci` は再帰実装を使用。`n=31` の入力で約 200 万回の再帰呼び出しが発生し、数秒かかる。より大きな値を誤って渡すと `RecursionError` が発生する可能性がある。
2. **`asyncio` イベントループの競合**：`main()` は `asyncio.run()` を使用するため、Jupyter や既存のイベントループがある環境ではエラーになる。
3. **`benchmark_executor` の出力形式**：このツールは `TaskExecutor` の `execution_mode` を複数回変更して再実行するため、合計時間 = モード数 × タスク数 × 単一タスク時間となり、完了まで数分かかる場合がある。

## 実行方法

```bash
python bench/bench_execution_mode.py
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10

### シナリオ 1：フィボナッチ（CPU 集約型）
12 タスク（エッジケース 5 個含む）、max_workers=6、max_retries=1

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 0.896s | シングルスレッド逐次実行 |
| thread | 0.862s | 6 スレッド並行、GIL 制約により改善は限定的 |
| async | 0.009s | コルーチン並行、GIL オーバーヘッドがないため純 CPU シナリオで最良 |

### シナリオ 2：sleep_1（I/O 集約型）
12 タスク、各 1 秒スリープ、max_workers=12

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 12.131s | 逐次スリープ、合計時間 ≈ 12 × 1s |
| thread | 1.028s | 12 スレッド並列、合計時間 ≈ 1s + スケジューリングオーバーヘッド |
| async | 1.024s | コルーチン並列、thread とほぼ同等 |

**主要な結論**：
- CPU 集約型タスク：async は GIL 競合がないため serial/thread の約 100 倍高速（ただし本例では fibonacci は純粋な同期再帰であり、async の優位性は主にイベントループスケジューリングに由来）
- I/O 集約型タスク：thread/async は serial の約 12 倍高速で、理論上限に近い
- thread モードは CPU 集約型シナリオでは GIL の制約により改善が微小

## 依存関係

- `celestialflow`（`TaskExecutor`、`TaskProgress`、`benchmark_executor`）
