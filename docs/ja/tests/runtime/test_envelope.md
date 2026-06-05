# TaskEnvelope テスト (test_envelope.py)

> 📅 最終更新日: 2026/06/05

## 目的

タスクデータ参照、遅延ハッシュ、ID 変更、pickle 不可タスク向けフォールバックハッシュを検証します。

## 主要ポイント

- 同一タスクの安定ハッシュと異なるタスクの分離を確認します。
- ハッシュ失敗時に使う一意なフォールバック bytes を扱います。

## 実行方法

```bash
pytest tests/runtime/test_envelope.py -v
pytest tests/runtime/test_envelope.py -k "hash or unhashable" -v
```
