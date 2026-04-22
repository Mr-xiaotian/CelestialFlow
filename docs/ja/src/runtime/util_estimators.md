# RuntimeEstimators

`runtime/util_estimators.py` はランタイムの所要時間推定関数を提供します。

## 主要関数

- `calc_remaining(processed, pending, elapsed)`: ノードの残り時間を推定します。
- `calc_elapsed(status, last_elapsed, last_pending, interval)`: ステータスに基づいて経過時間を累積します。
- `calc_global_remain_equal_pred(...)`: DAG と観測メトリクスに基づいてグローバル残り時間を推定します。

## 用途

- 監視ダッシュボードの ETA 表示を駆動します。
- 潜在的な輻輳ノードの特定を支援します。
