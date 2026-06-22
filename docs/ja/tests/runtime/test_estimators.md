# 残り時間推定テスト (test_estimators.py)

> 📅 最終更新日: 2026/06/22

## 役割
`calc_remaining`、`calc_elapsed`、`calc_global_pending` の3つの推定関数を検証し、CelestialFlow がノードレベルとグラフレベルの両方で安定した残り時間予測を提供できることを確認します。

## カバレッジポイント
- `calc_remaining`: `processed / pending / elapsed` に基づく基本推定。
- `calc_elapsed`: `StageStatus` と前回スナップショットに基づいて経過時間を累積し続けるかどうかを決定。
- `calc_global_pending`: DAG 上で負荷を上流から下流に伝播させ、線形チェーン、ファンイン、ファンアウト、ダイヤモンド、空グラフなどのトポロジをカバー。

## 主要シナリオ
- ゼロ値境界：`processed=0`、`pending=0`、空グラフ。
- 状態遷移：`NOT_STARTED`、`RUNNING`、`STOPPED` の累積戦略。
- グラフ構造伝播：線形チェーン、ファンアウト、ファンイン、ダイヤモンド、ボトルネックノード、map データ欠落。
- 性質検証：対称性、単調性、「負の値が出現してはならない」こと。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|-------------|---------|--------------|
| `TestCalcRemaining` | 7 | 基本比率計算とゼロ値境界 |
| `TestCalcElapsed` | 7 | 状態マシンに基づく時間累積戦略 |
| `TestCalcGlobalPending` | 16 | DAG 伝播推定：線形チェーン、ファンアウト、ファンイン、ダイヤモンド、ボトルネック、空グラフ、map データ欠落など |
| `TestPropertyBased` | 3 | 対称性、単調性などの性質検証 |

## 実行方法

```bash
pytest tests/runtime/test_estimators.py -v
pytest tests/runtime/test_estimators.py -k "calc_remaining or calc_elapsed" -v
pytest tests/runtime/test_estimators.py -k "global_pending" -v
```
