# funnel テストパッケージ

> 📅 最終更新日: 2026/06/05

## 役割
`tests/funnel/` は基本ファンネルコンポーネントのスレッドライフサイクルとキュー転送セマンティクスをカバーし、主に `BaseInlet` と `BaseSpout` の最小動作制約を検証します。

## 含まれるテストファイル
- `test_inlet.py`: inlet が `_funnel()` を通じてレコードをターゲットキューに書き込むことを検証。
- `test_spout.py`: spout の起動/停止フック、終了信号処理、抽象メソッド制約を検証。

## 実行方法

```bash
pytest tests/funnel -v
pytest tests/funnel -k "inlet or spout" -v
```
