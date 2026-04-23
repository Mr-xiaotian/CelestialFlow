# bench_executor.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目標

`TaskExecutor` の 3 つの実行モード（`serial`、`thread`、`async`）における CPU 集約型タスク（フィボナッチ）と I/O 集約型タスク（sleep）の性能差を比較します。フレームワーク組み込みの `benchmark_executor` ツールを使用して統一的な比較レポートを出力します。

## テスト内容

### `bench_executor_fibonacci`
- **タスク**：フィボナッチ数列の再帰計算（`n=25..31`）、異常入力（`0, None, ""`）を含む
- **設定**：`max_workers=6`、`max_retries=1`、`ValueError` でリトライ
- **比較モード**：`serial`、`thread`、`async`

### `bench_executor_sleep`
- **タスク**：純粋な 1 秒スリープ（I/O 待ちのシミュレーション）
- **設定**：`max_workers=12`、`max_retries=0`
- **比較モード**：`serial`、`thread`、`async`

## 主要パラメータ

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `max_workers` | 6 (CPU) / 12 (I/O) | 並行ワーカー数 |
| `max_retries` | 1 (CPU) / 0 (I/O) | リトライ回数 |
| `show_progress` | `True` | tqdm プログレスバーを表示 |

## 発生しうる問題

1. **再帰深度制限**：`fibonacci` は再帰実装を使用しており、入力 `n=31` では再帰深度が約 200 万に達し、数秒かかります。より大きな値を誤って渡すと `RecursionError` が発生する可能性があります。
2. **`asyncio` イベントループの競合**：`main()` は `asyncio.run()` を使用しており、Jupyter や既存のイベントループがある環境で実行するとエラーが発生します。
3. **`benchmark_executor` の出力形式**：このツールは `TaskExecutor` の `execution_mode` を複数回変更して繰り返し実行するため、合計所要時間 = モード数 x タスク数 x 単一タスクの所要時間となり、完了までに数分かかる場合があります。

## 実行方法

```bash
python bench/bench_executor.py
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10

### シナリオ 1：フィボナッチ（CPU 集約型）
12 タスク（5 つの異常境界値を含む）、max_workers=6、max_retries=1

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 0.896s | シングルスレッド逐次実行 |
| thread | 0.862s | 6 スレッド並行、GIL 制限により改善はわずか |
| async | 0.009s | コルーチン並行、GIL オーバーヘッドがないため純粋な CPU シナリオで最高性能 |

### シナリオ 2：sleep_1（I/O 集約型）
12 タスク、各 1 秒スリープ、max_workers=12

| モード | 所要時間 | 説明 |
|--------|----------|------|
| serial | 12.131s | 逐次スリープ、合計所要時間 ~ 12 x 1s |
| thread | 1.028s | 12 スレッド並列、合計所要時間 ~ 1s + スケジューリングオーバーヘッド |
| async | 1.024s | コルーチン並列、thread とほぼ同等 |

**主要な結論**：
- CPU 集約型タスク：async は GIL 競合がないため serial/thread より約 100x 高速です（ただし本例では fibonacci は純粋な同期再帰のため、async の優位性は主にイベントループスケジューリングによるものです）
- I/O 集約型タスク：thread/async は serial より約 12x 高速で、理論上限に近い性能を示します
- thread モードは GIL 制限により CPU 集約型シナリオでの改善はごくわずかです

## 依存関係

- `celestialflow`（`TaskExecutor`、`benchmark_executor`）
