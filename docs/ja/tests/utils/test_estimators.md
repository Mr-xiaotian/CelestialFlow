# 所要時間推定ユーティリティテスト (test_estimators.py)

> 📅 最終更新日: 2026/05/28

## 目的

`celestialflow.utils.util_estimators` 内のグローバルタスク残り時間推定関数 `calc_remaining`、`calc_elapsed`、`calc_global_remain_equal_pred` を検証します。

## コアテスト対象

- `calc_remaining`: `(pending, processed, elapsed)` に基づいて単一 Stage の推定残り時間を計算します。
- `calc_elapsed`: `time_start`、`time_end`、`status` に基づいて実際の経過時間を計算します。
- `calc_global_remain_equal_pred`: グラフ全体の全ノードを走査し、上流の処理済み量と下流の保留量に基づいて、**等比分布**で各ノードの残り時間を推定します。

## 主要テストシナリオ

### `TestCalcRemaining`
- 通常の推定：`(pending=5, processed=5, elapsed=10)` → 残り 10s
- 境界値：pending=0、processed=0、3 つすべて 0 → すべて 0 を返す
- 浮動小数点入力のサポート

### `TestCalcElapsed`
- RUNNING 状態で pending あり → `現在時刻 - time_start` を返す
- RUNNING 状態で pending なし → `time_end - time_start` を返す
- STOPPED 状態 → `time_end - time_start` を返す
- NOT_STARTED → 0 を返す
- 連続呼び出しで時間の進行をシミュレート

### `TestCalcGlobalRemainEqualPred`
- 先行ノードなしの単一ノード / 全ゼロ pending
- 線形チェーン（3 ノード A→B→C）：`total_processed` が適切に配分される
- ファンアウト（1 対多）、ファンイン（多対 1）、ダイヤモンド構造（A→[B,C]→D）
- ボトルネックノード（大きな pending 値）
- 結果の型は `dict[str, float]`、負の値なし
- 上流にデータがないが下流に pending がある（diff 値を使用）
- 空グラフの処理

### `TestPropertyBased` — プロパティベーステスト
- 対称線形チェーンは同じ推定値を生成
- 単調性：pending 大 → 推定値大
- 単調性：processed 大 → 推定値小

## 実行方法

```bash
# 全実行
pytest tests/utils/test_estimators.py -v

# calc_remaining テストのみ
pytest tests/utils/test_estimators.py -k "Remaining" -v

# calc_elapsed テストのみ
pytest tests/utils/test_estimators.py -k "Elapsed" -v

# グローバル推定テストのみ
pytest tests/utils/test_estimators.py -k "Global" -v

# プロパティベーステストのみ
pytest tests/utils/test_estimators.py -k "Property" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------------|----------|
| `TestCalcRemaining` | ~0.01s |
| `TestCalcElapsed` | ~0.02s |
| `TestCalcGlobalRemainEqualPred` | ~0.1s |
| `TestPropertyBased` | ~0.1s |

## 重要な詳細

- グローバル推定は**等比分布仮定**を使用：下流ノードの残り時間は上流各ノードの処理済み量の比率に応じて配分されます。
- ヘルパー関数 `_make_linear_chain(n)` は n ノードの線形 DAG を構築し、テストトポロジの迅速な構築を容易にします。
- プロパティベーステストは推定関数の数学的単調性を検証し、具体的な数値に依存しません。

## 注意事項

- これらの推定関数はダッシュボードでの進捗推定と ETA 表示に使用され、推定精度はユーザーエクスペリエンスに影響します。
- 関連実装は `src/celestialflow/utils/util_estimators.py` にあります。
