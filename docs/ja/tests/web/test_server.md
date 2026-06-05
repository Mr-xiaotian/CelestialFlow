# Web サーバーテスト (test_server.py)

> 📅 最終更新日: 2026/06/05

## 目的

組み込み監視サーバーの起動フローとサーバー統合挙動を検証します。

## 主要ポイント

- task graph と HTTP サービスの結線を扱います。
- リファクタ後も組み込み監視サーバーの信頼性を保ちます。

## 実行方法

```bash
pytest tests/web/test_server.py -v
pytest tests/web/test_server.py -k "server" -v
```
