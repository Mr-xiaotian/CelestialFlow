# ランタイム型テスト (test_types.py)

> 📅 最終更新日: 2026/07/16

## 役割
`celestialflow.runtime.util_types` の値オブジェクト、列挙型、ラッパー（終了信号、No-Op コンテキスト、オプションのロック付き値ラッパー、合計カウンタ、タスクイベント定数）を検証します。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestUtilTypes` | 28 | `TerminationSignal` デフォルト/カスタム/部分パラメータ構築；`TerminationIdPool` 非空/空/単一要素構築；`NoOpContext` with 文/例外透過/直接呼び出し enter/exit；`ValueWrapper` 基本読み書き/ロック付き読み書き/コンテキストマネージャ/`get_lock` がロックまたは NoOpContext を返す/負の数値境界；`SumCounter` 累積/初期値/reset ゼロクリア/空カウンタ/複数回 add；`StageStatus` 列挙値/IntEnum 動作/メンバー数；`CTreeEvent` タスク定数/終了定数/プレフィックス形式 |

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
