# ランタイム型テスト (test_types.py)

> 📅 最終更新日: 2026/06/22

## 役割
`celestialflow.runtime.util_types` の値オブジェクト、列挙型、ラッパー（終了信号、No-Op コンテキスト、オプションのロック付き値ラッパー、合計カウンタ、タスクイベント定数）を検証します。

## カバレッジポイント
- `TerminationSignal` / `TerminationIdPool` の構築セマンティクス。
- `NoOpContext` のコンテキスト管理動作と例外の透過伝播。
- `ValueWrapper` のロックあり/なし両モードでの読み書きセマンティクス。
- `SumCounter` の累積、リセット表現。
- `StageStatus`、`CTreeEvent` の列挙値。

## 主要シナリオ
- `ValueWrapper.get_lock()` が異なる構築方法で実際のロックまたは `NoOpContext` を返す。
- `SumCounter.reset()` が初期値とサブカウンタを同時にゼロクリアする。

## 実行方法

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or sum_counter" -v
pytest tests/runtime/test_types.py -k "termination" -v
```
