# Spout 基本テスト (test_spout.py)

> 📅 最終更新日: 2026/08/19

## 役割
`celestialflow.funnel.core_spout.BaseSpout` のライフサイクルフック、終了信号処理、抽象メソッド制約を検証し、リスニングスレッドが期待通りに起動・停止し、停止前のレコードを消費できることを確認します。

## カバレッジポイント
- `start()` が `_before_start()` を呼び出す。
- `stop()` が `_after_stop()` をトリガーし、停止後は新しいレコードを消費し続けない。
- 基底クラスで `_handle_record()` が未実装の場合、`CelestialFlowError` がスローされる。

## テストカバレッジマトリックス

| テストクラス | ケース | カバレッジ対象 |
|------------|------|--------------|
| `TestBaseSpout` | `test_base_spout_lifecycle` | 起動/停止フックが正しくトリガーされ、停止前のデータが依然として消費されること |
| `TestBaseSpout` | `test_spout_termination_signal` | 重複した `stop()` 呼び出しが安全であり、終了後に後続のエンキューデータが処理されないこと |
| `TestBaseSpout` | `test_spout_can_restart_after_stop` | `stop()` 後に再度 `start()` すると新しいバックグラウンドスレッドが作成され引き続き消費できること |
| `TestBaseSpout` | `test_spout_not_implemented_error` | 抽象メソッド `_handle_record` が未オーバーライドの場合に `CelestialFlowError` がスローされること |

## 実行方法

```bash
pytest tests/funnel/test_spout.py -v
pytest tests/funnel/test_spout.py -k "lifecycle or termination" -v
```
