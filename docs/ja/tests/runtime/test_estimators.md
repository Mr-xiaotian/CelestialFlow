# 推定器テスト (test_estimators.py)

> 📅 最終更新日: 2026/06/05

## 目的

ノード単位・グラフ単位の経過時間 / 残時間推定 helper を検証します。

## 主要ポイント

- ゼロ値境界、状態遷移、複数 DAG 形状を扱います。
- 全体残時間推定の単調性のような性質も確認します。

## 実行方法

```bash
pytest tests/runtime/test_estimators.py -v
pytest tests/runtime/test_estimators.py -k "calc_remaining or calc_elapsed" -v
pytest tests/runtime/test_estimators.py -k "global_remain" -v
```
