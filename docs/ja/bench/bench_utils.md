# bench_utils.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

`bench/` ディレクトリ配下の各ベンチマークに統一的な統計出力ツール `summarize()` を提供し、所要時間データの表示形式を標準化する。

## 機能

```python
def summarize(name: str, durations: list[float], count: int) -> None
```

出力内容：
- 各ラウンドの所要時間（生の値）
- 平均所要時間（mean）
- 標準偏差（pstdev）
- スループット（`count / mean_s`、items/s）

## 主要な実装

- `statistics.pstdev`（母集団標準偏差）を使用。小さなサンプル（`REPEAT = 3`）に適用
- スループットは平均値に基づいて計算。各ラウンドの差異が大きい場合、この値は参考値のみ

## 発生し得る問題

1. **サンプルサイズの小ささ**：ほとんどのベンチマークは `REPEAT = 3` を使用。`pstdev` は外れ値に敏感で、あるラウンドがシステムジッター（バックグラウンドプロセス、ガベージコレクションなど）により所要時間が急増した場合、標準偏差が著しく膨らむ。
2. **ゼロ値保護**：`throughput = count / mean_s if mean_s > 0 else 0.0`。極めて高速なシナリオ（`mean_s` が浮動小数点精度の限界に近い場合）では非常に大きな値が生成される可能性がある。

## 実行方法

このファイルは直接実行できない。共有モジュールとしてインポートされる：
```python
from bench_utils import summarize
```

## 関連ファイル

- `bench/bench_ipc_queue.py`
- `bench/bench_mpqueue_vs_shared_memory.py`
