# Observer テスト (test_observer.py)

> 📅 最終更新日: 2026/06/05

## 目的

CelestialFlow の監視 helper で使う observer 方式の進捗・コールバック挙動を検証します。

## 主要ポイント

- 開始・成功・失敗まわりのイベントコールバックを確認します。
- ユーザー向け進捗表示の一貫性を保ちます。

## 実行方法

```bash
pytest tests/observability/test_observer.py -v
pytest tests/observability/test_observer.py -k "progress or callback" -v
```
