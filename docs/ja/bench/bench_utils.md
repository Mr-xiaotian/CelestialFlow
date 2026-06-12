# bench_utils.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目的

`bench/` ディレクトリ配下の各ベンチマークテストに統一的な統計出力ツール `summarize()` を提供し、所要時間データの表示フォーマットを標準化する。

## 機能

```python
def summarize(name: str, durations: list[float], count: int) -> None
```

出力内容：
- 各ラウンドの所要時間（生の値）
- 平均所要時間（mean）
- 標準偏差（pstdev）
- スループット（`count / mean_s`、items/s）

## 主要実装

- `statistics.pstdev`（母標準偏差）を使用、小サンプル（`REPEAT = 3`）に適する
- スループット計算は平均値に基づく。各ラウンドの差が大きい場合、この値は参考程度

## 発生し得る問題

1. **サンプルサイズが小さすぎる**：多くの benchmark の `REPEAT = 3` であり、`pstdev` は外れ値に敏感。システムのジッター（バックグラウンドプロセス、ガベージコレクション等）により特定ラウンドの所要時間が急増した場合、標準偏差が顕著に膨張する。
2. **ゼロ値保護**：`throughput = count / mean_s if mean_s > 0 else 0.0`。極めて高速なシナリオ（`mean_s` が浮動小数点精度の下限に近い）では、極端に大きな値が生成される可能性がある。

## 実行方法

このファイル自体は直接実行できず、共有モジュールとしてインポートされる：
```python
from bench_utils import summarize
```

## 関連ファイル

- `bench/bench_ipc_queue.py`
- `bench/bench_mpqueue_vs_shared_memory.py`
