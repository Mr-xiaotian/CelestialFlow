# bench_utils.py ベンチマーク説明

## 目標

`bench/` ディレクトリ下の各ベンチマークテストに統一的な統計出力ツール `summarize()` を提供し、所要時間データの表示形式を標準化します。

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

- `statistics.pstdev`（母集団標準偏差）を使用しており、小サンプル（`REPEAT = 3`）に適しています
- スループットは平均値に基づいて計算されます。各ラウンド間の差異が大きい場合、この値は参考値にすぎません

## 発生しうる問題

1. **サンプルサイズが小さい**：多くのベンチマークは `REPEAT = 3` を使用しています。`pstdev` は外れ値に敏感であり、あるラウンドでシステムの揺らぎ（バックグラウンドプロセス、ガベージコレクションなど）により所要時間が急増した場合、標準偏差が大幅に膨張します。
2. **ゼロ値保護**：`throughput = count / mean_s if mean_s > 0 else 0.0`。極めて高速なシナリオ（`mean_s` が浮動小数点精度の下限に近い場合）では、非常に大きな値が生成される可能性があります。

## 実行方法

このファイルは直接実行できません。共有モジュールとしてインポートされます：
```python
from bench_utils import summarize
```

## 関連ファイル

- `bench/bench_ipc_queue.py`
- `bench/bench_mpqueue_vs_shared_memory.py`
