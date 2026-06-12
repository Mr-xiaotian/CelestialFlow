# Inlet 基本テスト (test_inlet.py)

> 📅 最終更新日: 2026/06/05

## 役割
`celestialflow.funnel.core_inlet.BaseInlet` の最小責務（呼び出し元から渡されたデータを `_funnel()` 経由でターゲットキューに入れ、実行中の `BaseSpout` サブクラスによって消費されること）を検証します。

## カバレッジポイント
- `MockInlet.send()` が `_funnel()` を通じてレコードを転送。
- `MockSpout` がキューから文字列と辞書の2種類のメッセージを消費。
- コンシューマが未起動の場合でも、レコードはまずキューに入り、後続の読み取りに備える。

## 主要シナリオ
- `test_inlet_to_spout_communication`: `MockSpout` を起動後に2つのメッセージを送信し、コンシューマが最終的に順序通り受信することを検証。
- `test_funnel_puts_record_into_queue`: spout を起動せず、キューから元のレコードを直接取得できることをアサートし、`_funnel()` がデータを改変しないことを確認。

## 実行方法

```bash
pytest tests/funnel/test_inlet.py -v
pytest tests/funnel/test_inlet.py -k "communication" -v
```
